from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nova_synesis.api.app import create_app
from nova_synesis.config import Settings
from nova_synesis.domain.models import MemoryType, ResourceType
from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog
from nova_synesis.services.orchestrator import create_orchestrator


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=str(tmp_path / "data" / "orchestrator.db"),
        working_directory=str(tmp_path),
        default_long_term_backend=str(tmp_path / "data" / "long_term.db"),
        default_vector_backend=str(tmp_path / "data" / "vector.db"),
    )


def test_end_to_end_flow_with_vector_memory_and_message_queue(tmp_path: Path) -> None:
    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            orchestrator.register_memory_system("vector", MemoryType.VECTOR)
            sender = orchestrator.register_agent(
                name="planner",
                role="planner",
                capabilities=[
                    {"name": "memory", "type": "knowledge"},
                    {"name": "messaging", "type": "dispatch"},
                ],
                communication={
                    "protocol": "MESSAGE_QUEUE",
                    "endpoint": "queue://planner",
                    "config": {},
                },
                memory_ids=["vector"],
            )
            target = orchestrator.register_agent(
                name="observer",
                role="observer",
                capabilities=[{"name": "observe", "type": "monitoring"}],
                communication={
                    "protocol": "MESSAGE_QUEUE",
                    "endpoint": "queue://observer",
                    "config": {},
                },
            )

            flow = orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "store_vector",
                        "handler_name": "memory_store",
                        "input": {
                            "memory_id": "vector",
                            "key": "doc-1",
                            "value": {
                                "value": {"text": "Alpha node"},
                                "embedding": [1.0, 0.0],
                                "metadata": {"topic": "alpha"},
                            },
                        },
                        "required_capabilities": ["memory"],
                        "preferred_agent_id": sender["agent_id"],
                    },
                    {
                        "node_id": "search_vector",
                        "handler_name": "memory_search",
                        "input": {
                            "memory_id": "vector",
                            "query": [1.0, 0.0],
                            "limit": 1,
                        },
                        "dependencies": ["store_vector"],
                        "conditions": {"store_vector": "results['store_vector']['stored'] == True"},
                        "preferred_agent_id": sender["agent_id"],
                    },
                    {
                        "node_id": "notify",
                        "handler_name": "send_message",
                        "input": {
                            "target_agent_name": target["name"],
                            "message": {
                                "match": "{{ results['search_vector']['matches'][0]['key'] }}",
                            },
                        },
                        "dependencies": ["search_vector"],
                        "conditions": {"search_vector": "len(results['search_vector']['matches']) > 0"},
                        "required_capabilities": ["messaging"],
                        "preferred_agent_id": sender["agent_id"],
                    },
                ]
            )

            snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
            assert snapshot["state"] == "COMPLETED"
            assert snapshot["results"]["search_vector"]["matches"][0]["key"] == "doc-1"

            received = await orchestrator.agents[target["agent_id"]].comms.receive()
            assert received["message"]["match"] == "doc-1"
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_fallback_resource_strategy_switches_to_secondary_resource(tmp_path: Path) -> None:
    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            resource_primary = orchestrator.register_resource(
                resource_type=ResourceType.MODEL,
                endpoint="model://primary",
                metadata={"capacity": 1},
            )
            resource_secondary = orchestrator.register_resource(
                resource_type=ResourceType.MODEL,
                endpoint="model://secondary",
                metadata={"capacity": 1},
            )
            agent = orchestrator.register_agent(
                name="model-runner",
                role="worker",
                capabilities=[{"name": "inference", "type": "model"}],
            )

            async def unstable_model_handler(context: dict) -> dict:
                endpoint = context["resources"][0].endpoint
                if endpoint == "model://primary":
                    raise RuntimeError("Primary model unavailable")
                return {"resource_endpoint": endpoint}

            orchestrator.register_handler("unstable_model", unstable_model_handler)
            orchestrator.issue_handler_certificate("unstable_model")

            flow = orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "run_model",
                        "handler_name": "unstable_model",
                        "input": {"prompt": "hello"},
                        "required_resource_ids": [resource_primary["resource_id"]],
                        "rollback_strategy": "FALLBACK_RESOURCE",
                        "retry_policy": {"max_retries": 1, "backoff_ms": 1, "exponential": False},
                        "preferred_agent_id": agent["agent_id"],
                    }
                ]
            )

            snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
            assert snapshot["state"] == "COMPLETED"
            assert snapshot["results"]["run_model"]["resource_endpoint"] == resource_secondary["endpoint"]
            executions = orchestrator.list_executions()
            assert executions[-1]["attempt_count"] == 2
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_fastapi_flow_execution_endpoint(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    app = create_app(orchestrator=orchestrator)

    with TestClient(app) as client:
        memory_response = client.post(
            "/memory-systems",
            json={"memory_id": "short-term", "type": "SHORT_TERM"},
        )
        assert memory_response.status_code == 200

        agent_response = client.post(
            "/agents",
            json={
                "name": "api-agent",
                "role": "worker",
                "capabilities": [{"name": "templating", "type": "rendering"}],
            },
        )
        assert agent_response.status_code == 200

        flow_response = client.post(
            "/flows",
            json={
                "nodes": [
                    {
                        "node_id": "render",
                        "handler_name": "template_render",
                        "input": {
                            "template": "Order {id}",
                            "values": {"id": 42},
                        },
                        "preferred_agent_id": agent_response.json()["agent_id"],
                    }
                ]
            },
        )
        assert flow_response.status_code == 200
        flow_id = flow_response.json()["flow_id"]

        run_response = client.post(f"/flows/{flow_id}/run")
        assert run_response.status_code == 200
        body = run_response.json()
        assert body["state"] == "COMPLETED"
        assert body["results"]["render"]["rendered"] == "Order 42"

        executions_response = client.get("/executions")
        assert executions_response.status_code == 200
        assert len(executions_response.json()) == 1


def test_handlers_endpoint_exposes_trust_metadata(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    app = create_app(orchestrator=orchestrator)

    with TestClient(app) as client:
        response = client.get("/handlers")
        assert response.status_code == 200
        body = response.json()
        assert "details" in body
        template_handler = next(
            item for item in body["details"] if item["name"] == "template_render"
        )
        assert template_handler["trusted"] is True
        assert template_handler["certificate"]["issuer"]


def test_manual_approval_endpoint_enables_execution(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))

    async def reviewed_handler(_: dict) -> dict:
        return {"ok": True}

    orchestrator.register_handler("reviewed_handler", reviewed_handler)
    orchestrator.issue_handler_certificate("reviewed_handler")

    app = create_app(orchestrator=orchestrator)

    with TestClient(app) as client:
        flow_response = client.post(
            "/flows",
            json={
                "nodes": [
                    {
                        "node_id": "review",
                        "handler_name": "reviewed_handler",
                        "input": {},
                        "requires_manual_approval": True,
                    }
                ]
            },
        )
        assert flow_response.status_code == 200
        flow_id = flow_response.json()["flow_id"]

        blocked_run = client.post(f"/flows/{flow_id}/run")
        assert blocked_run.status_code == 400
        assert "manual approval" in blocked_run.json()["detail"].lower()

        approve_response = client.post(
            f"/flows/{flow_id}/nodes/review/approval",
            json={"approved_by": "qa-operator", "reason": "Release checklist completed"},
        )
        assert approve_response.status_code == 200
        approval = approve_response.json()["nodes"]["review"]["manual_approval"]
        assert approval["approved"] is True
        assert approval["approved_by"] == "qa-operator"

        approved_run = client.post(f"/flows/{flow_id}/run")
        assert approved_run.status_code == 200
        assert approved_run.json()["state"] == "COMPLETED"


def test_websocket_flow_updates_stream_runtime_events(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    app = create_app(orchestrator=orchestrator)

    with TestClient(app) as client:
        flow_response = client.post(
            "/flows",
            json={
                "nodes": [
                    {
                        "node_id": "render",
                        "handler_name": "template_render",
                        "input": {
                            "template": "Hello {name}",
                            "values": {"name": "Live"},
                        },
                    }
                ]
            },
        )
        assert flow_response.status_code == 200
        flow_id = flow_response.json()["flow_id"]

        def run_background_flow() -> None:
            response = client.post(f"/flows/{flow_id}/run?background=true")
            assert response.status_code == 200

        with client.websocket_connect(f"/ws/flows/{flow_id}") as websocket:
            initial_event = websocket.receive_json()
            assert initial_event["type"] == "flow.snapshot"
            assert initial_event["snapshot"]["state"] == "CREATED"

            runner = threading.Thread(target=run_background_flow)
            runner.start()

            started_event = websocket.receive_json()
            running_event = websocket.receive_json()
            runner.join()

            assert started_event["type"] == "flow.started"
            assert started_event["snapshot"]["state"] == "RUNNING"
            assert running_event["type"] in {"node.started", "flow.progress", "flow.completed"}


def test_lit_planner_normalizes_graph_output(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed = planner._parse_model_output(
        """
        ```json
        {
          "nodes": [
            {
              "node_id": "fetch data",
              "title": "Fetch Items",
              "handler_name": "http_request",
              "input": {"url": "https://example.org/items", "method": "GET"},
              "required_resource_types": ["API"],
              "preferred_agent_name": "HTTP Worker"
            },
            {
              "node_id": "store",
              "handler_name": "memory_store",
              "input": {"memory_id": "long-term", "key": "items", "value": {"$ref": "results['fetch-data']['body']"}},
              "dependencies": ["fetch-data"],
              "conditions": {"fetch-data": "results['fetch-data']['status_code'] == 200"}
            }
          ],
          "edges": [
            {"from_node": "fetch-data", "to_node": "store", "condition": "results['fetch-data']['status_code'] == 200"},
            {"from_node": "start", "to_node": "fetch-data", "condition": "True"}
          ],
          "explanation": "Fetch remote data and persist it."
        }
        ```
        """
    )

    normalized, warnings = planner._normalize_flow_request(
        parsed=parsed,
        catalog=PlannerCatalog(
            handlers=["http_request", "memory_store", "template_render"],
            agents=[
                {
                    "agent_id": 7,
                    "name": "HTTP Worker",
                    "role": "worker",
                    "capabilities": [{"name": "http", "type": "network"}],
                }
            ],
            resources=[
                {
                    "resource_id": 3,
                    "type": "API",
                    "endpoint": "https://example.org",
                    "metadata": {},
                    "state": "AVAILABLE",
                }
            ],
            memory_systems=[{"memory_id": "long-term", "type": "LONG_TERM"}],
        ),
        max_nodes=12,
    )

    assert normalized["nodes"][0]["node_id"] == "fetch-data"
    assert normalized["nodes"][0]["preferred_agent_id"] == 7
    assert normalized["nodes"][0]["metadata"]["ui"]["title"] == "Fetch Items"
    assert normalized["nodes"][1]["dependencies"] == ["fetch-data"]
    assert normalized["edges"] == [
        {
            "from_node": "fetch-data",
            "to_node": "store",
            "condition": "results['fetch-data']['status_code'] == 200",
        }
    ]
    assert warnings


def test_semantic_firewall_rejects_cyclic_flow(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        with pytest.raises(ValueError, match="cycle"):
            orchestrator.create_flow(
                nodes=[
                    {"node_id": "a", "handler_name": "template_render", "input": {"template": "A", "values": {}}},
                    {"node_id": "b", "handler_name": "template_render", "input": {"template": "B", "values": {}}},
                ],
                edges=[
                    {"from_node": "a", "to_node": "b", "condition": "True"},
                    {"from_node": "b", "to_node": "a", "condition": "True"},
                ],
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_rejects_external_http_request(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        with pytest.raises(ValueError, match="Outbound host"):
            orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "fetch",
                        "handler_name": "http_request",
                        "input": {"url": "https://example.org/collect", "method": "GET"},
                    }
                ]
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_blocks_send_message_endpoint_override(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        target = orchestrator.register_agent(
            name="internal-target",
            role="worker",
            communication={
                "protocol": "MESSAGE_QUEUE",
                "endpoint": "queue://internal-target",
                "config": {},
            },
        )
        with pytest.raises(ValueError, match="override"):
            orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "notify",
                        "handler_name": "send_message",
                        "input": {
                            "target_agent_id": target["agent_id"],
                            "message": {
                                "target_endpoint": "queue://evil",
                                "text": "payload",
                            },
                        },
                    }
                ]
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_rejects_unknown_send_message_target_agent_name(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        with pytest.raises(ValueError, match="unknown agent 'missing-sink'"):
            orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "notify",
                        "handler_name": "send_message",
                        "input": {
                            "target_agent_name": "missing-sink",
                            "message": {"text": "payload"},
                        },
                    }
                ]
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_blocks_external_rest_agent_registration(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        with pytest.raises(ValueError, match="outside the allowlist"):
            orchestrator.register_agent(
                name="webhook-agent",
                role="worker",
                communication={
                    "protocol": "REST",
                    "endpoint": "https://evil.example/hook",
                    "config": {},
                },
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_blocks_sensitive_memory_exfiltration(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    settings.security_http_allowed_hosts = ("example.org",)
    settings.security_allow_loopback_hosts = True
    orchestrator = create_orchestrator(settings)
    try:
        orchestrator.register_memory_system(
            "secret-memory",
            MemoryType.LONG_TERM,
            config={"sensitive": True},
        )
        with pytest.raises(ValueError, match="Sensitive memory data"):
            orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "load_secret",
                        "handler_name": "memory_retrieve",
                        "input": {"memory_id": "secret-memory", "key": "billing-iban"},
                    },
                    {
                        "node_id": "exfiltrate",
                        "handler_name": "http_request",
                        "input": {
                            "url": "https://example.org/collect",
                            "method": "POST",
                            "json": {"payload": "{{ results['load_secret']['value'] }}"},
                        },
                        "dependencies": ["load_secret"],
                    },
                ]
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_semantic_firewall_blocks_template_context_escape(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    try:
        with pytest.raises(ValueError, match="disallowed symbol 'task'"):
            orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "escape",
                        "handler_name": "write_file",
                        "input": {
                            "path": "debug.txt",
                            "content": "{{ task }}",
                        },
                    }
                ]
            )
    finally:
        asyncio.run(orchestrator.shutdown())


def test_untrusted_handler_requires_manual_approval_override(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))

    async def custom_handler(_: dict) -> dict:
        return {"ok": True}

    try:
        orchestrator.register_handler("custom_handler", custom_handler)
        flow = orchestrator.create_flow(
            nodes=[
                {
                    "node_id": "custom-step",
                    "handler_name": "custom_handler",
                    "input": {},
                }
            ]
        )

        with pytest.raises(ValueError, match="untrusted handler"):
            asyncio.run(orchestrator.run_flow(int(flow["flow_id"])))

        orchestrator.approve_flow_node(
            flow_id=int(flow["flow_id"]),
            node_id="custom-step",
            approved_by="security-review",
            reason="Temporary override for audited custom handler",
        )
        snapshot = asyncio.run(orchestrator.run_flow(int(flow["flow_id"])))
        assert snapshot["state"] == "COMPLETED"
    finally:
        asyncio.run(orchestrator.shutdown())


def test_planner_status_endpoint_exposes_lit_configuration(tmp_path: Path) -> None:
    orchestrator = create_orchestrator(build_settings(tmp_path))
    app = create_app(orchestrator=orchestrator)

    with TestClient(app) as client:
        response = client.get("/planner/status")
        assert response.status_code == 200
        body = response.json()
        assert body["backend"] == "cpu"
        assert "binary_path" in body
        assert "model_path" in body
