from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from nova_synesis.config import Settings

HandlerCallable = Callable[..., Any]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass(slots=True)
class HandlerCertificate:
    handler_name: str
    fingerprint: str
    module_name: str
    qualname: str
    issuer: str
    issued_at: datetime
    expires_at: datetime
    built_in: bool
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "handler_name": self.handler_name,
            "fingerprint": self.fingerprint,
            "module_name": self.module_name,
            "qualname": self.qualname,
            "issuer": self.issuer,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "built_in": self.built_in,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandlerCertificate":
        issued_at = _parse_timestamp(str(payload.get("issued_at", "")))
        expires_at = _parse_timestamp(str(payload.get("expires_at", "")))
        if issued_at is None or expires_at is None:
            raise ValueError("Handler certificate contains invalid timestamps")
        return cls(
            handler_name=str(payload["handler_name"]),
            fingerprint=str(payload["fingerprint"]),
            module_name=str(payload["module_name"]),
            qualname=str(payload["qualname"]),
            issuer=str(payload["issuer"]),
            issued_at=issued_at,
            expires_at=expires_at,
            built_in=bool(payload.get("built_in", False)),
            signature=str(payload["signature"]),
        )


@dataclass(slots=True)
class HandlerTrustRecord:
    name: str
    module_name: str
    qualname: str
    fingerprint: str
    trusted: bool
    built_in: bool
    trust_reason: str
    certificate: HandlerCertificate | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "module_name": self.module_name,
            "qualname": self.qualname,
            "fingerprint": self.fingerprint,
            "trusted": self.trusted,
            "built_in": self.built_in,
            "trust_reason": self.trust_reason,
            "certificate": self.certificate.as_dict() if self.certificate else None,
        }


class HandlerTrustAuthority:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._secret = settings.handler_certificate_secret.encode("utf-8")

    def fingerprint_handler(self, name: str, handler: HandlerCallable) -> str:
        module_name = getattr(handler, "__module__", "__unknown__")
        qualname = getattr(handler, "__qualname__", getattr(handler, "__name__", name))
        material = [name, module_name, qualname]
        try:
            material.append(inspect.getsource(handler))
        except (OSError, TypeError):
            code_object = getattr(handler, "__code__", None)
            if code_object is not None:
                material.append(code_object.co_code.hex())
                material.append(repr(code_object.co_consts))
            else:
                material.append(repr(handler))
        digest = hashlib.sha256("\n".join(material).encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def issue_certificate(
        self,
        name: str,
        handler: HandlerCallable,
        *,
        built_in: bool = False,
        expires_in_hours: int | None = None,
    ) -> HandlerCertificate:
        module_name = getattr(handler, "__module__", "__unknown__")
        qualname = getattr(handler, "__qualname__", getattr(handler, "__name__", name))
        issued_at = _utcnow()
        ttl_hours = expires_in_hours or self.settings.handler_certificate_ttl_hours
        certificate = HandlerCertificate(
            handler_name=name,
            fingerprint=self.fingerprint_handler(name, handler),
            module_name=module_name,
            qualname=qualname,
            issuer=self.settings.handler_certificate_issuer,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(hours=max(1, int(ttl_hours))),
            built_in=built_in,
            signature="",
        )
        certificate.signature = self._sign_payload(certificate.payload())
        return certificate

    def validate_certificate(
        self,
        name: str,
        handler: HandlerCallable,
        raw_certificate: HandlerCertificate | dict[str, Any] | None,
    ) -> tuple[bool, str, HandlerCertificate | None]:
        if raw_certificate is None:
            return False, "Handler has no digital trust certificate", None

        certificate = (
            raw_certificate
            if isinstance(raw_certificate, HandlerCertificate)
            else HandlerCertificate.from_dict(dict(raw_certificate))
        )
        if certificate.handler_name != name:
            return False, "Handler certificate does not match the registered handler name", certificate

        expected_signature = self._sign_payload(certificate.payload())
        if not hmac.compare_digest(expected_signature, certificate.signature):
            return False, "Handler certificate signature is invalid", certificate

        if certificate.expires_at <= _utcnow():
            return False, "Handler certificate has expired", certificate

        expected_fingerprint = self.fingerprint_handler(name, handler)
        if certificate.fingerprint != expected_fingerprint:
            return False, "Handler certificate fingerprint does not match the current handler code", certificate

        module_name = getattr(handler, "__module__", "__unknown__")
        qualname = getattr(handler, "__qualname__", getattr(handler, "__name__", name))
        if certificate.module_name != module_name or certificate.qualname != qualname:
            return False, "Handler certificate does not match the current handler identity", certificate

        return True, f"Valid handler certificate issued by {certificate.issuer}", certificate

    def _sign_payload(self, payload: dict[str, Any]) -> str:
        message = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        digest = hmac.new(self._secret, message, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
