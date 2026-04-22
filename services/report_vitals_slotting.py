from __future__ import annotations

from bisect import bisect_left
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List


def select_latest_vitals_by_report_hour(
    vitals: Iterable[Any],
    start_dt: datetime,
    end_dt: datetime,
    *,
    slots: int = 24,
) -> Dict[int, Any]:
    """
    Раскладывает vitals по часовым ячейкам отчета и выбирает в каждой ячейке
    самое свежее значение по timestamp.

    Правила окон (без "дыр"):
    - 1-я ячейка (08:00): [08:00, 08:31)
    - Промежуточные: [H-00:29, H+00:31)
      пример: для 11:00 это [10:31, 11:31)
    - Последняя ячейка (07:00): [06:31, end_dt)
      что покрывает значения до 07:59 включительно (при end_dt = 08:00)
    """
    valid: List[Any] = [
        v for v in vitals
        if getattr(v, "timestamp", None) is not None
    ]
    if not valid:
        return {}

    valid.sort(key=lambda x: x.timestamp)
    timestamps = [v.timestamp for v in valid]

    result: Dict[int, Any] = {}
    for i in range(slots):
        target_time = start_dt + timedelta(hours=i)

        if i == 0:
            slot_start = start_dt
            slot_end = min(end_dt, target_time + timedelta(minutes=31))
        elif i == (slots - 1):
            slot_start = target_time - timedelta(minutes=29)
            slot_end = end_dt
        else:
            slot_start = target_time - timedelta(minutes=29)
            slot_end = min(end_dt, target_time + timedelta(minutes=31))

        if slot_end <= slot_start:
            continue

        left = bisect_left(timestamps, slot_start)
        right = bisect_left(timestamps, slot_end)
        if right > left:
            result[i] = valid[right - 1]

    return result

