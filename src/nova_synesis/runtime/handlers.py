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
from xml.sax.saxutils import escape as xml_escape

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
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
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
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
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
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" "
            "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
            "Target=\"word/document.xml\"/>"
            "<Relationship Id=\"rId2\" "
            "Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" "
            "Target=\"docProps/core.xml\"/>"
            "<Relationship Id=\"rId3\" "
            "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" "
            "Target=\"docProps/app.xml\"/>"
            "</Relationships>",
        )
        archive.writestr(
            "docProps/core.xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" "
            "xmlns:dc=\"http://purl.org/dc/elements/1.1/\" "
            "xmlns:dcterms=\"http://purl.org/dc/terms/\" "
            "xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" "
            "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
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
            "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" "
            "xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
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


def template_render_handler(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context["input"] or {})
    template = str(payload["template"])
    values = payload.get("values", {})
    return {"rendered": template.format_map(values)}


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
    as_of = _parse_iso_datetime(receivables.get("as_of")) or datetime.now(timezone.utc)
    due_date_text = as_of.date().isoformat()
    settle_by_text = (as_of.date() + timedelta(days=payment_deadline_days)).isoformat()

    letters: list[dict[str, Any]] = []
    for index, customer in enumerate(receivables.get("customers", []), start=1):
        customer_name = str(customer.get("customer_name", "")).strip()
        email = str(customer.get("email", "")).strip()
        address = str(customer.get("address", "")).strip()
        lines = []
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

        body = "\n".join(
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
                "content": body,
            }
        )

    return {
        "as_of": receivables.get("as_of"),
        "letter_count": len(letters),
        "customer_count": receivables.get("customer_count", len(letters)),
        "total_outstanding": receivables.get("total_outstanding", 0.0),
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
