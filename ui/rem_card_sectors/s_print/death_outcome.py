import json
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional

from .table_layout import (
    cell_attrs,
    cell_content,
    colspan_cell_attrs,
    render_colgroup,
    table_width_attrs,
    weighted_widths,
)


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.replace(second=0, microsecond=0, tzinfo=None)
    if value in (None, ""):
        return None

    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace(" ", "T")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed.replace(second=0, microsecond=0, tzinfo=None)


def _decode_payload(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        decoded = json.loads(str(value))
    except Exception:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _normalize_measures(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []

    result = []
    for item in value:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("label") or "").strip()
            text = str(item.get("value") or item.get("text") or item.get("comment") or "").strip()
        else:
            name = ""
            text = str(item or "").strip()
        if name or text:
            result.append({"name": name, "value": text})
    return result


def _format_dt(value: Optional[datetime]) -> str:
    return value.strftime("%d.%m.%Y %H:%M") if value else "—"


def _html_text(value: Any, fallback: str = "—") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return escape(text).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")


def _render_measures(measures: List[Dict[str, str]]) -> str:
    if not measures:
        return "—"

    rows = []
    for item in measures:
        name = _html_text(item.get("name"), "")
        value = _html_text(item.get("value"), "")
        if name and value:
            rows.append(f"{name}: {value}")
        elif name:
            rows.append(name)
        elif value:
            rows.append(value)
    return "<br/>".join(rows) if rows else "—"


def build_death_outcome_struct(remcard_service, admission_id, start_dt, end_dt) -> Dict[str, Any]:
    if not admission_id:
        return {}

    status_service = getattr(remcard_service, "status_service", None)
    if not status_service or not hasattr(status_service, "get_admission_outcome_context"):
        return {}

    try:
        context = status_service.get_admission_outcome_context(admission_id) or {}
    except Exception:
        return {}

    payload = _decode_payload(context.get("cardiac_arrest_measures_json"))
    biological_dt = _parse_dt(
        context.get("death_datetime") or payload.get("biological_death_datetime")
    )
    clinical_dt = _parse_dt(
        context.get("clinical_death_datetime") or payload.get("clinical_death_datetime")
    )

    outcome = str(context.get("outcome") or "").strip().lower()
    is_death = outcome in {"умер", "dead", "death"} or biological_dt is not None
    if not is_death:
        return {}

    if biological_dt is not None and start_dt is not None and end_dt is not None:
        start_bound = start_dt.replace(second=0, microsecond=0, tzinfo=None)
        end_bound = end_dt.replace(second=0, microsecond=0, tzinfo=None)
        if biological_dt < start_bound or biological_dt >= end_bound:
            return {}

    cause = context.get("cardiac_arrest_cause") or payload.get("cardiac_arrest_cause")
    return {
        "clinical_time": _format_dt(clinical_dt),
        "biological_time": _format_dt(biological_dt),
        "cause": str(cause or "").strip(),
        "comment": str(payload.get("comment") or "").strip(),
        "measures": _normalize_measures(payload.get("measures")),
    }


def render_death_outcome(data, table_width_pt):
    details = data.get("death_outcome") or {}
    if not details:
        return ""

    col_widths = weighted_widths(table_width_pt, [0.24, 0.76])
    label_style = "text-align: left; font-weight: bold; font-size: 8pt; padding: 4px; background-color: #f8f9fa;"
    value_style = "text-align: left; font-size: 8pt; padding: 4px; line-height: 1.25;"
    signature_html = (
        "ФИО врача ________________________________________________"
        "&nbsp;&nbsp;&nbsp;&nbsp;"
        "Подпись ______________________________"
    )

    def row(label: str, value: str, extra_value_style: str = "") -> str:
        merged_value_style = value_style
        if extra_value_style:
            merged_value_style = f"{merged_value_style} {extra_value_style}"
        return (
            "<tr>"
            f'<td class="death-label" {cell_attrs(col_widths[0], label_style)}>{label}</td>'
            f'<td class="death-value" {cell_attrs(col_widths[1], merged_value_style)}>{cell_content(value)}</td>'
            "</tr>"
        )

    table_attrs = table_width_attrs(table_width_pt).replace(
        'style="',
        'style="page-break-inside: avoid; break-inside: avoid; ',
        1,
    )
    html = (
        '<div class="section section-avoid death-section" '
        'style="page-break-inside: avoid; break-inside: avoid;">'
    )
    html += f'<table class="report-table data-table death-table" {table_attrs}>'
    html += render_colgroup(col_widths)
    html += "<tbody>"
    html += f'<tr class="table-title-row"><th colspan="2" {colspan_cell_attrs()}>ИСХОД: СМЕРТЬ</th></tr>'
    html += row("Время клинической смерти", _html_text(details.get("clinical_time")))
    html += row("Причина остановки сердца", _html_text(details.get("cause")))
    html += row("Мероприятия", _render_measures(details.get("measures") or []))
    html += row("Комментарий к причине остановки сердца", _html_text(details.get("comment")))
    html += row("Время биологической смерти", _html_text(details.get("biological_time")))
    html += row("Врач", signature_html, "height: 28px; white-space: nowrap;")
    html += "</tbody></table></div>"
    return html
