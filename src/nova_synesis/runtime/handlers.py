from __future__ import annotations

import csv
import inspect
import json
import re
import sqlite3
import unicodedata
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlencode
from xml.etree import ElementTree
from xml.sax.saxutils import escape as xml_escape

import httpx

from nova_synesis.config import Settings
from nova_synesis.domain.models import HumanInputRequest, ResourceType
from nova_synesis.planning.lit_planner import LiteRTPlanner
from nova_synesis.security import HandlerCertificate, HandlerTrustAuthority, HandlerTrustRecord

HandlerCallable = Callable[[dict[str, Any]], Any | Awaitable[Any]]

DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION = (
    "Formuliere ein professionelles, freundliches und bestimmtes Anschreiben in deutscher Sprache. "
    "Schreibe klar, aber nicht aggressiv. Verwende keine Markdown-Formatierung, keine Aufzaehlungszeichen "
    "im Fliesstext ausser bei Rechnungslisten und keine Platzhalter."
)

DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE = """Du bist ein erfahrener Sachbearbeiter im Forderungsmanagement eines Unternehmens.
Verfasse ein finales deutsches Anschreiben zur Zahlungserinnerung.

Unternehmensdaten:
- Firma: {sender_company}
- Adresse: {sender_address}
- E-Mail: {sender_email}
- Telefon: {sender_phone}

Kundendaten:
- Name: {customer_name}
- Adresse: {customer_address}
- E-Mail: {customer_email}

Fachliche Daten:
- Stichtag: {as_of_date}
- Zahlungsfrist bis: {settle_by_date}
- Anzahl offener Rechnungen: {invoice_count}
- Anzahl ueberfaelliger Rechnungen: {overdue_invoice_count}
- Maximal ueberfaellig seit Tagen: {max_days_overdue}
- Offener Gesamtbetrag: {total_outstanding}

Offene Rechnungen:
{invoice_lines}

Zusaetzliche Schreibanweisung:
{user_instruction}

Anforderungen:
- Gib nur den finalen Brieftext zurueck.
- Keine Markdown-Codeblocks.
- Keine JSON-Ausgabe.
- Kein Begleitkommentar vor oder nach dem Brief.
- Der Brief muss direkt versandfaehig sein.
"""

DEFAULT_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "robotik": [
        "robotik",
        "robotics",
        "roboter",
        "robot",
        "humanoid",
        "autonomer roboter",
        "automation",
        "automatisierung",
    ],
    "ki": [
        "ki",
        "ai",
        "artificial intelligence",
        "artificial-intelligence",
        "kuenstliche intelligenz",
        "künstliche intelligenz",
        "llm",
        "foundation model",
        "generative ai",
        "machine learning",
    ],
}


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


class HumanInputRequiredError(RuntimeError):
    def __init__(self, request: HumanInputRequest) -> None:
        super().__init__(request.title)
        self.request = request


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


def _parse_iso_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) != 0
    text = str(value).strip().casefold()
    return text in {"1", "true", "yes", "ja", "y"}


def _parse_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    return float(text or 0.0)


def _format_currency(amount: float) -> str:
    formatted = f"{amount:,.2f}"
    return f"{formatted.replace(',', 'X').replace('.', ',').replace('X', '.')} EUR"


def _ascii_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")


def _with_extension(file_name: str, extension: str) -> str:
    suffix = extension if extension.startswith(".") else f".{extension}"
    if Path(file_name).suffix.casefold() == suffix.casefold():
        return file_name
    return f"{Path(file_name).stem}{suffix}"


def _invoice_summary_lines(customer: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for invoice in customer.get("invoices", []):
        due_on = invoice.get("invoice_due_date", "") or "unbekannt"
        due_label = due_on.split("T", 1)[0] if isinstance(due_on, str) else str(due_on)
        lines.append(
            "- Rechnung {invoice_ref}: {product}, Faelligkeit {due_date}, Betrag {amount}, Status {status}".format(
                invoice_ref=invoice["invoice_ref"],
                product=invoice["product"] or "Leistung",
                due_date=due_label,
                amount=_format_currency(invoice["total_price"]),
                status=invoice["status"],
            )
        )
    return lines


def _render_receivable_template_letter(
    *,
    customer: dict[str, Any],
    sender_company: str,
    sender_email: str,
    sender_phone: str,
    sender_address: str,
    due_date_text: str,
    settle_by_text: str,
) -> str:
    customer_name = str(customer.get("customer_name", "")).strip()
    email = str(customer.get("email", "")).strip()
    address = str(customer.get("address", "")).strip()
    lines = _invoice_summary_lines(customer)
    return "\n".join(
        [
            sender_company,
            sender_address,
            f"E-Mail: {sender_email}",
            f"Telefon: {sender_phone}",
            "",
            due_date_text,
            "",
            customer_name,
            address,
            f"E-Mail: {email}",
            "",
            "Betreff: Zahlungserinnerung zu offenen Forderungen",
            "",
            f"Sehr geehrte Damen und Herren,",
            "",
            "bei der Durchsicht unserer offenen Posten ist aufgefallen, dass die folgenden Rechnungen noch nicht ausgeglichen wurden:",
            *lines,
            "",
            f"Der aktuell offene Gesamtbetrag betraegt {_format_currency(customer['total_outstanding'])}.",
            f"Bitte gleichen Sie den Betrag bis spaetestens {settle_by_text} aus oder melden Sie sich kurzfristig bei unserer Buchhaltung, falls Rueckfragen bestehen.",
            "",
            "Sollte die Zahlung zwischenzeitlich bereits erfolgt sein, betrachten Sie dieses Schreiben bitte als gegenstandslos.",
            "",
            "Mit freundlichen Gruessen",
            sender_company,
        ]
    )


def _render_receivable_llm_prompt(
    *,
    prompt_template: str,
    user_instruction: str,
    customer: dict[str, Any],
    sender_company: str,
    sender_email: str,
    sender_phone: str,
    sender_address: str,
    due_date_text: str,
    settle_by_text: str,
) -> str:
    invoice_lines = "\n".join(_invoice_summary_lines(customer))
    prompt_variables = {
        "sender_company": sender_company,
        "sender_email": sender_email,
        "sender_phone": sender_phone,
        "sender_address": sender_address,
        "customer_name": str(customer.get("customer_name", "")).strip(),
        "customer_email": str(customer.get("email", "")).strip(),
        "customer_address": str(customer.get("address", "")).strip(),
        "invoice_count": int(customer.get("invoice_count", 0)),
        "overdue_invoice_count": int(customer.get("overdue_invoice_count", 0)),
        "max_days_overdue": int(customer.get("max_days_overdue", 0)),
        "total_outstanding": _format_currency(float(customer.get("total_outstanding", 0.0))),
        "currency": str(customer.get("currency", "EUR")),
        "as_of_date": due_date_text,
        "settle_by_date": settle_by_text,
        "invoice_lines": invoice_lines,
        "invoices_json": json.dumps(customer.get("invoices", []), ensure_ascii=False, indent=2),
        "customer_json": json.dumps(customer, ensure_ascii=False, indent=2),
        "user_instruction": user_instruction,
    }
    try:
        return prompt_template.format_map(prompt_variables)
    except KeyError as exc:
        missing_key = str(exc).strip("'")
        raise ValueError(
            f"accounts_receivable_generate_letters prompt_template references unknown placeholder '{missing_key}'"
        ) from exc


def _sanitize_llm_letter_output(raw_text: str) -> str:
    normalized = raw_text.strip()
    if normalized.startswith("```"):
        fenced = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", normalized)
        normalized = re.sub(r"\s*```$", "", fenced).strip()
    return normalized


def _generate_local_text(prompt: str, settings: Settings, *, timeout_s: int | None = None) -> str:
    planner = LiteRTPlanner(settings)
    return planner.generate_text(prompt, timeout_s=timeout_s)


def _draft_receivable_letter(
    *,
    customer: dict[str, Any],
    sender_company: str,
    sender_email: str,
    sender_phone: str,
    sender_address: str,
    due_date_text: str,
    settle_by_text: str,
    use_local_llm: bool,
    settings: Settings | None,
    prompt_template: str,
    user_instruction: str,
    fallback_to_template_on_error: bool,
    customer_label: str,
    llm_timeout_s: int | None = None,
) -> dict[str, Any]:
    body = _render_receivable_template_letter(
        customer=customer,
        sender_company=sender_company,
        sender_email=sender_email,
        sender_phone=sender_phone,
        sender_address=sender_address,
        due_date_text=due_date_text,
        settle_by_text=settle_by_text,
    )
    llm_prompt: str | None = None
    actual_generation_mode = "template"
    warnings: list[str] = []

    if use_local_llm:
        if settings is None:
            raise ValueError("Local LLM drafting requires runtime settings")
        llm_prompt = _render_receivable_llm_prompt(
            prompt_template=prompt_template,
            user_instruction=user_instruction,
            customer=customer,
            sender_company=sender_company,
            sender_email=sender_email,
            sender_phone=sender_phone,
            sender_address=sender_address,
            due_date_text=due_date_text,
            settle_by_text=settle_by_text,
        )
        try:
            body = _sanitize_llm_letter_output(
                _generate_local_text(llm_prompt, settings, timeout_s=llm_timeout_s)
            )
            if not body:
                raise ValueError("local LLM returned an empty letter")
            actual_generation_mode = "llm"
        except Exception as exc:
            if not fallback_to_template_on_error:
                raise
            warnings.append(
                f"Customer '{customer_label}': local LLM drafting failed and fell back to template ({exc})"
            )
            actual_generation_mode = "template_fallback"

    return {
        "content": body,
        "prompt": llm_prompt,
        "generation_mode": actual_generation_mode,
        "warnings": warnings,
    }


def preview_accounts_receivable_letter_draft(
    *,
    settings: Settings,
    working_directory: Path,
    extract_input: dict[str, Any],
    generate_input: dict[str, Any],
    customer_index: int = 0,
) -> dict[str, Any]:
    receivables = accounts_receivable_extract_handler(
        {
            "input": dict(extract_input),
            "working_directory": working_directory,
        }
    )
    customers = list(receivables.get("customers", []))
    if not customers:
        raise ValueError("No open receivables available for preview")
    if customer_index < 0 or customer_index >= len(customers):
        raise ValueError(
            f"Preview customer_index '{customer_index}' is outside the available range 0..{len(customers) - 1}"
        )

    payload = dict(generate_input)
    sender_company = str(payload.get("sender_company", "NOVA-SYNESIS Forderungsmanagement")).strip()
    sender_email = str(payload.get("sender_email", "buchhaltung@example.invalid")).strip()
    sender_phone = str(payload.get("sender_phone", "+49 000 000000")).strip()
    sender_address = str(payload.get("sender_address", "Musterstrasse 1, 10115 Berlin")).strip()
    payment_deadline_days = int(payload.get("payment_deadline_days", 7))
    generation_mode = str(payload.get("generation_mode", "template")).strip().casefold() or "template"
    use_local_llm = generation_mode in {"llm", "local_llm", "lit"}
    prompt_template = str(payload.get("prompt_template", DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE))
    user_instruction = str(
        payload.get("user_instruction", DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION)
    ).strip() or DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION
    fallback_to_template_on_error = bool(payload.get("fallback_to_template_on_error", True))
    as_of = _parse_iso_datetime(receivables.get("as_of")) or datetime.now(timezone.utc)
    due_date_text = as_of.date().isoformat()
    settle_by_text = (as_of.date() + timedelta(days=payment_deadline_days)).isoformat()
    customer = customers[customer_index]
    customer_name = str(customer.get("customer_name", "")).strip() or f"customer-{customer_index:04d}"

    drafted = _draft_receivable_letter(
        customer=customer,
        sender_company=sender_company,
        sender_email=sender_email,
        sender_phone=sender_phone,
        sender_address=sender_address,
        due_date_text=due_date_text,
        settle_by_text=settle_by_text,
        use_local_llm=use_local_llm,
        settings=settings,
        prompt_template=prompt_template,
        user_instruction=user_instruction,
        fallback_to_template_on_error=fallback_to_template_on_error,
        customer_label=customer_name,
        llm_timeout_s=settings.lit_preview_timeout_s,
    )

    return {
        "customer_index": customer_index,
        "customer_name": customer_name,
        "customer_id": customer.get("customer_id"),
        "generation_mode": drafted["generation_mode"],
        "prompt": drafted["prompt"],
        "letter": drafted["content"],
        "warnings": drafted["warnings"],
        "source_summary": {
            "customer_count": receivables.get("customer_count", 0),
            "invoice_count": receivables.get("invoice_count", 0),
            "overdue_count": receivables.get("overdue_count", 0),
            "total_outstanding": receivables.get("total_outstanding", 0.0),
            "currency": receivables.get("currency", "EUR"),
            "source_type": receivables.get("source_type"),
            "source_path": receivables.get("source_path"),
        },
        "llm": {
            "enabled": use_local_llm,
            "model_path": settings.lit_model_path if use_local_llm else None,
            "backend": settings.lit_backend if use_local_llm else None,
            "fallback_to_template_on_error": fallback_to_template_on_error,
        },
        "customer": customer,
    }


def _build_docx_document_xml(content: str) -> str:
    paragraphs = []
    for raw_line in content.splitlines():
        text = xml_escape(raw_line)
        paragraphs.append(
            "<w:p><w:r><w:t xml:space=\"preserve\">"
            f"{text}"
            "</w:t></w:r></w:p>"
        )
    if not paragraphs:
        paragraphs.append("<w:p/>")

    body = "".join(paragraphs)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"[http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas](http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas)\" "
        "xmlns:mc=\"[http://schemas.openxmlformats.org/markup-compatibility/2006](http://schemas.openxmlformats.org/markup-compatibility/2006)\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"[http://schemas.openxmlformats.org/officeDocument/2006/relationships](http://schemas.openxmlformats.org/officeDocument/2006/relationships)\" "
        "xmlns:m=\"[http://schemas.openxmlformats.org/officeDocument/2006/math](http://schemas.openxmlformats.org/officeDocument/2006/math)\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"[http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing](http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing)\" "
        "xmlns:wp=\"[http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing](http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing)\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"[http://schemas.openxmlformats.org/wordprocessingml/2006/main](http://schemas.openxmlformats.org/wordprocessingml/2006/main)\" "
        "xmlns:w14=\"[http://schemas.microsoft.com/office/word/2010/wordml](http://schemas.microsoft.com/office/word/2010/wordml)\" "
        "xmlns:wpg=\"[http://schemas.microsoft.com/office/word/2010/wordprocessingGroup](http://schemas.microsoft.com/office/word/2010/wordprocessingGroup)\" "
        "xmlns:wpi=\"[http://schemas.microsoft.com/office/word/2010/wordprocessingInk](http://schemas.microsoft.com/office/word/2010/wordprocessingInk)\" "
        "xmlns:wne=\"[http://schemas.microsoft.com/office/word/2006/wordml](http://schemas.microsoft.com/office/word/2006/wordml)\" "
        "xmlns:wps=\"[http://schemas.microsoft.com/office/word/2010/wordprocessingShape](http://schemas.microsoft.com/office/word/2010/wordprocessingShape)\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{body}"
        "<w:sectPr>"
        "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1134\" w:right=\"1134\" w:bottom=\"1134\" w:left=\"1134\" "
        "w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "</w:sectPr>"
        "</w:body></w:document>"
    )


def _write_simple_docx(path: Path, *, content: str, title: str) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    core_title = xml_escape(title)
    core_created = xml_escape(created_at)
    document_xml = _build_docx_document_xml(content)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Types xmlns=\"[http://schemas.openxmlformats.org/package/2006/content-types](http://schemas.openxmlformats.org/package/2006/content-types)\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/word/document.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
            "<Override PartName=\"/docProps/core.xml\" "
            "ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
            "<Override PartName=\"/docProps/app.xml\" "
            "ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"[http://schemas.openxmlformats.org/package/2006/relationships](http://schemas.openxmlformats.org/package/2006/relationships)\">"
            "<Relationship Id=\"rId1\" "
            "Type=\"[http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument](http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument)\" "
            "Target=\"word/document.xml\"/>"
            "<Relationship Id=\"rId2\" "
            "Type=\"[http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties](http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties)\" "
            "Target=\"docProps/core.xml\"/>"
            "<Relationship Id=\"rId3\" "
            "Type=\"[http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties](http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties)\" "
            "Target=\"docProps/app.xml\"/>"
            "</Relationships>",
        )
        archive.writestr(
            "docProps/core.xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<cp:coreProperties xmlns:cp=\"[http://schemas.openxmlformats.org/package/2006/metadata/core-properties](http://schemas.openxmlformats.org/package/2006/metadata/core-properties)\" "
            "xmlns:dc=\"[http://purl.org/dc/elements/1.1/](http://purl.org/dc/elements/1.1/)\" "
            "xmlns:dcterms=\"[http://purl.org/dc/terms/](http://purl.org/dc/terms/)\" "
            "xmlns:dcmitype=\"[http://purl.org/dc/dcmitype/](http://purl.org/dc/dcmitype/)\" "
            "xmlns:xsi=\"[http://www.w3.org/2001/XMLSchema-instance](http://www.w3.org/2001/XMLSchema-instance)\">"
            f"<dc:title>{core_title}</dc:title>"
            "<dc:creator>NOVA-SYNESIS</dc:creator>"
            "<cp:lastModifiedBy>NOVA-SYNESIS</cp:lastModifiedBy>"
            f"<dcterms:created xsi:type=\"dcterms:W3CDTF\">{core_created}</dcterms:created>"
            f"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">{core_created}</dcterms:modified>"
            "</cp:coreProperties>",
        )
        archive.writestr(
            "docProps/app.xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Properties xmlns=\"[http://schemas.openxmlformats.org/officeDocument/2006/extended-properties](http://schemas.openxmlformats.org/officeDocument/2006/extended-properties)\" "
            "xmlns:vt=\"[http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes](http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes)\">"
            "<Application>NOVA-SYNESIS</Application>"
            "</Properties>",
        )
        archive.writestr("word/document.xml", document_xml)


def _serialize_invoice_record(
    record: dict[str, Any],
    *,
    index: int,
    as_of: datetime,
) -> dict[str, Any]:
    due_at = _parse_iso_datetime(record.get("invoice_due_date"))
    order_at = _parse_iso_datetime(record.get("order_date"))
    delivery_at = _parse_iso_datetime(record.get("delivery_date"))
    total_price = _parse_float(record.get("total_price", 0.0))
    invoice_paid = _parse_bool(record.get("invoice_paid", False))
    days_overdue = 0
    status = "PAID"
    if not invoice_paid:
        status = "OPEN"
        if due_at is not None and due_at.date() < as_of.date():
            status = "OVERDUE"
            days_overdue = (as_of.date() - due_at.date()).days

    return {
        "invoice_ref": str(record.get("id") or record.get("invoice_id") or f"invoice-{index:04d}"),
        "customer_name": str(record.get("customer_name", "")).strip(),
        "email": str(record.get("email", "")).strip(),
        "address": str(record.get("address", "")).strip(),
        "product": str(record.get("product", "")).strip(),
        "quantity": int(float(record.get("quantity", 0) or 0)),
        "price_per_unit": _parse_float(record.get("price_per_unit", 0.0)),
        "total_price": total_price,
        "order_date": order_at.isoformat() if order_at else None,
        "delivery_date": delivery_at.isoformat() if delivery_at else None,
        "invoice_due_date": due_at.isoformat() if due_at else None,
        "invoice_paid": invoice_paid,
        "status": status,
        "days_overdue": days_overdue,
    }


def _load_orders_from_csv(path: Path, *, as_of: datetime) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        return [
            _serialize_invoice_record(row, index=index, as_of=as_of)
            for index, row in enumerate(reader, start=1)
        ]


def _load_orders_from_sqlite(path: Path, *, table: str, as_of: datetime) -> list[dict[str, Any]]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError(f"Unsupported SQLite table name '{table}'")
    query = (
        "SELECT id, customer_name, email, address, product, quantity, price_per_unit, total_price, "
        "order_date, delivery_date, invoice_due_date, invoice_paid FROM "
        f"{table}"
    )
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query).fetchall()
    return [
        _serialize_invoice_record(dict(row), index=index, as_of=as_of)
        for index, row in enumerate(rows, start=1)
    ]


def _group_receivables(invoices: list[dict[str, Any]], *, as_of: datetime) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for invoice in invoices:
        if invoice["invoice_paid"]:
            continue
        grouped[
            (
                invoice["customer_name"],
                invoice["email"],
                invoice["address"],
            )
        ].append(invoice)

    customers: list[dict[str, Any]] = []
    overdue_count = 0
    invoice_count = 0
    total_outstanding = 0.0

    for index, ((customer_name, email, address), customer_invoices) in enumerate(grouped.items(), start=1):
        customer_invoices = sorted(
            customer_invoices,
            key=lambda item: item["invoice_due_date"] or "",
        )
        invoice_total = sum(item["total_price"] for item in customer_invoices)
        customer_overdue = sum(1 for item in customer_invoices if item["status"] == "OVERDUE")
        overdue_days = max((item["days_overdue"] for item in customer_invoices), default=0)
        overdue_count += customer_overdue
        invoice_count += len(customer_invoices)
        total_outstanding += invoice_total
        customers.append(
            {
                "customer_id": f"customer-{index:04d}",
                "customer_name": customer_name,
                "email": email,
                "address": address,
                "invoice_count": len(customer_invoices),
                "overdue_invoice_count": customer_overdue,
                "max_days_overdue": overdue_days,
                "total_outstanding": round(invoice_total, 2),
                "currency": "EUR",
                "invoices": customer_invoices,
            }
        )

    customers.sort(
        key=lambda item: (
            -item["overdue_invoice_count"],
            -item["total_outstanding"],
            item["customer_name"].casefold(),
        )
    )
    return {
        "as_of": as_of.isoformat(),
        "customer_count": len(customers),
        "invoice_count": invoice_count,
        "overdue_count": overdue_count,
        "total_outstanding": round(total_outstanding, 2),
        "currency": "EUR",
        "customers": customers,
    }


def _normalized_match_text(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return re.sub(r"\s+", " ", ascii_value.casefold()).strip()


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "").replace("&nbsp;", " ").strip()


def _topic_keyword_map(raw_topics: Any) -> dict[str, list[str]]:
    if isinstance(raw_topics, dict):
        topic_map: dict[str, list[str]] = {}
        for label, keywords in raw_topics.items():
            label_text = str(label).strip()
            if not label_text:
                continue
            normalized_keywords: list[str] = []
            if isinstance(keywords, list):
                normalized_keywords.extend(
                    _normalized_match_text(str(keyword))
                    for keyword in keywords
                    if str(keyword).strip()
                )
            default_keywords = DEFAULT_TOPIC_KEYWORDS.get(_normalized_match_text(label_text), [])
            topic_map[label_text] = sorted(
                {
                    keyword
                    for keyword in [*normalized_keywords, *default_keywords, _normalized_match_text(label_text)]
                    if keyword
                }
            )
        return topic_map

    labels = [
        str(item).strip()
        for item in (raw_topics if isinstance(raw_topics, list) else [])
        if str(item).strip()
    ]
    if not labels:
        labels = ["Robotik", "KI"]
    return {
        label: sorted(
            {
                keyword
                for keyword in [
                    _normalized_match_text(label),
                    *DEFAULT_TOPIC_KEYWORDS.get(_normalized_match_text(label), []),
                ]
                if keyword
            }
        )
        for label in labels
    }


def _csv_safe_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _csv_has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _detect_csv_columns(rows: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in row.keys():
            key_text = str(key).strip()
            if key_text and key_text not in seen:
                seen.append(key_text)
    return seen


def _is_placeholder_input_shell(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return True
        if re.fullmatch(r"[.\u2026]+", normalized):
            return True
        return normalized.casefold() in {
            "placeholder",
            "<placeholder>",
            "todo",
            "tbd",
            "null",
            "none",
        }
    if isinstance(value, dict):
        if not value:
            return True
        if "$ref" in value and len(value) == 1:
            return False
        return all(_is_placeholder_input_shell(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        if not value:
            return True
        return all(_is_placeholder_input_shell(item) for item in value)
    return False


def _has_valid_embedding_payload(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    embedding = value.get("embedding")
    if not isinstance(embedding, (list, tuple)) or not embedding:
        return False
    try:
        [float(component) for component in embedding]
    except (TypeError, ValueError):
        return False
    return True


def _resolve_upstream_embedding_result(context: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    flow = context.get("flow")
    node_id = context.get("node_id")
    results = context.get("results") or {}
    if flow is None or node_id is None or not hasattr(flow, "incoming_edges"):
        return None, None

    for edge in reversed(flow.incoming_edges(str(node_id))):
        upstream_result = results.get(edge.from_node)
        if _has_valid_embedding_payload(upstream_result):
            return edge.from_node, upstream_result
    return None, None


def _normalize_memory_store_value(context: dict[str, Any], payload: dict[str, Any]) -> tuple[Any, str | None]:
    memory_id = str(payload["memory_id"])
    value = payload["value"]

    try:
        memory_system = context["memory_manager"].get(memory_id)
        raw_memory_type = getattr(memory_system, "type", None)
        memory_type = getattr(raw_memory_type, "value", str(raw_memory_type))
    except Exception:
        memory_type = None

    if memory_type != "VECTOR":
        return value, None

    if _has_valid_embedding_payload(value):
        return value, None

    upstream_node_id, upstream_result = _resolve_upstream_embedding_result(context)
    if upstream_result is not None and (
        value is None
        or _is_placeholder_input_shell(value)
        or (isinstance(value, dict) and "embedding" in value)
    ):
        return upstream_result, upstream_node_id

    if isinstance(value, dict) and "embedding" in value:
        raise ValueError(
            "memory_store received an invalid vector payload; use the upstream generate_embedding result or provide an 'embedding' list of numbers"
        )

    return value, None


def _extract_google_news_items(feed_xml: str, *, max_items: int) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(feed_xml)
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title_text = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        published_at = (item.findtext("pubDate") or "").strip()
        source_name = (item.findtext("source") or "").strip()
        title_without_source = title_text
        if not source_name and " - " in title_text:
            title_without_source, source_name = title_text.rsplit(" - ", 1)
        items.append(
            {
                "title": title_without_source.strip(),
                "source": source_name.strip(),
                "link": link,
                "summary": re.sub(r"\s+", " ", description).strip(),
                "published_at": published_at,
            }
        )
        if len(items) >= max_items:
            break
    return items


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
    value, repaired_from_node = _normalize_memory_store_value(context, payload)
    result = await context["memory_manager"].store(
        memory_id=str(payload["memory_id"]),
        key=str(payload["key"]),
        value=value,
    )
    if repaired_from_node is not None:
        result["auto_repaired_value_from_node"] = repaired_from_node
        result["auto_repaired_value"] = True
    return result


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
    target_agent_name = payload.get("target_agent_name")
    if target_agent_id is not None:
        target_agent = agents[int(target_agent_id)]
    elif target_agent_name is not None:
        resolved_name = str(target_agent_name).strip().casefold()
        for agent in agents.values():
            if agent.name.casefold() == resolved_name:
                target_agent = agent
                target_agent_id = agent.agent_id
                break

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
        raise ValueError(
            "send_message requires either a sender with comms or a target agent resolved by target_agent_id or target_agent_name"
        )

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


async def news_search_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    query = str(payload.get("query") or "IT Nachrichten").strip() or "IT Nachrichten"
    language = str(payload.get("language", "de")).strip().lower() or "de"
    country = str(payload.get("country", "DE")).strip().upper() or "DE"
    time_range = str(payload.get("time_range", "7d")).strip().lower()
    max_items = max(1, min(int(payload.get("max_items", 20)), 100))
    timeout_s = float(payload.get("timeout_s", 15.0))
    search_query = query if not time_range else f"{query} when:{time_range}"
    endpoint = "https://news.google.com/rss/search"
    params = {
        "q": search_query,
        "hl": f"{language}-{country}",
        "gl": country,
        "ceid": f"{country}:{language}",
    }

    async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
        response = await client.get(endpoint, params=params)
        response.raise_for_status()

    items = _extract_google_news_items(response.text, max_items=max_items)
    return {
        "query": query,
        "search_query": search_query,
        "feed_url": f"{endpoint}?{urlencode(params)}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "items": items,
    }


def topic_split_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    raw_items = payload.get("items") or payload.get("articles") or []
    if not isinstance(raw_items, list):
        raise ValueError("topic_split requires an 'items' list")
    include_uncategorized = bool(payload.get("include_uncategorized", True))
    topic_map = _topic_keyword_map(payload.get("topics"))
    grouped: dict[str, list[dict[str, Any]]] = {label: [] for label in topic_map}
    csv_rows: list[dict[str, Any]] = []
    uncategorized_label = str(payload.get("uncategorized_label", "Sonstiges")).strip() or "Sonstiges"

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        haystack = _normalized_match_text(
            " ".join(
                str(
                    item.get(field, "")
                )
                for field in ("title", "summary", "source")
            )
        )
        matched_topics = [
            label
            for label, keywords in topic_map.items()
            if any(keyword and keyword in haystack for keyword in keywords)
        ]
        if not matched_topics and include_uncategorized:
            grouped.setdefault(uncategorized_label, [])
            matched_topics = [uncategorized_label]

        item["matched_topics"] = matched_topics
        for label in matched_topics:
            grouped.setdefault(label, []).append(item)
            csv_rows.append(
                {
                    "topic": label,
                    "title": str(item.get("title", "")),
                    "source": str(item.get("source", "")),
                    "published_at": str(item.get("published_at", "")),
                    "link": str(item.get("link", "")),
                    "summary": str(item.get("summary", "")),
                }
            )

    return {
        "topic_count": len(grouped),
        "topics": grouped,
        "classified_item_count": sum(len(items) for items in grouped.values()),
        "csv_rows": csv_rows,
    }


def template_render_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    template = str(payload["template"])
    values = payload.get("values", {})
    return {"rendered": template.format_map(values)}


def human_input_request_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    task = context.get("task")
    if task is None:
        raise RuntimeError("human_input_request requires task context")

    existing_response = task.metadata.get("human_input_response")
    if isinstance(existing_response, dict) and "value" in existing_response:
        return {
            "submitted": True,
            "value": existing_response.get("value"),
            "submitted_by": existing_response.get("submitted_by"),
            "submitted_at": existing_response.get("submitted_at"),
            "metadata": existing_response.get("metadata", {}),
        }

    request = HumanInputRequest(
        title=str(payload.get("title", "Human Input Required")).strip() or "Human Input Required",
        description=(
            str(payload.get("description")).strip()
            if payload.get("description") not in {None, ""}
            else None
        ),
        schema=dict(payload.get("schema", {})),
        default_value=payload.get("default_value"),
        required_role=(
            str(payload.get("required_role")).strip()
            if payload.get("required_role") not in {None, ""}
            else None
        ),
        timeout_s=int(payload["timeout_s"]) if payload.get("timeout_s") not in {None, ""} else None,
        requested_by=str(payload.get("requested_by", context.get("node_id", "runtime"))),
    )
    raise HumanInputRequiredError(request)


def _stringify_local_llm_input(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return str(value)


def _looks_like_follow_up_request(prompt_text: str) -> bool:
    normalized = prompt_text.casefold()
    return any(
        token in normalized
        for token in (
            "please provide",
            "once you provide",
            "looking forward to receiving",
            "share the output",
            "provide the output",
            "send the output",
            "send the results",
            "waiting for the results",
        )
    )


async def local_llm_text_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    settings = context.get("settings")
    if not isinstance(settings, Settings):
        raise RuntimeError("local_llm_text requires runtime settings")

    prompt = payload.get("prompt")
    instruction = payload.get("instruction")
    system_prompt = payload.get("system_prompt")
    data = payload.get("data")

    if data is None:
        for alias in ("content", "code", "text", "input", "value", "document", "source", "result"):
            if alias in payload:
                data = payload[alias]
                break

    rendered_input = _stringify_local_llm_input(data).strip()

    if prompt in {None, ""}:
        if not rendered_input:
            raise ValueError("local_llm_text requires either a 'prompt' or non-empty 'data'")
        instruction_text = str(
            instruction or "Analyze the provided input and return a concise technical result."
        ).strip()
        prompt_parts = []
        if system_prompt not in {None, ""}:
            prompt_parts.append(str(system_prompt).strip())
        prompt_parts.append(instruction_text)
        prompt_parts.append(f"Input:\n{rendered_input}")
        prompt = "\n\n".join(part for part in prompt_parts if part)
    else:
        prompt_text = str(prompt).strip()
        if rendered_input:
            guidance = (
                "Use the following input as the complete source material. "
                "Do not ask for additional input, do not request missing data, and produce the final result directly."
            )
            if _looks_like_follow_up_request(prompt_text):
                prompt_text = (
                    "Create the final result directly from the provided source material. "
                    "Do not ask the user for more data.\n\nOriginal task context:\n"
                    f"{prompt_text}"
                )
            prompt_parts = []
            if system_prompt not in {None, ""}:
                prompt_parts.append(str(system_prompt).strip())
            prompt_parts.append(prompt_text)
            prompt_parts.append(guidance)
            prompt_parts.append(f"Input:\n{rendered_input}")
            prompt = "\n\n".join(part for part in prompt_parts if part)
        else:
            prompt_parts = []
            if system_prompt not in {None, ""}:
                prompt_parts.append(str(system_prompt).strip())
            prompt_parts.append(prompt_text)
            prompt = "\n\n".join(part for part in prompt_parts if part)

    raw_timeout = payload.get("timeout_s")
    timeout_s = int(raw_timeout) if raw_timeout not in {None, ""} else settings.lit_timeout_s
    text = _generate_local_text(prompt, settings, timeout_s=timeout_s)
    prompt_tokens = max(1, len(prompt.split()))
    completion_tokens = max(1, len(text.split())) if text else 0
    return {
        "text": text,
        "prompt": prompt,
        "model_path": settings.lit_model_path,
        "backend": settings.lit_backend,
        "_telemetry": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model_name": Path(settings.lit_model_path).name,
        },
    }


async def generate_embedding_handler(context: dict[str, Any]) -> dict[str, Any]:
    """
    Handler to convert text or structured data into a format required by VectorMemory.
    Fix: Using isoformat() for timestamp to ensure JSON serializability.
    """
    payload = dict(context["input"] or {})
    raw_data = payload.get("data")
    
    if not raw_data:
        raise ValueError("generate_embedding requires 'data' input")

    # Serialisierung sicherstellen, falls raw_data ein komplexes Objekt ist
    text_content = json.dumps(raw_data, ensure_ascii=False, default=str) if not isinstance(raw_data, str) else raw_data
    
    # Dummy-Vektor Logik
    vector_size = 128
    dummy_embedding = [float(len(text_content) % (i + 1)) / 10.0 for i in range(vector_size)]

    return {
        "embedding": dummy_embedding,
        "value": raw_data,
        "metadata": {
            "source_node": context.get("node_id"),
            # WICHTIG: .isoformat() macht daraus einen String!
            "timestamp": datetime.now(timezone.utc).isoformat() 
        }
    }


def accounts_receivable_extract_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    working_directory = Path(context["working_directory"])
    path = _resolve_working_path(
        working_directory=working_directory,
        raw_path=str(payload["path"]),
        allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
    )
    as_of = _parse_iso_datetime(payload.get("as_of")) or datetime.now(timezone.utc)
    source_kind = str(payload.get("source_type", "auto")).casefold()
    table = str(payload.get("table", "orders"))

    if source_kind == "auto":
        if path.suffix.casefold() == ".csv":
            source_kind = "csv"
        elif path.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
            source_kind = "sqlite"
        else:
            raise ValueError(f"Unsupported accounts receivable source '{path.suffix}'")

    if source_kind == "csv":
        invoices = _load_orders_from_csv(path, as_of=as_of)
    elif source_kind in {"sqlite", "db", "database"}:
        invoices = _load_orders_from_sqlite(path, table=table, as_of=as_of)
    else:
        raise ValueError(f"Unsupported source_type '{source_kind}'")

    summary = _group_receivables(invoices, as_of=as_of)
    summary.update(
        {
            "source_path": str(path),
            "source_type": "sqlite" if source_kind in {"sqlite", "db", "database"} else "csv",
            "table": table if source_kind in {"sqlite", "db", "database"} else None,
        }
    )
    return summary


def accounts_receivable_generate_letters_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    receivables = payload.get("receivables")
    if not isinstance(receivables, dict):
        raise ValueError("accounts_receivable_generate_letters requires a receivables payload")

    sender_company = str(payload.get("sender_company", "NOVA-SYNESIS Forderungsmanagement")).strip()
    sender_email = str(payload.get("sender_email", "buchhaltung@example.invalid")).strip()
    sender_phone = str(payload.get("sender_phone", "+49 000 000000")).strip()
    sender_address = str(payload.get("sender_address", "Musterstrasse 1, 10115 Berlin")).strip()
    payment_deadline_days = int(payload.get("payment_deadline_days", 7))
    generation_mode = str(payload.get("generation_mode", "template")).strip().casefold() or "template"
    use_local_llm = generation_mode in {"llm", "local_llm", "lit"}
    prompt_template = str(
        payload.get("prompt_template", DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE)
    )
    user_instruction = str(
        payload.get("user_instruction", DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION)
    ).strip() or DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION
    fallback_to_template_on_error = bool(payload.get("fallback_to_template_on_error", True))
    settings = context.get("settings")
    if use_local_llm and not isinstance(settings, Settings):
        raise ValueError("accounts_receivable_generate_letters requires runtime settings for local LLM mode")
    as_of = _parse_iso_datetime(receivables.get("as_of")) or datetime.now(timezone.utc)
    due_date_text = as_of.date().isoformat()
    settle_by_text = (as_of.date() + timedelta(days=payment_deadline_days)).isoformat()

    letters: list[dict[str, Any]] = []
    generation_warnings: list[str] = []
    for index, customer in enumerate(receivables.get("customers", []), start=1):
        customer_name = str(customer.get("customer_name", "")).strip()
        email = str(customer.get("email", "")).strip()
        address = str(customer.get("address", "")).strip()
        drafted = _draft_receivable_letter(
            customer=customer,
            sender_company=sender_company,
            sender_email=sender_email,
            sender_phone=sender_phone,
            sender_address=sender_address,
            due_date_text=due_date_text,
            settle_by_text=settle_by_text,
            use_local_llm=use_local_llm,
            settings=settings if isinstance(settings, Settings) else None,
            prompt_template=prompt_template,
            user_instruction=user_instruction,
            fallback_to_template_on_error=fallback_to_template_on_error,
            customer_label=customer_name or f"customer-{index:04d}",
        )
        body = str(drafted["content"])
        actual_generation_mode = str(drafted["generation_mode"])
        generation_warnings.extend(str(item) for item in drafted["warnings"])
        file_stem = _ascii_slug(customer_name) or f"kunde-{index:04d}"
        letters.append(
            {
                "customer_name": customer_name,
                "email": email,
                "address": address,
                "subject": "Zahlungserinnerung zu offenen Forderungen",
                "file_stem": file_stem,
                "file_name": f"{index:03d}-{file_stem}-zahlungserinnerung.txt",
                "total_outstanding": customer["total_outstanding"],
                "invoice_count": customer["invoice_count"],
                "generation_mode": actual_generation_mode,
                "content": body,
            }
        )

    return {
        "as_of": receivables.get("as_of"),
        "letter_count": len(letters),
        "customer_count": receivables.get("customer_count", len(letters)),
        "total_outstanding": receivables.get("total_outstanding", 0.0),
        "generation_mode": "llm" if use_local_llm else "template",
        "llm": (
            {
                "enabled": True,
                "model_path": settings.lit_model_path,
                "backend": settings.lit_backend,
                "fallback_to_template_on_error": fallback_to_template_on_error,
            }
            if use_local_llm and isinstance(settings, Settings)
            else {
                "enabled": False,
                "model_path": None,
                "backend": None,
                "fallback_to_template_on_error": fallback_to_template_on_error,
            }
        ),
        "warnings": generation_warnings,
        "letters": letters,
    }


def accounts_receivable_write_letters_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    working_directory = Path(context["working_directory"])
    letters = list(payload.get("letters") or [])
    output_format = str(payload.get("output_format", "txt")).strip().casefold()
    output_directory = _resolve_working_path(
        working_directory=working_directory,
        raw_path=str(payload["output_directory"]),
        allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    encoding = str(payload.get("encoding", "utf-8"))

    written_letters: list[dict[str, Any]] = []
    for index, letter in enumerate(letters, start=1):
        if not isinstance(letter, dict):
            raise ValueError("accounts_receivable_write_letters expects each letter to be a dictionary")
        file_name = str(letter.get("file_name") or f"{index:03d}-zahlungserinnerung.txt")
        if output_format == "docx":
            file_name = _with_extension(file_name, ".docx")
        elif output_format == "txt":
            file_name = _with_extension(file_name, ".txt")
        else:
            raise ValueError("accounts_receivable_write_letters supports only output_format 'txt' or 'docx'")
        target_path = output_directory / file_name
        content = str(letter.get("content", ""))
        if output_format == "docx":
            _write_simple_docx(
                target_path,
                content=content,
                title=str(letter.get("subject") or "Zahlungserinnerung"),
            )
        else:
            target_path.write_text(content, encoding=encoding)
        written_letters.append(
            {
                "customer_name": letter.get("customer_name"),
                "email": letter.get("email"),
                "path": str(target_path),
                "subject": letter.get("subject"),
                "total_outstanding": letter.get("total_outstanding"),
                "generation_mode": letter.get("generation_mode"),
                "format": output_format,
            }
        )

    manifest_path_value = payload.get("manifest_path")
    manifest_path = None
    if manifest_path_value:
        manifest_path = _resolve_working_path(
            working_directory=working_directory,
            raw_path=str(manifest_path_value),
            allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "letter_count": len(written_letters),
                    "letters": written_letters,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding=encoding,
        )

    summary_path_value = payload.get("summary_path")
    summary_path = None
    if summary_path_value:
        summary_path = _resolve_working_path(
            working_directory=working_directory,
            raw_path=str(summary_path_value),
            allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_lines = [
            "Offene Forderungen: Serienanschreiben erzeugt",
            f"Anzahl Schreiben: {len(written_letters)}",
        ]
        for letter in written_letters:
            summary_lines.append(
                f"- {letter['customer_name']}: {letter['path']} ({_format_currency(float(letter['total_outstanding'] or 0.0))})"
            )
        summary_path.write_text("\n".join(summary_lines) + "\n", encoding=encoding)

    return {
        "written": True,
        "letter_count": len(written_letters),
        "output_directory": str(output_directory),
        "letters": written_letters,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "summary_path": str(summary_path) if summary_path else None,
    }


def merge_payloads_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    base = dict(payload.get("base", {}))
    for update in payload.get("updates", []):
        if not isinstance(update, dict):
            raise ValueError("merge_payloads expects all updates to be dictionaries")
        base.update(update)
    return base


async def execute_subflow_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    orchestrator = context.get("orchestrator")
    flow = context.get("flow")
    if orchestrator is None:
        raise RuntimeError("execute_subflow requires orchestrator context")
    target_flow_id = int(payload["target_flow_id"])
    target_version_id = (
        int(payload["target_version_id"])
        if payload.get("target_version_id") not in {None, ""}
        else None
    )
    input_mapping = payload.get("input_mapping", {})
    if input_mapping is not None and not isinstance(input_mapping, dict):
        raise ValueError("execute_subflow requires 'input_mapping' to be a dictionary")
    stack = list(flow.metadata.get("subflow_stack", [])) if flow is not None else []
    stack.append({"flow_id": flow.flow_id, "node_id": context.get("node_id")}) if flow is not None else None
    return await orchestrator.run_subflow(
        target_flow_id=target_flow_id,
        target_version_id=target_version_id,
        input_mapping=dict(input_mapping or {}),
        parent_stack=stack,
    )


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


def write_csv_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    working_directory = Path(context["working_directory"])
    path = _resolve_working_path(
        working_directory=working_directory,
        raw_path=str(payload["path"]),
        allow_outside_workdir=bool(payload.get("allow_outside_workdir", False)),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("write_csv requires a 'rows' list")
    normalized_rows = [dict(row) for row in rows if isinstance(row, dict)]
    detected_columns = _detect_csv_columns(normalized_rows)
    auto_corrected_fieldnames = False
    correction_reason: str | None = None
    fieldnames = payload.get("fieldnames")
    if isinstance(fieldnames, list) and fieldnames:
        columns = [str(field).strip() for field in fieldnames if str(field).strip()]
        if columns and normalized_rows and detected_columns:
            provided_set = {column.casefold() for column in columns}
            detected_set = {column.casefold() for column in detected_columns}
            overlap_count = len(provided_set & detected_set)
            populated_cells = sum(
                1
                for row in normalized_rows[:25]
                for column in columns
                if _csv_has_content(row.get(column))
            )
            total_cells = max(1, len(normalized_rows[:25]) * max(1, len(columns)))
            empty_ratio = 1.0 - (populated_cells / total_cells)
            has_placeholder_columns = any("placeholder" in column.casefold() for column in columns)
            if has_placeholder_columns or (overlap_count <= 1 and empty_ratio >= 0.6):
                columns = detected_columns
                auto_corrected_fieldnames = True
                correction_reason = (
                    "Provided fieldnames were incompatible with the actual row payload and were replaced "
                    "with detected row columns."
                )
    else:
        columns = detected_columns
    if not columns:
        columns = ["value"]
        normalized_rows = [{"value": _csv_safe_value(row)} for row in rows]
    encoding = str(payload.get("encoding", "utf-8"))
    with path.open("w", encoding=encoding, newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=columns)
        writer.writeheader()
        for row in normalized_rows:
            writer.writerow({column: _csv_safe_value(row.get(column)) for column in columns})
    return {
        "path": str(path),
        "written": True,
        "row_count": len(normalized_rows),
        "fieldnames": columns,
        "auto_corrected_fieldnames": auto_corrected_fieldnames,
        "fieldname_correction_reason": correction_reason,
    }


def json_serialize_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    return {"json": json.dumps(payload["value"], ensure_ascii=False, indent=payload.get("indent", 2))}

async def generate_embedding_handler(context: dict[str, Any]) -> dict[str, Any]:
    """
    Handler to convert data into a vector format. 
    Ensures JSON compatibility by converting timestamps to strings.
    """
    payload = dict(context.get("input") or {})
    raw_data = payload.get("data")
    
    if not raw_data:
        raise ValueError("generate_embedding requires 'data' input")

    # Sicherstellen, dass der Inhalt für das Pseudo-Embedding ein String ist
    text_content = json.dumps(raw_data, ensure_ascii=False, default=str) if not isinstance(raw_data, str) else raw_data
    
    # Generierung eines deterministischen Dummy-Vektors (128-dimensional)
    vector_size = 128
    dummy_embedding = [float(len(text_content) % (i + 1)) / 10.0 for i in range(vector_size)]

    return {
        "embedding": dummy_embedding,
        "value": raw_data,
        "metadata": {
            "source_node": context.get("node_id"),
            "timestamp": datetime.now(timezone.utc).isoformat() # Als String für JSON
        }
    }


def register_default_handlers(registry: TaskHandlerRegistry) -> None:
    registry.register("http_request", http_request_handler, built_in=True)
    registry.register("news_search", news_search_handler, built_in=True)
    registry.register("topic_split", topic_split_handler, built_in=True)
    registry.register("memory_store", memory_store_handler, built_in=True)
    registry.register("memory_retrieve", memory_retrieve_handler, built_in=True)
    registry.register("memory_search", memory_search_handler, built_in=True)
    registry.register("send_message", send_message_handler, built_in=True)
    registry.register("resource_health_check", resource_health_check_handler, built_in=True)
    registry.register("template_render", template_render_handler, built_in=True)
    registry.register("human_input_request", human_input_request_handler, built_in=True)
    registry.register("local_llm_text", local_llm_text_handler, built_in=True)
    registry.register("merge_payloads", merge_payloads_handler, built_in=True)
    registry.register("execute_subflow", execute_subflow_handler, built_in=True)
    registry.register("read_file", read_file_handler, built_in=True)
    registry.register("filesystem_read", read_file_handler, built_in=True)
    registry.register("write_file", write_file_handler, built_in=True)
    registry.register("filesystem_write", write_file_handler, built_in=True)
    registry.register("write_csv", write_csv_handler, built_in=True)
    registry.register("json_serialize", json_serialize_handler, built_in=True)
    registry.register("generate_embedding", generate_embedding_handler, built_in=True) # <--- Neu registriert
    registry.register("accounts_receivable_extract", accounts_receivable_extract_handler, built_in=True)
    registry.register(
        "accounts_receivable_generate_letters",
        accounts_receivable_generate_letters_handler,
        built_in=True,
    )
    registry.register(
        "accounts_receivable_write_letters",
        accounts_receivable_write_letters_handler,
        built_in=True,
    )
