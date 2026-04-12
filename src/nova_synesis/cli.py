from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import uvicorn

from nova_synesis.api.app import create_app
from nova_synesis.config import Settings
from nova_synesis.services.orchestrator import create_orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOVA-SYNESIS CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_api = subparsers.add_parser("run-api", help="Start the FastAPI service")
    run_api.add_argument("--host", default=None)
    run_api.add_argument("--port", type=int, default=None)
    run_api.add_argument("--db-path", default=None)
    run_api.add_argument("--workdir", default=None)
    run_api.add_argument("--lit-model", default=None)
    run_api.add_argument("--lit-binary", default=None)
    run_api.add_argument("--lit-backend", default=None)

    execute_intent = subparsers.add_parser("execute-intent", help="Plan and execute an intent from JSON")
    execute_intent.add_argument("--file", required=True)
    execute_intent.add_argument("--db-path", default=None)
    execute_intent.add_argument("--workdir", default=None)
    execute_intent.add_argument("--lit-model", default=None)
    execute_intent.add_argument("--lit-binary", default=None)
    execute_intent.add_argument("--lit-backend", default=None)

    create_flow = subparsers.add_parser("run-flow-spec", help="Create and execute a flow from JSON")
    create_flow.add_argument("--file", required=True)
    create_flow.add_argument("--db-path", default=None)
    create_flow.add_argument("--workdir", default=None)
    create_flow.add_argument("--lit-model", default=None)
    create_flow.add_argument("--lit-binary", default=None)
    create_flow.add_argument("--lit-backend", default=None)

    return parser


def _resolve_lit_cli_path(raw_value: str, *, workdir: str) -> str:
    raw_text = raw_value.strip()
    if not raw_text:
        return raw_text
    candidate = Path(raw_text)
    if candidate.is_absolute():
        return str(candidate)
    if candidate.parent == Path("."):
        lit_dir_candidate = Path(workdir) / "LIT" / candidate.name
        if lit_dir_candidate.exists():
            return str(lit_dir_candidate)
    return str((Path(workdir) / candidate).resolve())


def _build_settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env()
    if args.db_path:
        settings.database_path = args.db_path
    if args.workdir:
        settings.working_directory = args.workdir
    if getattr(args, "lit_model", None):
        settings.lit_model_path = _resolve_lit_cli_path(args.lit_model, workdir=settings.working_directory)
    if getattr(args, "lit_binary", None):
        settings.lit_binary_path = _resolve_lit_cli_path(args.lit_binary, workdir=settings.working_directory)
    if getattr(args, "lit_backend", None):
        settings.lit_backend = str(args.lit_backend).strip() or settings.lit_backend
    settings.ensure_directories()
    return settings


async def _execute_intent_from_file(file_path: str, settings: Settings) -> dict[str, Any]:
    orchestrator = create_orchestrator(settings)
    payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    try:
        return await orchestrator.execute_intent(
            goal=payload["goal"],
            constraints=payload.get("constraints", {}),
            priority=int(payload.get("priority", 1)),
        )
    finally:
        await orchestrator.shutdown()


async def _run_flow_spec_from_file(file_path: str, settings: Settings) -> dict[str, Any]:
    orchestrator = create_orchestrator(settings)
    payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    try:
        flow = orchestrator.create_flow(
            nodes=payload["nodes"],
            edges=payload.get("edges", []),
            metadata=payload.get("metadata", {}),
        )
        return await orchestrator.run_flow(int(flow["flow_id"]))
    finally:
        await orchestrator.shutdown()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run-api":
        settings = _build_settings(args)
        if args.host:
            settings.api_host = args.host
        if args.port:
            settings.api_port = args.port
        app = create_app(settings=settings)
        uvicorn.run(app, host=settings.api_host, port=settings.api_port)
        return

    if args.command == "execute-intent":
        settings = _build_settings(args)
        result = asyncio.run(_execute_intent_from_file(args.file, settings))
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    if args.command == "run-flow-spec":
        settings = _build_settings(args)
        result = asyncio.run(_run_flow_spec_from_file(args.file, settings))
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    parser.error(f"Unknown command '{args.command}'")


if __name__ == "__main__":
    main()
