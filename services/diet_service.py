import json
import re
from datetime import datetime
from typing import Any, List, Optional

from rem_card.data.dao.diet_dao import DietPlanDAO, DietTemplateDAO, OralIntakeDAO
from rem_card.data.dao.exceptions import OptimisticLockError
from rem_card.data.dto.remcard_dto import DietPlanDTO, DietTemplateDTO, OralIntakeEventDTO
from rem_card.services.shift_service import ShiftService


TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def _dt_to_db(value: datetime) -> str:
    return value.replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")


def normalize_minute(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("datetime expected")
    return value.replace(second=0, microsecond=0)


def normalize_schedule(schedule: Any) -> str:
    if schedule is None or schedule == "":
        raw_items = []
    elif isinstance(schedule, str):
        raw_items = json.loads(schedule)
    else:
        raw_items = schedule

    if not isinstance(raw_items, list):
        raise ValueError("Расписание питания должно быть списком")

    normalized = []
    seen_times = set()
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("Строка расписания питания должна быть объектом")
        time_text = str(item.get("time") or "").strip()
        if not TIME_RE.fullmatch(time_text) or not ShiftService.is_time_input_valid(time_text):
            raise ValueError("Время питания должно быть в формате HH:mm")
        normalized_time = ShiftService.normalize_time(time_text)
        if normalized_time in seen_times:
            raise ValueError("В расписании питания не должно быть повторяющихся времен")
        seen_times.add(normalized_time)
        amount = int(float(item.get("amount") or 0))
        if amount <= 0:
            raise ValueError("Объем питания должен быть больше 0 мл")
        normalized.append({"time": normalized_time, "amount": amount})

    normalized.sort(key=lambda item: ((int(item["time"][:2]) - 8) % 24, int(item["time"][3:5])))
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def schedule_items(schedule_json: str) -> list[dict[str, int | str]]:
    try:
        items = json.loads(schedule_json or "[]")
    except Exception:
        return []
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        time_text = str(item.get("time") or "").strip()
        if not TIME_RE.fullmatch(time_text) or not ShiftService.is_time_input_valid(time_text):
            continue
        try:
            amount = int(float(item.get("amount") or 0))
        except Exception:
            continue
        if amount <= 0:
            continue
        result.append({"time": ShiftService.normalize_time(time_text), "amount": amount})
    result.sort(key=lambda item: ((int(str(item["time"])[:2]) - 8) % 24, int(str(item["time"])[3:5])))
    return result


class DietTemplateService:
    def __init__(self, dao: DietTemplateDAO):
        self.dao = dao

    def list_templates(self) -> List[DietTemplateDTO]:
        return self.dao.list_templates()

    def get_template(self, template_id: int) -> DietTemplateDTO:
        template = self.dao.get_template(template_id)
        if not template:
            raise ValueError("Шаблон питания не найден")
        return template

    def create_template(self, name: str, diet_text: str = "", schedule_json: Any = None, is_default: bool = False):
        dto = DietTemplateDTO(
            name=self._normalize_name(name),
            diet_text=str(diet_text or ""),
            schedule_json=normalize_schedule(schedule_json),
            is_default=1 if is_default else 0,
            last_modified_by="doctor",
        )
        with self.dao.db.remcard_transaction(source="diet_template_create") as cursor:
            return self.dao.create_template(dto, cursor=cursor)

    def update_template(
        self,
        template_id: int,
        name: str,
        diet_text: str = "",
        schedule_json: Any = None,
        is_default: bool = False,
        expected_version: Optional[int] = None,
    ):
        current = self.get_template(template_id)
        dto = DietTemplateDTO(
            id=int(template_id),
            name=self._normalize_name(name),
            diet_text=str(diet_text or ""),
            schedule_json=normalize_schedule(schedule_json),
            is_default=1 if is_default else 0,
            version=int(expected_version if expected_version is not None else current.version or 0),
            last_modified_by="doctor",
        )
        with self.dao.db.remcard_transaction(source="diet_template_update") as cursor:
            self.dao.update_template(dto, expected_version=dto.version, cursor=cursor)

    def delete_template(self, template_id: int, expected_version: Optional[int] = None):
        with self.dao.db.remcard_transaction(source="diet_template_delete") as cursor:
            self.dao.delete_template(template_id, expected_version=expected_version, cursor=cursor)

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized = str(name or "").strip()
        if not normalized:
            raise ValueError("Название шаблона питания обязательно")
        return normalized


class DietPlanService:
    def __init__(self, dao: DietPlanDAO, template_service: DietTemplateService):
        self.dao = dao
        self.template_service = template_service

    def shift_start_for_date(self, shift_date: datetime) -> datetime:
        start, _ = ShiftService.get_day_period(shift_date)
        return normalize_minute(start)

    def get_plan(self, admission_id: int, shift_date: datetime) -> Optional[DietPlanDTO]:
        return self.dao.get_plan(int(admission_id), self.shift_start_for_date(shift_date))

    def apply_template(
        self,
        admission_id: int,
        shift_date: datetime,
        template_id: int,
        expected_version: Optional[int] = None,
    ):
        template = self.template_service.get_template(template_id)
        dto = DietPlanDTO(
            admission_id=int(admission_id),
            shift_start=self.shift_start_for_date(shift_date),
            template_id=int(template_id),
            diet_text=template.diet_text,
            schedule_json=template.schedule_json,
            last_modified_by="doctor",
        )
        return self.dao.upsert_plan(dto, expected_version=expected_version)

    def upsert_plan(
        self,
        admission_id: int,
        shift_date: datetime,
        diet_text: str,
        schedule_json: Any,
        template_id: Optional[int] = None,
        expected_version: Optional[int] = None,
    ):
        dto = DietPlanDTO(
            admission_id=int(admission_id),
            shift_start=self.shift_start_for_date(shift_date),
            template_id=template_id,
            diet_text=str(diet_text or ""),
            schedule_json=normalize_schedule(schedule_json),
            last_modified_by="doctor",
        )
        return self.dao.upsert_plan(dto, expected_version=expected_version)

    def delete_plan(self, admission_id: int, shift_date: datetime, expected_version: Optional[int] = None):
        self.dao.delete_plan(
            int(admission_id),
            self.shift_start_for_date(shift_date),
            expected_version=expected_version,
        )


class OralIntakeService:
    def __init__(self, dao: OralIntakeDAO, vital_service, diet_plan_service: Optional[DietPlanService] = None):
        self.dao = dao
        self.vital_service = vital_service
        self.diet_plan_service = diet_plan_service

    def normalize_event_time(self, event_time: Optional[datetime] = None) -> datetime:
        dt = normalize_minute(event_time or datetime.now())
        now = normalize_minute(datetime.now())
        if dt > now:
            raise ValueError("Факт перорального ввода не может быть в будущем")
        return dt

    def shift_start_for_event(self, event_time: datetime) -> datetime:
        start, _ = ShiftService.get_day_period(event_time)
        return normalize_minute(start)

    def get_events(self, admission_id: int, shift_date: datetime) -> List[OralIntakeEventDTO]:
        start, end = self.vital_service.get_effective_bounds(int(admission_id), shift_date)
        return self.dao.get_events(int(admission_id), start, end)

    def upsert_event(
        self,
        admission_id: int,
        event_time: datetime,
        amount_ml: Optional[float],
        expected_version: Optional[int] = None,
    ):
        event_dt = self.normalize_event_time(event_time)
        is_ok, msg = self.vital_service.validate_timestamp(int(admission_id), event_dt, self.shift_start_for_event(event_dt))
        if not is_ok:
            raise ValueError(msg)

        if amount_ml is None or float(amount_ml) <= 0:
            return self.delete_event(
                admission_id=int(admission_id),
                event_time=event_dt,
                expected_version=expected_version,
            )

        dto = OralIntakeEventDTO(
            admission_id=int(admission_id),
            shift_start=self.shift_start_for_event(event_dt),
            event_time=event_dt,
            amount_ml=float(amount_ml),
            last_modified_by="nurse",
        )
        try:
            return self.dao.upsert_event(dto, expected_version=expected_version)
        except OptimisticLockError:
            current = self.dao.get_event_at(int(admission_id), event_dt)
            if current and abs(float(current.amount_ml) - float(amount_ml)) < 0.001:
                return current
            raise

    def add_event(self, admission_id: int, amount_ml: float, event_time: Optional[datetime] = None):
        return self.upsert_event(int(admission_id), event_time or datetime.now(), amount_ml)

    def delete_event(
        self,
        admission_id: int,
        event_time: datetime,
        expected_version: Optional[int] = None,
    ):
        event_dt = self.normalize_event_time(event_time)
        try:
            self.dao.delete_event(int(admission_id), event_dt, expected_version=expected_version)
        except OptimisticLockError:
            current = self.dao.get_event_at(int(admission_id), event_dt)
            if current is None:
                return None
            raise
        return None

    def get_totals(self, admission_id: int, shift_date: datetime, current_time: Optional[datetime] = None) -> dict:
        start, end = self.vital_service.get_effective_bounds(int(admission_id), shift_date)
        calc_time = current_time or datetime.now()
        if calc_time < start:
            calc_time = start
        if calc_time >= end:
            calc_time = end

        events = self.dao.get_events(int(admission_id), start, end)
        plan = None
        if self.diet_plan_service is not None:
            plan = self.diet_plan_service.get_plan(int(admission_id), shift_date)
        return self._calculate_totals(events, plan, shift_date, start, end, normalize_minute(calc_time))

    @staticmethod
    def _calculate_totals(
        events: List[OralIntakeEventDTO],
        plan: Optional[DietPlanDTO],
        shift_date: datetime,
        start: datetime,
        end: datetime,
        current_time: datetime,
    ) -> dict:
        planned_by_time = {}
        if plan is not None:
            for item in schedule_items(plan.schedule_json):
                planned_dt = ShiftService.resolve_datetime(str(item["time"]), shift_date)
                if start <= planned_dt < end:
                    key = _dt_to_db(planned_dt)
                    planned_by_time[key] = planned_by_time.get(key, 0.0) + float(item["amount"])

        current = 0.0
        unplanned_daily = 0.0
        current_limit = normalize_minute(current_time)

        for event in events or []:
            event_dt = normalize_minute(event.event_time)
            amount = float(event.amount_ml or 0.0)
            if event_dt <= current_limit:
                current += amount
            # Плановые строки остаются планом; PRN/внеплановый факт добавляем к прогнозу отдельно.
            if _dt_to_db(event_dt) not in planned_by_time:
                unplanned_daily += amount

        daily = sum(planned_by_time.values()) + unplanned_daily
        return {"current": round(current, 1), "daily": round(daily, 1)}
