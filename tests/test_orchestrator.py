from __future__ import annotations

import asyncio
import argparse
import json
import subprocess
import sqlite3
import threading
import zipfile
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from nova_synesis.api.app import create_app
from nova_synesis.cli import _build_settings as build_cli_settings
from nova_synesis.cli import _resolve_lit_cli_path
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


def test_resolve_lit_cli_path_prefers_lit_directory_for_plain_filename(tmp_path: Path) -> None:
    lit_dir = tmp_path / "LIT"
    lit_dir.mkdir(parents=True, exist_ok=True)
    model_path = lit_dir / "model_multimodal.litertlm"
    model_path.write_text("dummy", encoding="utf-8")

    resolved = _resolve_lit_cli_path("model_multimodal.litertlm", workdir=str(tmp_path))

    assert Path(resolved).resolve() == model_path.resolve()


def test_build_cli_settings_applies_lit_model_override(tmp_path: Path) -> None:
    lit_dir = tmp_path / "LIT"
    lit_dir.mkdir(parents=True, exist_ok=True)
    model_path = lit_dir / "model_multimodal.litertlm"
    model_path.write_text("dummy", encoding="utf-8")

    args = argparse.Namespace(
        db_path=None,
        workdir=str(tmp_path),
        lit_model="model_multimodal.litertlm",
        lit_binary=None,
        lit_backend="cpu",
    )

    settings = build_cli_settings(args)

    assert Path(settings.lit_model_path).resolve() == model_path.resolve()


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


def test_generate_flow_with_llm_bootstraps_agent_and_memory_catalog(tmp_path: Path) -> None:
    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            observed_catalogs: list[PlannerCatalog] = []

            def fake_generate(
                prompt: str,
                catalog: PlannerCatalog,
                current_flow: dict[str, Any] | None = None,
                max_nodes: int = 12,
            ):
                observed_catalogs.append(catalog)
                return type(
                    "PlannerResult",
                    (),
                    {
                        "flow_request": {
                            "nodes": [
                                {
                                    "node_id": "notify",
                                    "handler_name": "send_message",
                                    "input": {
                                        "target_agent_name": "nova-system-agent",
                                        "message": {"text": "done"},
                                    },
                                    "required_capabilities": [],
                                    "required_resource_ids": [],
                                    "required_resource_types": [],
                                    "retry_policy": {
                                        "max_retries": 1,
                                        "backoff_ms": 1,
                                        "exponential": False,
                                        "max_backoff_ms": 1,
                                        "jitter_ratio": 0.0,
                                    },
                                    "rollback_strategy": "FAIL_FAST",
                                    "validator_rules": {},
                                    "metadata": {},
                                    "requires_manual_approval": False,
                                    "manual_approval": {},
                                    "compensation_handler": None,
                                    "dependencies": [],
                                    "conditions": {},
                                    "preferred_agent_id": None,
                                }
                            ],
                            "edges": [],
                            "metadata": {},
                        },
                        "explanation": "ok",
                        "warnings": [],
                        "raw_response": "{}",
                        "model_path": "model",
                        "backend": "cpu",
                    },
                )()

            orchestrator.lit_planner.generate_flow_request = fake_generate  # type: ignore[method-assign]
            result = await orchestrator.generate_flow_with_llm("Create any free-form workflow", max_nodes=4)
            assert observed_catalogs
            agent_names = {agent["name"] for agent in observed_catalogs[0].agents}
            memory_ids = {memory["memory_id"] for memory in observed_catalogs[0].memory_systems}
            assert "nova-system-agent" in agent_names
            assert "planner-scratch" in memory_ids
            assert "planner-vector" in memory_ids
            assert any(
                "Planner bootstrap registered agent 'nova-system-agent'" in warning
                for warning in result["warnings"]
            )
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


def test_preapproved_manual_approval_in_flow_request_runs_after_save(tmp_path: Path) -> None:
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
                        "manual_approval": {
                            "approved": True,
                            "approved_by": "inspector-checkbox",
                            "approved_at": "2026-04-11T07:41:17.228000+00:00",
                            "reason": "Checked in inspector",
                        },
                    }
                ]
            },
        )
        assert flow_response.status_code == 200
        snapshot = flow_response.json()
        flow_id = snapshot["flow_id"]
        assert snapshot["nodes"]["review"]["manual_approval"]["approved"] is True
        assert snapshot["nodes"]["review"]["manual_approval"]["approved_by"] == "inspector-checkbox"

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


def test_lit_planner_repairs_common_malformed_json_patterns(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed, warnings = planner._parse_model_output_with_warnings(
        """
        Here is the plan:
        {
          nodes: [
            {
              'node_id': 'fetch',
              'handler_name': 'http_request',
              'input': {
                'url': 'http://127.0.0.1:8552/health',
                'method': 'GET',
              },
              'required_resource_types': ['API',],
              'metadata': {'draft': True,},
            },
          ],
          'edges': [],
          'explanation': 'Fetch the health endpoint',
        }
        """
    )

    assert parsed["nodes"][0]["node_id"] == "fetch"
    assert parsed["nodes"][0]["input"]["url"] == "http://127.0.0.1:8552/health"
    assert parsed["nodes"][0]["required_resource_types"] == ["API"]
    assert parsed["nodes"][0]["metadata"]["draft"] is True
    assert parsed["explanation"] == "Fetch the health endpoint"
    assert warnings


def test_lit_planner_repairs_incomplete_json_object(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed, warnings = planner._parse_model_output_with_warnings(
        '{"nodes":[{"node_id":"notify","handler_name":"template_render","input":{"template":"Done","values":{}}}],"edges":[],"explanation":"ok"'
    )

    assert parsed["nodes"][0]["handler_name"] == "template_render"
    assert parsed["edges"] == []
    assert parsed["explanation"] == "ok"
    assert warnings


def test_lit_planner_repairs_missing_commas_and_single_quoted_strings(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed, warnings = planner._parse_model_output_with_warnings(
        """
        {
          nodes: [
            {
              'node_id': 'fetch'
              'handler_name': 'http_request'
              'input': {
                'url': 'http://127.0.0.1:8552/health'
                'method': 'GET'
              }
            }
          ]
          'edges': []
          'explanation': 'Fetch latest health'
        }
        """
    )

    assert parsed["nodes"][0]["node_id"] == "fetch"
    assert parsed["nodes"][0]["handler_name"] == "http_request"
    assert parsed["nodes"][0]["input"]["url"] == "http://127.0.0.1:8552/health"
    assert parsed["nodes"][0]["input"]["method"] == "GET"
    assert parsed["edges"] == []
    assert parsed["explanation"] == "Fetch latest health"
    assert warnings


def test_lit_planner_extracts_single_quoted_json_with_braces_inside_strings(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed, warnings = planner._parse_model_output_with_warnings(
        """
        Here is the plan:
        {'nodes': [{'node_id': 'render', 'handler_name': 'template_render', 'input': {'template': 'Use {topic} and {summary}', 'values': {}}}], 'edges': []}
        """
    )

    assert parsed["nodes"][0]["handler_name"] == "template_render"
    assert parsed["nodes"][0]["input"]["template"] == "Use {topic} and {summary}"
    assert parsed["edges"] == []
    assert warnings


def test_lit_planner_retries_with_compact_prompt_on_context_overflow(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    prompt_lengths: list[int] = []

    def fake_invoke_model(planner_prompt: str) -> str:
        prompt_lengths.append(len(planner_prompt))
        if len(prompt_lengths) == 1:
            raise RuntimeError(
                "stream error: INVALID_ARGUMENT: Input token ids are too long. "
                "Exceeding the maximum number of tokens allowed: 4549 >= 4096"
            )
        return json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "notify",
                        "handler_name": "send_message",
                        "input": {
                            "target_agent_name": "observer",
                            "message": {"text": "done"},
                        },
                    }
                ],
                "edges": [],
                "explanation": "Send a completion message.",
            }
        )

    planner._invoke_model = fake_invoke_model  # type: ignore[method-assign]

    result = planner.generate_flow_request(
        prompt="Send a completion message when work is done.",
        catalog=PlannerCatalog(
            handlers=["send_message"],
            agents=[
                {
                    "agent_id": 1,
                    "name": "observer",
                    "role": "worker",
                    "capabilities": [],
                    "communication": {
                        "protocol": "MESSAGE_QUEUE",
                        "endpoint": "queue://observer",
                        "config": {},
                    },
                }
            ],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=3,
    )

    assert len(prompt_lengths) == 2
    assert prompt_lengths[1] < prompt_lengths[0]
    assert any("compacted automatically" in warning for warning in result.warnings)
    assert result.flow_request["nodes"][0]["input"]["target_agent_id"] == 1


def test_lit_planner_normalizes_send_message_target_agent_name(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "notify",
                    "handler_name": "send_message",
                    "input": {
                        "target_agent_name": "observer",
                        "message": {"text": "done"},
                    },
                }
            ],
            "edges": [],
        },
        catalog=PlannerCatalog(
            handlers=["send_message"],
            agents=[
                {
                    "agent_id": 1,
                    "name": "observer",
                    "role": "worker",
                    "capabilities": [],
                    "communication": {
                        "protocol": "MESSAGE_QUEUE",
                        "endpoint": "queue://observer",
                        "config": {},
                    },
                },
                {
                    "agent_id": 2,
                    "name": "audit",
                    "role": "worker",
                    "capabilities": [],
                    "communication": {
                        "protocol": "MESSAGE_QUEUE",
                        "endpoint": "queue://audit",
                        "config": {},
                    },
                },
            ],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=4,
    )

    assert normalized["nodes"][0]["input"]["target_agent_id"] == 1
    assert any("resolved target_agent_name 'observer'" in warning for warning in warnings)


def test_lit_planner_falls_back_to_only_message_target_for_unknown_name(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "notify",
                    "handler_name": "send_message",
                    "input": {
                        "target_agent_name": "ops-archiver",
                        "message": {"text": "done"},
                    },
                }
            ],
            "edges": [],
        },
        catalog=PlannerCatalog(
            handlers=["send_message"],
            agents=[
                {
                    "agent_id": 7,
                    "name": "observer",
                    "role": "worker",
                    "capabilities": [],
                    "communication": {
                        "protocol": "MESSAGE_QUEUE",
                        "endpoint": "queue://observer",
                        "config": {},
                    },
                }
            ],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=4,
    )

    assert normalized["nodes"][0]["input"]["target_agent_id"] == 7
    assert any("referenced unknown agent 'ops-archiver'; defaulted to the only communication-enabled agent" in warning for warning in warnings)


def test_lit_planner_omits_send_message_when_no_communication_target_exists(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "fetch",
                    "handler_name": "template_render",
                    "input": {
                        "template": "fetched",
                        "values": {},
                    },
                },
                {
                    "node_id": "send_completion_message",
                    "handler_name": "send_message",
                    "input": {
                        "message": {"text": "done"},
                    },
                    "dependencies": ["fetch"],
                },
                {
                    "node_id": "persist",
                    "handler_name": "json_serialize",
                    "input": {},
                    "dependencies": ["send_completion_message"],
                },
            ],
            "edges": [
                {"from_node": "fetch", "to_node": "send_completion_message", "condition": "True"},
                {"from_node": "send_completion_message", "to_node": "persist", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["template_render", "send_message", "json_serialize"],
            agents=[],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=5,
    )

    assert [node["node_id"] for node in normalized["nodes"]] == ["fetch", "persist"]
    assert normalized["edges"] == [
        {
            "from_node": "fetch",
            "to_node": "persist",
            "condition": "True",
        }
    ]
    assert normalized["nodes"][1]["dependencies"] == ["fetch"]
    assert any(
        "send_message node 'send_completion_message' was omitted because no communication-enabled target agent is registered"
        in warning
        for warning in warnings
    )
    assert any("rewired 1 edge(s)" in warning for warning in warnings)


def test_lit_planner_repairs_agent_name_used_as_handler(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "node-2",
                    "title": "Split robotics and AI topics",
                    "handler_name": "triage-router",
                    "input": {
                        "items": {"$ref": "results['node-1']['items']"},
                    },
                }
            ],
            "edges": [],
        },
        catalog=PlannerCatalog(
            handlers=["news_search", "topic_split", "write_csv"],
            agents=[
                {
                    "agent_id": 5,
                    "name": "triage-router",
                    "role": "router",
                    "capabilities": [],
                    "communication": None,
                }
            ],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=4,
    )

    assert normalized["nodes"][0]["handler_name"] == "topic_split"
    assert normalized["nodes"][0]["preferred_agent_id"] == 5
    assert normalized["nodes"][0]["input"]["topics"] == ["Robotik", "KI"]
    assert any("replaced it with 'topic_split'" in warning for warning in warnings)


def test_lit_planner_repairs_filesystem_security_audit_flow(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "file_load",
                    "title": "Load local source file",
                    "handler_name": "filesystem_read",
                    "input": {"file": "my_server.ts"},
                },
                {
                    "node_id": "vulnerability_scan",
                    "title": "Security audit using nova-system-agent",
                    "handler_name": "nova-system-agent",
                    "input": {"code": "{{file_load.content}}"},
                    "dependencies": ["file_load"],
                },
                {
                    "node_id": "write_report",
                    "title": "Write audit report",
                    "handler_name": "filesystem_write",
                    "input": {"path": "sl.txt", "code": "{{vulnerability_scan.text}}"},
                    "dependencies": ["vulnerability_scan"],
                },
            ],
            "edges": [
                {"from_node": "file_load", "to_node": "vulnerability_scan", "condition": "True"},
                {"from_node": "vulnerability_scan", "to_node": "write_report", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["filesystem_read", "local_llm_text", "filesystem_write"],
            agents=[
                {
                    "agent_id": 9,
                    "name": "nova-system-agent",
                    "role": "system",
                    "capabilities": [],
                    "communication": None,
                }
            ],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=4,
    )

    file_load = next(node for node in normalized["nodes"] if node["node_id"] == "file_load")
    vulnerability_scan = next(node for node in normalized["nodes"] if node["node_id"] == "vulnerability_scan")
    write_report = next(node for node in normalized["nodes"] if node["node_id"] == "write_report")

    assert file_load["handler_name"] == "filesystem_read"
    assert file_load["input"]["path"] == "my_server.ts"
    assert vulnerability_scan["handler_name"] == "local_llm_text"
    assert vulnerability_scan["preferred_agent_id"] == 9
    assert vulnerability_scan["input"]["data"] == {"$ref": "results['file_load']['content']"}
    assert "Audit the provided source code for security vulnerabilities" in vulnerability_scan["input"]["instruction"]
    assert write_report["handler_name"] == "filesystem_write"
    assert write_report["input"]["content"] == {"$ref": "results['vulnerability_scan']['text']"}
    assert any("normalized it to 'local_llm_text'" in warning or "replaced it with 'local_llm_text'" in warning for warning in warnings)


def test_lit_planner_local_llm_text_defaults_upstream_data_even_when_prompt_exists(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "file_load",
                    "handler_name": "filesystem_read",
                    "input": {"path": "my_server.ts"},
                },
                {
                    "node_id": "format_report",
                    "title": "Format structured report",
                    "handler_name": "local_llm_text",
                    "input": {
                        "prompt": "Please provide the ${vulnerability_scan.result} so I can format it."
                    },
                    "dependencies": ["file_load"],
                },
            ],
            "edges": [
                {"from_node": "file_load", "to_node": "format_report", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["filesystem_read", "local_llm_text"],
            agents=[],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=4,
    )

    format_report = next(node for node in normalized["nodes"] if node["node_id"] == "format_report")
    assert format_report["input"]["data"] == {"$ref": "results['file_load']['content']"}
    assert any(
        "local_llm_text node 'format_report' had no data; defaulted to upstream 'file_load.content' reference"
        in warning
        for warning in warnings
    )


def test_lit_planner_repairs_topic_split_and_write_csv_upstream_references(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "search-news",
                    "handler_name": "news_search",
                    "input": {"query": "Robotik und KI"},
                },
                {
                    "node_id": "split-topics",
                    "title": "Split Topics",
                    "handler_name": "topic_split",
                    "input": {
                        "items": "news_search.output",
                        "to": ["Robotik", "KI"],
                    },
                    "dependencies": ["search-news"],
                },
                {
                    "node_id": "write-csv",
                    "handler_name": "write_csv",
                    "input": {
                        "path": "test.csv",
                        "rows": "split-topics.output",
                    },
                    "dependencies": ["split-topics"],
                },
            ],
            "edges": [
                {"from_node": "search-news", "to_node": "split-topics", "condition": "True"},
                {"from_node": "split-topics", "to_node": "write-csv", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["news_search", "topic_split", "write_csv"],
            agents=[],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=5,
    )

    split_node = next(node for node in normalized["nodes"] if node["node_id"] == "split-topics")
    write_csv_node = next(node for node in normalized["nodes"] if node["node_id"] == "write-csv")

    assert split_node["input"]["items"] == {"$ref": "results['search-news']['items']"}
    assert split_node["input"]["topics"] == ["Robotik", "KI"]
    assert write_csv_node["input"]["rows"] == {"$ref": "results['split-topics']['csv_rows']"}
    assert any("used 'to'; remapped to 'topics'" in warning for warning in warnings)
    assert any("converted string items to upstream 'search-news.items' reference" in warning for warning in warnings)
    assert any("converted string rows to upstream 'split-topics.csv_rows' reference" in warning for warning in warnings)


def test_lit_planner_replaces_placeholder_write_csv_fieldnames_for_topic_split(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "search_news",
                    "handler_name": "news_search",
                    "input": {"query": "Robotik und KI"},
                },
                {
                    "node_id": "topic_split",
                    "handler_name": "topic_split",
                    "input": {
                        "items": {"$ref": "results['search_news']['items']"},
                        "topics": ["Robotik", "KI"],
                    },
                    "dependencies": ["search_news"],
                },
                {
                    "node_id": "write_csv",
                    "handler_name": "write_csv",
                    "input": {
                        "path": "test.csv",
                        "rows": {"$ref": "results['topic_split']['csv_rows']"},
                        "fieldnames": ["topic", "item_id", "embedding_vector_placeholder"],
                    },
                    "dependencies": ["topic_split"],
                },
            ],
            "edges": [
                {"from_node": "search_news", "to_node": "topic_split", "condition": "True"},
                {"from_node": "topic_split", "to_node": "write_csv", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["news_search", "topic_split", "write_csv"],
            agents=[],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=5,
    )

    write_csv_node = next(node for node in normalized["nodes"] if node["node_id"] == "write_csv")

    assert write_csv_node["input"]["fieldnames"] == [
        "topic",
        "title",
        "source",
        "published_at",
        "link",
        "summary",
    ]
    assert any(
        "write_csv node 'write_csv' replaced incompatible fieldnames with topic_split CSV columns" in warning
        for warning in warnings
    )


def test_lit_planner_rewires_write_csv_from_generate_embedding_back_to_topic_split_csv_rows(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "search_news",
                    "handler_name": "news_search",
                    "input": {"query": "Robotik und KI"},
                },
                {
                    "node_id": "topic_split",
                    "handler_name": "topic_split",
                    "input": {
                        "items": {"$ref": "results['search_news']['items']"},
                        "topics": ["Robotik", "KI"],
                    },
                    "dependencies": ["search_news"],
                },
                {
                    "node_id": "generate_embedding",
                    "handler_name": "generate_embedding",
                    "input": {"data": {"$ref": "results['topic_split']"}},
                    "dependencies": ["topic_split"],
                },
                {
                    "node_id": "write_csv",
                    "handler_name": "write_csv",
                    "input": {
                        "path": "test.csv",
                        "rows": {"$ref": "results['generate_embedding']"},
                    },
                    "dependencies": ["generate_embedding"],
                },
            ],
            "edges": [
                {"from_node": "search_news", "to_node": "topic_split", "condition": "True"},
                {"from_node": "topic_split", "to_node": "generate_embedding", "condition": "True"},
                {"from_node": "generate_embedding", "to_node": "write_csv", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["news_search", "topic_split", "generate_embedding", "write_csv"],
            agents=[],
            resources=[],
            memory_systems=[],
        ),
        max_nodes=6,
    )

    write_csv_node = next(node for node in normalized["nodes"] if node["node_id"] == "write_csv")

    assert write_csv_node["input"]["rows"] == {"$ref": "results['topic_split']['csv_rows']"}
    assert write_csv_node["input"]["fieldnames"] == [
        "topic",
        "title",
        "source",
        "published_at",
        "link",
        "summary",
    ]
    assert any(
        "write_csv node 'write_csv' rewired rows to upstream topic_split 'topic_split.csv_rows' for news export"
        in warning
        for warning in warnings
    )


def test_lit_planner_repairs_generate_embedding_and_vector_memory_store_inputs(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "topic_split",
                    "handler_name": "topic_split",
                    "input": {
                        "items": {"$ref": "results['search_news']['items']"},
                        "topics": ["Robotik", "KI"],
                    },
                    "dependencies": ["search_news"],
                },
                {
                    "node_id": "generate_embedding",
                    "handler_name": "generate_embedding",
                    "input": {
                        "data": "topic_split.output",
                    },
                    "dependencies": ["topic_split"],
                },
                {
                    "node_id": "store_results",
                    "handler_name": "memory_store",
                    "input": {
                        "memory_id": "planner-vector",
                        "key": "filtered_news",
                    },
                    "dependencies": ["generate_embedding"],
                },
            ],
            "edges": [
                {"from_node": "topic_split", "to_node": "generate_embedding", "condition": "True"},
                {"from_node": "generate_embedding", "to_node": "store_results", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["topic_split", "generate_embedding", "memory_store"],
            agents=[],
            resources=[],
            memory_systems=[{"memory_id": "planner-vector"}],
        ),
        max_nodes=5,
    )

    embedding_node = next(node for node in normalized["nodes"] if node["node_id"] == "generate_embedding")
    store_node = next(node for node in normalized["nodes"] if node["node_id"] == "store_results")

    assert embedding_node["input"]["data"] == {"$ref": "results['topic_split']"}
    assert store_node["input"]["value"] == {"$ref": "results['generate_embedding']"}
    assert any(
        "converted string data to upstream 'topic_split' result reference" in warning
        for warning in warnings
    )
    assert not any(
        "memory_store node 'store_results' had no value; defaulted to upstream result reference" in warning
        for warning in warnings
    )


def test_lit_planner_replaces_placeholder_vector_payload_shells_with_upstream_references(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    normalized, warnings = planner._normalize_flow_request(
        parsed={
            "nodes": [
                {
                    "node_id": "topic_split",
                    "handler_name": "topic_split",
                    "input": {
                        "items": {"$ref": "results['search_news']['items']"},
                        "topics": ["Robotik", "KI"],
                    },
                    "dependencies": ["search_news"],
                },
                {
                    "node_id": "generate_embedding",
                    "handler_name": "generate_embedding",
                    "input": {
                        "data": {"items": []},
                    },
                    "dependencies": ["topic_split"],
                },
                {
                    "node_id": "store_results",
                    "handler_name": "memory_store",
                    "input": {
                        "memory_id": "planner-vector",
                        "key": "filtered_news",
                        "value": {
                            "embedding": "...",
                            "value": "...",
                            "metadata": "...",
                        },
                    },
                    "dependencies": ["generate_embedding"],
                },
            ],
            "edges": [
                {"from_node": "topic_split", "to_node": "generate_embedding", "condition": "True"},
                {"from_node": "generate_embedding", "to_node": "store_results", "condition": "True"},
            ],
        },
        catalog=PlannerCatalog(
            handlers=["topic_split", "generate_embedding", "memory_store"],
            agents=[],
            resources=[],
            memory_systems=[{"memory_id": "planner-vector"}],
        ),
        max_nodes=5,
    )

    embedding_node = next(node for node in normalized["nodes"] if node["node_id"] == "generate_embedding")
    store_node = next(node for node in normalized["nodes"] if node["node_id"] == "store_results")

    assert embedding_node["input"]["data"] == {"$ref": "results['topic_split']"}
    assert store_node["input"]["value"] == {"$ref": "results['generate_embedding']"}
    assert any(
        "generate_embedding node 'generate_embedding' replaced placeholder data shell with upstream 'topic_split' result reference"
        in warning
        for warning in warnings
    )
    assert any(
        "memory_store node 'store_results' replaced placeholder value shell with upstream 'generate_embedding' result reference"
        in warning
        for warning in warnings
    )


def test_lit_planner_tolerates_ellipsis_placeholder_in_literal_repair(tmp_path: Path) -> None:
    planner = LiteRTPlanner(build_settings(tmp_path))
    parsed, warnings = planner._parse_model_output_with_warnings(
        """{'nodes': [{'node_id': 'search_news', 'handler_name': 'news_search', 'input': {'query': 'Robotik und KI', 'max_items': ...}}], 'edges': []}"""
    )

    assert parsed["nodes"][0]["input"]["max_items"] is None
    assert any("Unsupported placeholder values were replaced with null" in warning for warning in warnings)


def test_lit_planner_retries_after_quarantining_stale_xnnpack_cache(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    binary_path = tmp_path / "LIT" / "lit.windows_x86_64.exe"
    model_path = tmp_path / "LIT" / "model_multimodal.litertlm"
    cache_path = Path(f"{model_path}.xnnpack_cache")
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_text("binary", encoding="utf-8")
    model_path.write_text("model", encoding="utf-8")
    cache_path.write_text("stale-cache", encoding="utf-8")
    settings.lit_binary_path = str(binary_path)
    settings.lit_model_path = str(model_path)
    planner = LiteRTPlanner(settings)

    results = [
        subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr=(
                "INFO: Created TensorFlow Lite XNNPACK delegate for CPU.\n"
                "ERROR: third_party/tensorflow/lite/delegates/xnnpack/weight_cache.cc:721: "
                "Cannot get the address of a buffer in a cache before the build step that introduces it has finished."
            ),
        ),
        subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"nodes":[],"edges":[],"explanation":"ok"}',
            stderr="",
        ),
    ]

    with patch("nova_synesis.planning.lit_planner.subprocess.run", side_effect=results) as mocked_run:
        output = planner._invoke_model("Return JSON.")

    assert '"nodes":[]' in output
    assert mocked_run.call_count == 2
    assert not cache_path.exists()
    quarantined = list(cache_path.parent.glob(f"{cache_path.name}.stale-*"))
    assert len(quarantined) == 1


def test_lit_planner_surfaces_clear_engine_error_after_cache_retry_fails(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    binary_path = tmp_path / "LIT" / "lit.windows_x86_64.exe"
    model_path = tmp_path / "LIT" / "model_multimodal.litertlm"
    cache_path = Path(f"{model_path}.xnnpack_cache")
    binary_path.parent.mkdir(parents=True, exist_ok=True)
    binary_path.write_text("binary", encoding="utf-8")
    model_path.write_text("model", encoding="utf-8")
    cache_path.write_text("stale-cache", encoding="utf-8")
    settings.lit_binary_path = str(binary_path)
    settings.lit_model_path = str(model_path)
    planner = LiteRTPlanner(settings)

    results = [
        subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="INFO: Created TensorFlow Lite XNNPACK delegate for CPU. Error: failed to create engine: failed to create engine",
        ),
        subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="INFO: Created TensorFlow Lite XNNPACK delegate for CPU. Error: failed to create engine: failed to create engine",
        ),
    ]

    with patch("nova_synesis.planning.lit_planner.subprocess.run", side_effect=results):
        with pytest.raises(RuntimeError, match="LiteRT could not create an inference engine"):
            planner._invoke_model("Return JSON.")

    quarantined = list(cache_path.parent.glob(f"{cache_path.name}.stale-*"))
    assert len(quarantined) == 1


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


def test_accounts_receivable_workflow_from_csv_generates_letters(tmp_path: Path) -> None:
    orders_csv = tmp_path / "orders.csv"
    orders_csv.write_text(
        "\n".join(
            [
                "customer_name,email,address,product,quantity,price_per_unit,total_price,order_date,delivery_date,invoice_due_date,invoice_paid",
                "Alice Example,alice@example.org,Alpha Strasse 1 10115 Berlin,Laptop,1,1200.0,1200.0,2026-03-01T08:00:00,2026-03-02T08:00:00,2026-03-10T08:00:00,0",
                "Alice Example,alice@example.org,Alpha Strasse 1 10115 Berlin,Monitor,2,300.0,600.0,2026-03-05T08:00:00,2026-03-06T08:00:00,2026-03-15T08:00:00,0",
                "Bob Example,bob@example.org,Beta Weg 2 80331 Muenchen,Mouse,4,40.0,160.0,2026-03-09T08:00:00,2026-03-10T08:00:00,2026-03-20T08:00:00,1",
                "Cara Example,cara@example.org,Gamma Platz 3 50667 Koeln,Keyboard,2,80.0,160.0,2026-03-11T08:00:00,2026-03-12T08:00:00,2026-03-22T08:00:00,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            flow = orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "extract_open_receivables",
                        "handler_name": "accounts_receivable_extract",
                        "input": {
                            "path": "orders.csv",
                            "source_type": "csv",
                            "as_of": "2026-04-09T00:00:00+00:00",
                        },
                    },
                    {
                        "node_id": "serialize_receivables",
                        "handler_name": "json_serialize",
                        "input": {
                            "value": {"$ref": "results['extract_open_receivables']"},
                            "indent": 2,
                        },
                    },
                    {
                        "node_id": "write_receivables_report",
                        "handler_name": "write_file",
                        "input": {
                            "path": "output/open-receivables.json",
                            "content": "{{ results['serialize_receivables']['json'] }}",
                            "encoding": "utf-8",
                        },
                    },
                    {
                        "node_id": "generate_letters",
                        "handler_name": "accounts_receivable_generate_letters",
                        "input": {
                            "receivables": {"$ref": "results['extract_open_receivables']"},
                            "sender_company": "Example Finance",
                            "sender_email": "finance@example.org",
                            "sender_phone": "+49 30 000000",
                            "sender_address": "Finance Street 1, 10115 Berlin",
                            "payment_deadline_days": 10,
                        },
                    },
                    {
                        "node_id": "write_letters",
                        "handler_name": "accounts_receivable_write_letters",
                        "input": {
                            "letters": {"$ref": "results['generate_letters']['letters']"},
                            "output_directory": "billing",
                            "manifest_path": "output/letters-manifest.json",
                            "summary_path": "output/letters-summary.txt",
                            "output_format": "docx",
                        },
                    },
                ],
                edges=[
                    {"from_node": "extract_open_receivables", "to_node": "serialize_receivables", "condition": "True"},
                    {"from_node": "serialize_receivables", "to_node": "write_receivables_report", "condition": "True"},
                    {
                        "from_node": "extract_open_receivables",
                        "to_node": "generate_letters",
                        "condition": "results['extract_open_receivables']['customer_count'] > 0",
                    },
                    {"from_node": "generate_letters", "to_node": "write_letters", "condition": "True"},
                ],
            )

            snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
            assert snapshot["state"] == "COMPLETED"
            assert snapshot["results"]["extract_open_receivables"]["customer_count"] == 2
            assert snapshot["results"]["extract_open_receivables"]["invoice_count"] == 3
            assert snapshot["results"]["extract_open_receivables"]["total_outstanding"] == 1960.0
            assert snapshot["results"]["generate_letters"]["letter_count"] == 2
            assert snapshot["results"]["write_letters"]["letter_count"] == 2

            report = json.loads((tmp_path / "output" / "open-receivables.json").read_text(encoding="utf-8"))
            assert report["customer_count"] == 2

            letters = sorted((tmp_path / "billing").glob("*.docx"))
            assert len(letters) == 2
            with zipfile.ZipFile(letters[0]) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            assert "Alice Example" in document_xml
            assert "Example Finance" in document_xml

            summary_text = (tmp_path / "output" / "letters-summary.txt").read_text(encoding="utf-8")
            assert "Anzahl Schreiben: 2" in summary_text
            assert ".docx" in summary_text
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_news_search_topic_split_and_write_csv_workflow(tmp_path: Path) -> None:
    rss_payload = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Neuer Roboter fuer Fabriken - Example Robotics</title>
      <link>https://example.invalid/robotik</link>
      <description>Ein neuer Roboter verbessert die Automation.</description>
      <pubDate>Sat, 11 Apr 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>KI Modell verbessert Diagnosen - Example AI</title>
      <link>https://example.invalid/ki</link>
      <description>Ein neues KI System analysiert medizinische Daten.</description>
      <pubDate>Sat, 11 Apr 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    async def fake_get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        assert url == "https://news.google.com/rss/search"
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(200, text=rss_payload, request=request)

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            orchestrator.register_memory_system(
                "planner-scratch",
                MemoryType.LONG_TERM,
                config={"planner_visible": True, "allow_untrusted_ingest": True},
            )
            with patch("nova_synesis.runtime.handlers.httpx.AsyncClient.get", new=fake_get):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "search_news",
                            "handler_name": "news_search",
                            "input": {"query": "IT Nachrichten", "max_items": 10},
                        },
                        {
                            "node_id": "split_topics",
                            "handler_name": "topic_split",
                            "input": {
                                "items": {"$ref": "results['search_news']['items']"},
                                "topics": ["Robotik", "KI"],
                            },
                            "dependencies": ["search_news"],
                        },
                        {
                            "node_id": "store_topics",
                            "handler_name": "memory_store",
                            "input": {
                                "memory_id": "planner-scratch",
                                "key": "it-news",
                                "value": {"$ref": "results['split_topics']"},
                            },
                            "dependencies": ["split_topics"],
                        },
                        {
                            "node_id": "write_news_csv",
                            "handler_name": "write_csv",
                            "input": {
                                "path": "test.csv",
                                "rows": {"$ref": "results['split_topics']['csv_rows']"},
                            },
                            "dependencies": ["split_topics"],
                        },
                    ]
                )

                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
                assert snapshot["state"] == "COMPLETED"
                csv_path = tmp_path / "test.csv"
                assert csv_path.exists()
                csv_text = csv_path.read_text(encoding="utf-8")
                assert "Robotik" in csv_text
                assert "KI" in csv_text
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_news_search_topic_split_generate_embedding_and_vector_store_workflow(tmp_path: Path) -> None:
    rss_payload = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Neuer Roboter fuer Fabriken - Example Robotics</title>
      <link>https://example.invalid/robotik</link>
      <description>Ein neuer Roboter verbessert die Automation.</description>
      <pubDate>Sat, 11 Apr 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>KI Modell verbessert Diagnosen - Example AI</title>
      <link>https://example.invalid/ki</link>
      <description>Ein neues KI System analysiert medizinische Daten.</description>
      <pubDate>Sat, 11 Apr 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    async def fake_get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        assert url == "https://news.google.com/rss/search"
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(200, text=rss_payload, request=request)

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            orchestrator.register_memory_system(
                "planner-vector",
                MemoryType.VECTOR,
                config={"planner_visible": True, "allow_untrusted_ingest": True},
            )
            with patch("nova_synesis.runtime.handlers.httpx.AsyncClient.get", new=fake_get):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "search_news",
                            "handler_name": "news_search",
                            "input": {"query": "Robotik und KI", "max_items": 10},
                        },
                        {
                            "node_id": "topic_split",
                            "handler_name": "topic_split",
                            "input": {
                                "items": {"$ref": "results['search_news']['items']"},
                                "topics": ["Robotik", "KI"],
                            },
                            "dependencies": ["search_news"],
                        },
                        {
                            "node_id": "generate_embedding",
                            "handler_name": "generate_embedding",
                            "input": {
                                "data": {"$ref": "results['topic_split']"},
                            },
                            "dependencies": ["topic_split"],
                        },
                        {
                            "node_id": "store_results",
                            "handler_name": "memory_store",
                            "input": {
                                "memory_id": "planner-vector",
                                "key": "filtered_news",
                                "value": {"$ref": "results['generate_embedding']"},
                            },
                            "dependencies": ["generate_embedding"],
                        },
                        {
                            "node_id": "write_csv",
                            "handler_name": "write_csv",
                            "input": {
                                "path": "test.csv",
                                "rows": {"$ref": "results['topic_split']['csv_rows']"},
                            },
                            "dependencies": ["topic_split"],
                        },
                    ],
                    edges=[
                        {"from_node": "search_news", "to_node": "topic_split", "condition": "True"},
                        {"from_node": "topic_split", "to_node": "generate_embedding", "condition": "True"},
                        {"from_node": "generate_embedding", "to_node": "store_results", "condition": "True"},
                        {"from_node": "topic_split", "to_node": "write_csv", "condition": "True"},
                    ],
                )

                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
                assert snapshot["state"] == "COMPLETED"
                csv_path = tmp_path / "test.csv"
                assert csv_path.exists()
                csv_text = csv_path.read_text(encoding="utf-8")
                assert "Robotik" in csv_text
                assert "KI" in csv_text
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_memory_store_runtime_repairs_placeholder_vector_payload_from_upstream_embedding(tmp_path: Path) -> None:
    rss_payload = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Neuer Roboter fuer Fabriken - Example Robotics</title>
      <link>https://example.invalid/robotik</link>
      <description>Ein neuer Roboter verbessert die Automation.</description>
      <pubDate>Sat, 11 Apr 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>KI Modell verbessert Diagnosen - Example AI</title>
      <link>https://example.invalid/ki</link>
      <description>Ein neues KI System analysiert medizinische Daten.</description>
      <pubDate>Sat, 11 Apr 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    async def fake_get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        assert url == "https://news.google.com/rss/search"
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(200, text=rss_payload, request=request)

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            orchestrator.register_memory_system(
                "planner-vector",
                MemoryType.VECTOR,
                config={"planner_visible": True, "allow_untrusted_ingest": True},
            )
            with patch("nova_synesis.runtime.handlers.httpx.AsyncClient.get", new=fake_get):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "search_news",
                            "handler_name": "news_search",
                            "input": {"query": "Robotik und KI", "max_items": 10},
                        },
                        {
                            "node_id": "topic_split",
                            "handler_name": "topic_split",
                            "input": {
                                "items": {"$ref": "results['search_news']['items']"},
                                "topics": ["Robotik", "KI"],
                            },
                            "dependencies": ["search_news"],
                        },
                        {
                            "node_id": "generate_embedding",
                            "handler_name": "generate_embedding",
                            "input": {
                                "data": {"$ref": "results['topic_split']"},
                            },
                            "dependencies": ["topic_split"],
                        },
                        {
                            "node_id": "store_results",
                            "handler_name": "memory_store",
                            "input": {
                                "memory_id": "planner-vector",
                                "key": "filtered_news",
                                "value": {
                                    "embedding": "...",
                                    "value": "...",
                                    "metadata": "...",
                                },
                            },
                            "dependencies": ["generate_embedding"],
                        },
                    ],
                    edges=[
                        {"from_node": "search_news", "to_node": "topic_split", "condition": "True"},
                        {"from_node": "topic_split", "to_node": "generate_embedding", "condition": "True"},
                        {"from_node": "generate_embedding", "to_node": "store_results", "condition": "True"},
                    ],
                )

                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
                assert snapshot["state"] == "COMPLETED"
                assert snapshot["results"]["store_results"]["auto_repaired_value"] is True
                assert snapshot["results"]["store_results"]["auto_repaired_value_from_node"] == "generate_embedding"
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_write_csv_runtime_replaces_placeholder_fieldnames_with_detected_columns(tmp_path: Path) -> None:
    rss_payload = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Neuer Roboter fuer Fabriken - Example Robotics</title>
      <link>https://example.invalid/robotik</link>
      <description>Ein neuer Roboter verbessert die Automation.</description>
      <pubDate>Sat, 11 Apr 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>KI Modell verbessert Diagnosen - Example AI</title>
      <link>https://example.invalid/ki</link>
      <description>Ein neues KI System analysiert medizinische Daten.</description>
      <pubDate>Sat, 11 Apr 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    async def fake_get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        assert url == "https://news.google.com/rss/search"
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(200, text=rss_payload, request=request)

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            with patch("nova_synesis.runtime.handlers.httpx.AsyncClient.get", new=fake_get):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "search_news",
                            "handler_name": "news_search",
                            "input": {"query": "Robotik und KI", "max_items": 10},
                        },
                        {
                            "node_id": "topic_split",
                            "handler_name": "topic_split",
                            "input": {
                                "items": {"$ref": "results['search_news']['items']"},
                                "topics": ["Robotik", "KI"],
                            },
                            "dependencies": ["search_news"],
                        },
                        {
                            "node_id": "write_csv",
                            "handler_name": "write_csv",
                            "input": {
                                "path": "test.csv",
                                "rows": {"$ref": "results['topic_split']['csv_rows']"},
                                "fieldnames": ["topic", "item_id", "embedding_vector_placeholder"],
                            },
                            "dependencies": ["topic_split"],
                        },
                    ],
                    edges=[
                        {"from_node": "search_news", "to_node": "topic_split", "condition": "True"},
                        {"from_node": "topic_split", "to_node": "write_csv", "condition": "True"},
                    ],
                )

                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
                assert snapshot["state"] == "COMPLETED"
                csv_path = tmp_path / "test.csv"
                assert csv_path.exists()
                csv_text = csv_path.read_text(encoding="utf-8")
                assert "topic,title,source,published_at,link,summary" in csv_text
                assert "embedding_vector_placeholder" not in csv_text
                assert "Neuer Roboter fuer Fabriken" in csv_text
                assert "KI Modell verbessert Diagnosen" in csv_text
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_accounts_receivable_workflow_from_sqlite_generates_letters(tmp_path: Path) -> None:
    orders_db = tmp_path / "orders.db"
    with sqlite3.connect(orders_db) as connection:
        connection.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                email TEXT,
                address TEXT,
                product TEXT,
                quantity INTEGER,
                price_per_unit REAL,
                total_price REAL,
                order_date TEXT,
                delivery_date TEXT,
                invoice_due_date TEXT,
                invoice_paid INTEGER
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO orders (
                customer_name, email, address, product, quantity, price_per_unit, total_price,
                order_date, delivery_date, invoice_due_date, invoice_paid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Delta Example",
                    "delta@example.org",
                    "Delta Allee 4 20095 Hamburg",
                    "Server",
                    1,
                    2400.0,
                    2400.0,
                    "2026-03-01T08:00:00",
                    "2026-03-03T08:00:00",
                    "2026-03-20T08:00:00",
                    0,
                ),
                (
                    "Echo Example",
                    "echo@example.org",
                    "Echo Ring 5 04109 Leipzig",
                    "Monitor",
                    2,
                    300.0,
                    600.0,
                    "2026-03-10T08:00:00",
                    "2026-03-11T08:00:00",
                    "2026-04-10T08:00:00",
                    0,
                ),
                (
                    "Foxtrot Example",
                    "foxtrot@example.org",
                    "Foxtrot Weg 6 01067 Dresden",
                    "Keyboard",
                    2,
                    80.0,
                    160.0,
                    "2026-03-11T08:00:00",
                    "2026-03-12T08:00:00",
                    "2026-04-12T08:00:00",
                    1,
                ),
            ],
        )
        connection.commit()

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            flow = orchestrator.create_flow(
                nodes=[
                    {
                        "node_id": "extract_open_receivables",
                        "handler_name": "accounts_receivable_extract",
                        "input": {
                            "path": "orders.db",
                            "source_type": "sqlite",
                            "table": "orders",
                            "as_of": "2026-04-09T00:00:00+00:00",
                        },
                    },
                    {
                        "node_id": "generate_letters",
                        "handler_name": "accounts_receivable_generate_letters",
                        "input": {
                            "receivables": {"$ref": "results['extract_open_receivables']"},
                            "sender_company": "Example Finance",
                            "payment_deadline_days": 5,
                        },
                    },
                    {
                        "node_id": "write_letters",
                        "handler_name": "accounts_receivable_write_letters",
                        "input": {
                            "letters": {"$ref": "results['generate_letters']['letters']"},
                            "output_directory": "billing/db",
                            "manifest_path": "db-output/letters-manifest.json",
                            "summary_path": "db-output/letters-summary.txt",
                            "output_format": "docx",
                        },
                    },
                ],
                edges=[
                    {
                        "from_node": "extract_open_receivables",
                        "to_node": "generate_letters",
                        "condition": "results['extract_open_receivables']['customer_count'] > 0",
                    },
                    {"from_node": "generate_letters", "to_node": "write_letters", "condition": "True"},
                ],
            )

            snapshot = await orchestrator.run_flow(int(flow["flow_id"]))
            assert snapshot["state"] == "COMPLETED"
            extract_result = snapshot["results"]["extract_open_receivables"]
            assert extract_result["source_type"] == "sqlite"
            assert extract_result["customer_count"] == 2
            assert extract_result["invoice_count"] == 2
            assert extract_result["overdue_count"] == 1

            manifest = json.loads((tmp_path / "db-output" / "letters-manifest.json").read_text(encoding="utf-8"))
            assert manifest["letter_count"] == 2
            assert any(item["customer_name"] == "Delta Example" for item in manifest["letters"])
            assert all(str(item["path"]).endswith(".docx") for item in manifest["letters"])
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_accounts_receivable_workflow_can_generate_letter_text_with_local_llm(tmp_path: Path) -> None:
    orders_csv = tmp_path / "orders.csv"
    orders_csv.write_text(
        "\n".join(
            [
                "customer_name,email,address,product,quantity,price_per_unit,total_price,order_date,delivery_date,invoice_due_date,invoice_paid",
                "Alice Example,alice@example.org,Alpha Strasse 1 10115 Berlin,Laptop,1,1200.0,1200.0,2026-03-01T08:00:00,2026-03-02T08:00:00,2026-03-10T08:00:00,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_llm(prompt: str, settings: Settings, *, timeout_s: int | None = None) -> str:
        assert settings.lit_backend == "cpu"
        assert "Alice Example" in prompt
        assert "Bitte freundlich, bestimmt und klar formulieren." in prompt
        assert timeout_s is None
        return (
            "NOVA-SYNESIS Finance Desk\n"
            "2026-04-09\n\n"
            "Alice Example\n"
            "Betreff: Zahlungserinnerung\n\n"
            "bitte begleichen Sie den offenen Betrag in Hoehe von 1.200,00 EUR.\n"
            "Dies ist ein individuell per lokalem LLM formulierter Brief."
        )

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            with patch("nova_synesis.runtime.handlers._generate_local_text", side_effect=fake_llm):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "extract_open_receivables",
                            "handler_name": "accounts_receivable_extract",
                            "input": {
                                "path": "orders.csv",
                                "source_type": "csv",
                                "as_of": "2026-04-09T00:00:00+00:00",
                            },
                        },
                        {
                            "node_id": "generate_letters",
                            "handler_name": "accounts_receivable_generate_letters",
                            "input": {
                                "receivables": {"$ref": "results['extract_open_receivables']"},
                                "sender_company": "Example Finance",
                                "sender_email": "finance@example.org",
                                "sender_phone": "+49 30 000000",
                                "sender_address": "Finance Street 1, 10115 Berlin",
                                "payment_deadline_days": 7,
                                "generation_mode": "llm",
                                "user_instruction": "Bitte freundlich, bestimmt und klar formulieren.",
                                "prompt_template": (
                                    "Schreibe ein deutsches Anschreiben an {customer_name}.\n"
                                    "Absender: {sender_company}\n"
                                    "Offene Rechnungen:\n{invoice_lines}\n"
                                    "Anweisung: {user_instruction}"
                                ),
                                "fallback_to_template_on_error": False,
                            },
                        },
                        {
                            "node_id": "write_letters",
                            "handler_name": "accounts_receivable_write_letters",
                            "input": {
                                "letters": {"$ref": "results['generate_letters']['letters']"},
                                "output_directory": "billing/llm",
                                "manifest_path": "output/llm-letters-manifest.json",
                                "summary_path": "output/llm-letters-summary.txt",
                                "output_format": "docx",
                            },
                        },
                    ],
                    edges=[
                        {
                            "from_node": "extract_open_receivables",
                            "to_node": "generate_letters",
                            "condition": "results['extract_open_receivables']['customer_count'] > 0",
                        },
                        {"from_node": "generate_letters", "to_node": "write_letters", "condition": "True"},
                    ],
                )

                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))

            assert snapshot["state"] == "COMPLETED"
            generate_result = snapshot["results"]["generate_letters"]
            assert generate_result["generation_mode"] == "llm"
            assert generate_result["llm"]["enabled"] is True
            assert generate_result["warnings"] == []
            assert generate_result["letters"][0]["generation_mode"] == "llm"

            letters = sorted((tmp_path / "billing" / "llm").glob("*.docx"))
            assert len(letters) == 1
            with zipfile.ZipFile(letters[0]) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            assert "individuell per lokalem LLM formulierter Brief" in document_xml

            manifest = json.loads((tmp_path / "output" / "llm-letters-manifest.json").read_text(encoding="utf-8"))
            assert manifest["letters"][0]["generation_mode"] == "llm"
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_accounts_receivable_preview_endpoint_returns_llm_draft(tmp_path: Path) -> None:
    orders_csv = tmp_path / "orders.csv"
    orders_csv.write_text(
        "\n".join(
            [
                "customer_name,email,address,product,quantity,price_per_unit,total_price,order_date,delivery_date,invoice_due_date,invoice_paid",
                "Alice Example,alice@example.org,Alpha Strasse 1 10115 Berlin,Laptop,1,1200.0,1200.0,2026-03-01T08:00:00,2026-03-02T08:00:00,2026-03-10T08:00:00,0",
                "Cara Example,cara@example.org,Gamma Platz 3 50667 Koeln,Keyboard,2,80.0,160.0,2026-03-11T08:00:00,2026-03-12T08:00:00,2026-03-22T08:00:00,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    orchestrator = create_orchestrator(build_settings(tmp_path))
    app = create_app(orchestrator=orchestrator)

    def fake_llm(prompt: str, settings: Settings, *, timeout_s: int | None = None) -> str:
        assert "Alice Example" in prompt
        assert timeout_s == settings.lit_preview_timeout_s
        return "Dies ist ein lokal generierter Vorschaubrief fuer Alice Example."

    try:
        with patch("nova_synesis.runtime.handlers._generate_local_text", side_effect=fake_llm):
            with TestClient(app) as client:
                response = client.post(
                    "/tools/accounts-receivable/preview-draft",
                    json={
                        "extract_input": {
                            "path": "orders.csv",
                            "source_type": "csv",
                            "as_of": "2026-04-09T00:00:00+00:00",
                        },
                        "generate_input": {
                            "sender_company": "Example Finance",
                            "generation_mode": "llm",
                            "user_instruction": "Bitte freundlich formulieren.",
                            "prompt_template": (
                                "Schreibe einen deutschen Brief an {customer_name}.\n"
                                "Firma: {sender_company}\n"
                                "Anweisung: {user_instruction}\n"
                                "Rechnungen:\n{invoice_lines}"
                            ),
                            "fallback_to_template_on_error": False,
                        },
                        "customer_index": 0,
                    },
                )

        assert response.status_code == 200
        payload = response.json()
        assert payload["customer_name"] == "Alice Example"
        assert payload["generation_mode"] == "llm"
        assert "Schreibe einen deutschen Brief an Alice Example." in payload["prompt"]
        assert "lokal generierter Vorschaubrief" in payload["letter"]
        assert payload["source_summary"]["customer_count"] == 2
    finally:
        asyncio.run(orchestrator.shutdown())


def test_local_llm_text_handler_generates_text_from_instruction_and_data(tmp_path: Path) -> None:
    def fake_llm(prompt: str, settings: Settings, *, timeout_s: int | None = None) -> str:
        assert "Audit the following file for security flaws." in prompt
        assert "const apiKey = process.env.API_KEY;" in prompt
        assert timeout_s == settings.lit_timeout_s
        return "Potential issue: secret handling should avoid direct exposure."

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            with patch("nova_synesis.runtime.handlers._generate_local_text", side_effect=fake_llm):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "audit_code",
                            "handler_name": "local_llm_text",
                            "input": {
                                "instruction": "Audit the following file for security flaws.",
                                "data": "const apiKey = process.env.API_KEY;",
                            },
                        }
                    ]
                )
                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))

            assert snapshot["state"] == "COMPLETED"
            result = snapshot["results"]["audit_code"]
            assert result["text"] == "Potential issue: secret handling should avoid direct exposure."
            assert "Audit the following file for security flaws." in result["prompt"]
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())


def test_local_llm_text_handler_uses_prompt_and_data_without_follow_up_requests(tmp_path: Path) -> None:
    captured_prompt: dict[str, str] = {}

    def fake_llm(prompt: str, settings: Settings, *, timeout_s: int | None = None) -> str:
        captured_prompt["value"] = prompt
        return "Final structured summary."

    async def run() -> None:
        orchestrator = create_orchestrator(build_settings(tmp_path))
        try:
            with patch("nova_synesis.runtime.handlers._generate_local_text", side_effect=fake_llm):
                flow = orchestrator.create_flow(
                    nodes=[
                        {
                            "node_id": "format_report",
                            "handler_name": "local_llm_text",
                            "input": {
                                "prompt": "Please provide the ${vulnerability_scan.result} so I can analyze it and format it.",
                                "data": "Finding A: injection risk in request parser.",
                            },
                        }
                    ]
                )
                snapshot = await orchestrator.run_flow(int(flow["flow_id"]))

            assert snapshot["state"] == "COMPLETED"
            assert snapshot["results"]["format_report"]["text"] == "Final structured summary."
            assert "Use the following input as the complete source material." in captured_prompt["value"]
            assert "Finding A: injection risk in request parser." in captured_prompt["value"]
            assert "Do not ask the user for more data." in captured_prompt["value"]
        finally:
            await orchestrator.shutdown()

    asyncio.run(run())
