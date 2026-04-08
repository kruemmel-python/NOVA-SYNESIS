from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(primary: str, legacy: str, default: str | None = None) -> str | None:
    return os.getenv(primary, os.getenv(legacy, default))


@dataclass(slots=True)
class Settings:
    app_name: str = "NOVA-SYNESIS"
    environment: str = "production"
    log_level: str = "INFO"
    database_path: str = "data/orchestrator.db"
    working_directory: str = "."
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    default_short_term_backend: str = "memory"
    default_long_term_backend: str = "data/long_term_memory.db"
    default_vector_backend: str = "data/vector_memory.db"
    max_flow_concurrency: int = 4
    lit_binary_path: str = "LIT/lit.windows_x86_64.exe"
    lit_model_path: str = "LIT/gemma-4-E2B-it.litertlm"
    lit_backend: str = "cpu"
    lit_timeout_s: int = 240
    security_enabled: bool = True
    security_max_nodes: int = 40
    security_max_edges: int = 160
    security_max_total_attempts: int = 120
    security_max_expression_length: int = 512
    security_max_expression_nodes: int = 64
    security_allow_loopback_hosts: bool = True
    security_http_allowed_hosts: tuple[str, ...] = (
        "127.0.0.1",
        "localhost",
    )
    security_send_message_allowed_protocols: tuple[str, ...] = ("MESSAGE_QUEUE",)
    security_blocked_handler_keywords: tuple[str, ...] = (
        "exploit",
        "phish",
        "credential",
        "scan",
        "bruteforce",
        "exfil",
        "social",
    )
    security_blocked_capability_keywords: tuple[str, ...] = (
        "exploit",
        "phish",
        "credential",
        "scan",
        "bruteforce",
        "exfil",
        "social",
    )
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        cors_origins = _env("NS_CORS_ORIGINS", "AO_CORS_ORIGINS")
        security_http_allowed_hosts = _env(
            "NS_SECURITY_HTTP_ALLOWED_HOSTS",
            "AO_SECURITY_HTTP_ALLOWED_HOSTS",
        )
        security_send_protocols = _env(
            "NS_SECURITY_SEND_PROTOCOLS",
            "AO_SECURITY_SEND_PROTOCOLS",
        )
        blocked_handler_keywords = _env(
            "NS_SECURITY_BLOCKED_HANDLER_KEYWORDS",
            "AO_SECURITY_BLOCKED_HANDLER_KEYWORDS",
        )
        blocked_capability_keywords = _env(
            "NS_SECURITY_BLOCKED_CAPABILITY_KEYWORDS",
            "AO_SECURITY_BLOCKED_CAPABILITY_KEYWORDS",
        )
        return cls(
            app_name=_env("NS_APP_NAME", "AO_APP_NAME", defaults.app_name) or defaults.app_name,
            environment=_env("NS_ENVIRONMENT", "AO_ENVIRONMENT", defaults.environment)
            or defaults.environment,
            log_level=_env("NS_LOG_LEVEL", "AO_LOG_LEVEL", defaults.log_level) or defaults.log_level,
            database_path=_env("NS_DATABASE_PATH", "AO_DATABASE_PATH", defaults.database_path)
            or defaults.database_path,
            working_directory=_env(
                "NS_WORKING_DIRECTORY",
                "AO_WORKING_DIRECTORY",
                defaults.working_directory,
            )
            or defaults.working_directory,
            api_host=_env("NS_API_HOST", "AO_API_HOST", defaults.api_host) or defaults.api_host,
            api_port=int(_env("NS_API_PORT", "AO_API_PORT", str(defaults.api_port)) or defaults.api_port),
            default_short_term_backend=_env(
                "NS_SHORT_TERM_BACKEND",
                "AO_SHORT_TERM_BACKEND",
                defaults.default_short_term_backend,
            )
            or defaults.default_short_term_backend,
            default_long_term_backend=_env(
                "NS_LONG_TERM_BACKEND",
                "AO_LONG_TERM_BACKEND",
                defaults.default_long_term_backend,
            )
            or defaults.default_long_term_backend,
            default_vector_backend=_env(
                "NS_VECTOR_BACKEND",
                "AO_VECTOR_BACKEND",
                defaults.default_vector_backend,
            )
            or defaults.default_vector_backend,
            max_flow_concurrency=int(
                _env(
                    "NS_MAX_FLOW_CONCURRENCY",
                    "AO_MAX_FLOW_CONCURRENCY",
                    str(defaults.max_flow_concurrency),
                )
                or defaults.max_flow_concurrency
            ),
            lit_binary_path=_env("NS_LIT_BINARY_PATH", "AO_LIT_BINARY_PATH", defaults.lit_binary_path)
            or defaults.lit_binary_path,
            lit_model_path=_env("NS_LIT_MODEL_PATH", "AO_LIT_MODEL_PATH", defaults.lit_model_path)
            or defaults.lit_model_path,
            lit_backend=_env("NS_LIT_BACKEND", "AO_LIT_BACKEND", defaults.lit_backend)
            or defaults.lit_backend,
            lit_timeout_s=int(
                _env("NS_LIT_TIMEOUT_S", "AO_LIT_TIMEOUT_S", str(defaults.lit_timeout_s))
                or defaults.lit_timeout_s
            ),
            security_enabled=(
                _env("NS_SECURITY_ENABLED", "AO_SECURITY_ENABLED", str(defaults.security_enabled))
                or str(defaults.security_enabled)
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            security_max_nodes=int(
                _env("NS_SECURITY_MAX_NODES", "AO_SECURITY_MAX_NODES", str(defaults.security_max_nodes))
                or defaults.security_max_nodes
            ),
            security_max_edges=int(
                _env("NS_SECURITY_MAX_EDGES", "AO_SECURITY_MAX_EDGES", str(defaults.security_max_edges))
                or defaults.security_max_edges
            ),
            security_max_total_attempts=int(
                _env(
                    "NS_SECURITY_MAX_TOTAL_ATTEMPTS",
                    "AO_SECURITY_MAX_TOTAL_ATTEMPTS",
                    str(defaults.security_max_total_attempts),
                )
                or defaults.security_max_total_attempts
            ),
            security_max_expression_length=int(
                _env(
                    "NS_SECURITY_MAX_EXPRESSION_LENGTH",
                    "AO_SECURITY_MAX_EXPRESSION_LENGTH",
                    str(defaults.security_max_expression_length),
                )
                or defaults.security_max_expression_length
            ),
            security_max_expression_nodes=int(
                _env(
                    "NS_SECURITY_MAX_EXPRESSION_NODES",
                    "AO_SECURITY_MAX_EXPRESSION_NODES",
                    str(defaults.security_max_expression_nodes),
                )
                or defaults.security_max_expression_nodes
            ),
            security_allow_loopback_hosts=(
                _env(
                    "NS_SECURITY_ALLOW_LOOPBACK_HOSTS",
                    "AO_SECURITY_ALLOW_LOOPBACK_HOSTS",
                    str(defaults.security_allow_loopback_hosts),
                )
                or str(defaults.security_allow_loopback_hosts)
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            security_http_allowed_hosts=(
                tuple(host.strip() for host in security_http_allowed_hosts.split(",") if host.strip())
                if security_http_allowed_hosts
                else defaults.security_http_allowed_hosts
            ),
            security_send_message_allowed_protocols=(
                tuple(protocol.strip() for protocol in security_send_protocols.split(",") if protocol.strip())
                if security_send_protocols
                else defaults.security_send_message_allowed_protocols
            ),
            security_blocked_handler_keywords=(
                tuple(keyword.strip() for keyword in blocked_handler_keywords.split(",") if keyword.strip())
                if blocked_handler_keywords
                else defaults.security_blocked_handler_keywords
            ),
            security_blocked_capability_keywords=(
                tuple(keyword.strip() for keyword in blocked_capability_keywords.split(",") if keyword.strip())
                if blocked_capability_keywords
                else defaults.security_blocked_capability_keywords
            ),
            cors_origins=(
                tuple(origin.strip() for origin in cors_origins.split(",") if origin.strip())
                if cors_origins
                else defaults.cors_origins
            ),
        )

    def ensure_directories(self) -> None:
        for candidate in (
            Path(self.database_path).parent,
            Path(self.default_long_term_backend).parent,
            Path(self.default_vector_backend).parent,
            Path(self.working_directory),
        ):
            candidate.mkdir(parents=True, exist_ok=True)
