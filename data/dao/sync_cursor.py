from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

EPOCH_SYNC_TS = "1970-01-01 00:00:00.000"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def normalize_sync_cursor(cursor: Any, *, default_ts: str = EPOCH_SYNC_TS) -> Tuple[str, int]:
    if cursor is None:
        return default_ts, 0

    if isinstance(cursor, Mapping):
        ts = str(
            cursor.get("updated_at")
            or cursor.get("last_sync_time")
            or cursor.get("ts")
            or default_ts
        )
        row_id = _safe_int(cursor.get("id", 0))
        return ts, row_id

    if isinstance(cursor, (list, tuple)) and len(cursor) >= 2:
        ts = str(cursor[0] or default_ts)
        row_id = _safe_int(cursor[1], 0)
        return ts, row_id

    return str(cursor or default_ts), 0


def make_sync_cursor(updated_at: str, row_id: int) -> Dict[str, Any]:
    return {
        "updated_at": str(updated_at or EPOCH_SYNC_TS),
        "id": _safe_int(row_id, 0),
    }


def is_cursor_newer(
    candidate_ts: str,
    candidate_id: int,
    current_ts: str,
    current_id: int,
) -> bool:
    if candidate_ts > current_ts:
        return True
    if candidate_ts == current_ts and int(candidate_id) > int(current_id):
        return True
    return False


def max_sync_cursor(*cursors: Any, default_ts: str = EPOCH_SYNC_TS) -> Dict[str, Any]:
    best_ts, best_id = normalize_sync_cursor(None, default_ts=default_ts)
    for cursor in cursors:
        ts, row_id = normalize_sync_cursor(cursor, default_ts=default_ts)
        if is_cursor_newer(ts, row_id, best_ts, best_id):
            best_ts, best_id = ts, row_id
    return make_sync_cursor(best_ts, best_id)
