from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

from nova_synesis.config import Settings
from nova_synesis.domain.models import ResourceType
from nova_synesis.security import HandlerCertificate, HandlerTrustAuthority, HandlerTrustRecord

HandlerCallable = Callable[[dict[str, Any]], Any | Awaitable[Any]]


class TaskHandlerRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._trust_authority = HandlerTrustAuthority(self._settings)
        self._handlers: dict[str, HandlerCallable] = {}
        self._handler_records: dict[str, HandlerTrustRecord] = {}

    def register(
        self,
        name: str,
        handler: HandlerCallable,
        *,
        certificate: HandlerCertificate | dict[str, Any] | None = None,
        built_in: bool = False,
    ) -> HandlerCallable:
        trusted = False
        trust_reason = "Handler has no digital trust certificate"
        validated_certificate: HandlerCertificate | None = None

        if certificate is not None:
            trusted, trust_reason, validated_certificate = self._trust_authority.validate_certificate(
                name=name,
                handler=handler,
                raw_certificate=certificate,
            )
        elif built_in and self._settings.security_auto_issue_builtin_handler_certificates:
            validated_certificate = self._trust_authority.issue_certificate(
                name=name,
                handler=handler,
                built_in=True,
            )
            trusted = True
            trust_reason = f"Built-in handler certificate issued by {validated_certificate.issuer}"

        module_name = getattr(handler, "__module__", "__unknown__")
        qualname = getattr(handler, "__qualname__", getattr(handler, "__name__", name))
        self._handler_records[name] = HandlerTrustRecord(
            name=name,
            module_name=module_name,
            qualname=qualname,
            fingerprint=self._trust_authority.fingerprint_handler(name, handler),
            trusted=trusted,
            built_in=built_in,
            trust_reason=trust_reason,
            certificate=validated_certificate,
        )
        self._handlers[name] = handler
        return handler

    def get(self, name: str) -> HandlerCallable:
        if name not in self._handlers:
            raise KeyError(f"Unknown task handler '{name}'")
        return self._handlers[name]

    def get_record(self, name: str) -> HandlerTrustRecord:
        if name not in self._handler_records:
            raise KeyError(f"Unknown task handler '{name}'")
        return self._handler_records[name]

    def names(self, trusted_only: bool = False) -> list[str]:
        if not trusted_only:
            return sorted(self._handlers.keys())
        return sorted(
            record.name for record in self._handler_records.values() if record.trusted
        )

    def describe(self) -> list[dict[str, Any]]:
        return [record.as_dict() for record in sorted(self._handler_records.values(), key=lambda item: item.name)]

    def issue_certificate(self, name: str, *, expires_in_hours: int | None = None) -> dict[str, Any]:
        handler = self.get(name)
        certificate = self._trust_authority.issue_certificate(
            name=name,
            handler=handler,
            built_in=self.get_record(name).built_in,
            expires_in_hours=expires_in_hours,
        )
        self._handler_records[name] = HandlerTrustRecord(
            name=name,
            module_name=getattr(handler, "__module__", "__unknown__"),
            qualname=getattr(handler, "__qualname__", getattr(handler, "__name__", name)),
            fingerprint=self._trust_authority.fingerprint_handler(name, handler),
            trusted=True,
            built_in=self.get_record(name).built_in,
            trust_reason=f"Valid handler certificate issued by {certificate.issuer}",
            certificate=certificate,
        )
        return certificate.as_dict()

    async def execute(self, name: str, context: dict[str, Any]) -> Any:
        handler = self.get(name)
        result = handler(context)
        if inspect.isawaitable(result):
            return await result
        return result


def _resolve_working_path(
    working_directory: Path,
    raw_path: str,
    allow_outside_workdir: bool = False,
) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (working_directory / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if allow_outside_workdir:
        return candidate

    base = working_directory.resolve()
    if base == candidate or base in candidate.parents:
        return candidate
    raise ValueError(f"Path '{candidate}' is outside the allowed working directory")


def _primary_resource_endpoint(context: dict[str, Any], resource_type: ResourceType | None = None) -> str | None:
    for resource in context.get("resources", []):
        if resource_type is None or resource.type == resource_type:
            return resource.endpoint
    return None


async def http_request_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    url = payload.get("url") or _primary_resource_endpoint(context, ResourceType.API)
    if not url:
        raise ValueError("http_request requires a URL or an API resource")
    method = str(payload.get("method", "GET")).upper()
    timeout_s = float(payload.get("timeout_s", 10.0))
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.request(
            method,
            url,
            headers=payload.get("headers"),
            params=payload.get("params"),
            json=payload.get("json"),
            data=payload.get("data"),
        )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
    }


async def memory_store_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    return await context["memory_manager"].store(
        memory_id=str(payload["memory_id"]),
        key=str(payload["key"]),
        value=payload["value"],
    )


async def memory_retrieve_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    value = await context["memory_manager"].retrieve(
        memory_id=str(payload["memory_id"]),
        key=str(payload["key"]),
    )
    return {"memory_id": payload["memory_id"], "key": payload["key"], "value": value}


async def memory_search_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    matches = await context["memory_manager"].search(
        memory_id=str(payload["memory_id"]),
        query=payload["query"],
        limit=int(payload.get("limit", 5)),
    )
    return {"memory_id": payload["memory_id"], "matches": matches}


async def send_message_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    sender = context.get("agent")
    agents = context["agents"]
    target_agent = None
    target_agent_id = payload.get("target_agent_id")
    if target_agent_id is not None:
        target_agent = agents[int(target_agent_id)]

    message = payload.get("message", payload)
    if isinstance(message, dict) and target_agent is not None and target_agent.comms is not None:
        message.setdefault("target_endpoint", target_agent.comms.endpoint)

    if sender is not None and sender.comms is not None:
        envelope = {
            "source_agent_id": sender.agent_id,
            "target": target_agent_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if target_agent is not None and target_agent.comms is not None:
            envelope["target_endpoint"] = target_agent.comms.endpoint
        receipt = await sender.comms.send(envelope)
    elif target_agent is not None and target_agent.comms is not None:
        receipt = await target_agent.comms.send(message)
    else:
        raise ValueError("send_message requires either a sender with comms or a target agent with comms")

    return {"delivered": True, "receipt": receipt}


async def resource_health_check_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    resource_ids = payload.get("resource_ids")
    if resource_ids:
        resources = [context["resource_manager"].get(int(resource_id)) for resource_id in resource_ids]
        report = []
        for resource in resources:
            report.append(
                {
                    "resource_id": resource.resource_id,
                    "healthy": await resource.health_check(),
                    "state": resource.state.value,
                }
            )
        return {"resources": report}
    return {"resources": await context["resource_manager"].health_report()}


def template_render_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    template = str(payload["template"])
    values = payload.get("values", {})
    return {"rendered": template.format_map(values)}


def merge_payloads_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    base = dict(payload.get("base", {}))
    for update in payload.get("updates", []):
        if not isinstance(update, dict):
            raise ValueError("merge_payloads expects all updates to be dictionaries")
        base.update(update)
    return base


def read_file_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    working_directory = Path(context["working_directory"])
    path = _resolve_working_path(
        working_directory=working_directory,
        raw_path=str(payload["path"]),
        allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
    )
    encoding = payload.get("encoding", "utf-8")
    return {"path": str(path), "content": path.read_text(encoding=encoding)}


def write_file_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    working_directory = Path(context["working_directory"])
    path = _resolve_working_path(
        working_directory=working_directory,
        raw_path=str(payload["path"]),
        allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    encoding = payload.get("encoding", "utf-8")
    content = payload.get("content", "")
    mode = "a" if payload.get("append", False) else "w"
    with path.open(mode, encoding=encoding) as file_handle:
        file_handle.write(content)
    return {"path": str(path), "written": True, "bytes": len(content.encode(encoding))}


def json_serialize_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    return {"json": json.dumps(payload["value"], ensure_ascii=False, indent=payload.get("indent", 2))}


def register_default_handlers(registry: TaskHandlerRegistry) -> None:
    registry.register("http_request", http_request_handler, built_in=True)
    registry.register("memory_store", memory_store_handler, built_in=True)
    registry.register("memory_retrieve", memory_retrieve_handler, built_in=True)
    registry.register("memory_search", memory_search_handler, built_in=True)
    registry.register("send_message", send_message_handler, built_in=True)
    registry.register("resource_health_check", resource_health_check_handler, built_in=True)
    registry.register("template_render", template_render_handler, built_in=True)
    registry.register("merge_payloads", merge_payloads_handler, built_in=True)
    registry.register("read_file", read_file_handler, built_in=True)
    registry.register("write_file", write_file_handler, built_in=True)
    registry.register("json_serialize", json_serialize_handler, built_in=True)
