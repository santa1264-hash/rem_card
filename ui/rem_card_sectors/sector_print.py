import os
import pathlib
import datetime
import re
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLabel, QFrame, QApplication
)
from PySide6.QtCore import Qt, QSettings, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices

from rem_card.app.logger import logger
from rem_card.ui.shared.base_sector import BaseSectorWidget
from rem_card.ui.shared.custom_message_box import CustomMessageBox
from rem_card.services.balance_calculator import BalanceCalculator
from rem_card.services.report_vitals_slotting import select_latest_vitals_by_report_hour
from rem_card.data.dto.remcard_dto import AdministrationDTO

class PrintConfig:
    def __init__(self):
        self.settings = QSettings("SectorPrint", "Config")
        self.version = "1.0"
        
    def save(self, vitals: bool, balance: bool, prescriptions: bool, events: bool, 
             ventilation: bool, labs: bool, procedures: bool):
        self.settings.setValue("sector_print/version", self.version)
        self.settings.setValue("sector_print/sections/vitals", vitals)
        self.settings.setValue("sector_print/sections/balance", balance)
        self.settings.setValue("sector_print/sections/prescriptions", prescriptions)
        self.settings.setValue("sector_print/sections/events", events)
        self.settings.setValue("sector_print/sections/ventilation", ventilation)
        self.settings.setValue("sector_print/sections/labs", labs)
        self.settings.setValue("sector_print/sections/procedures", procedures)
        
    def load(self):
        return {
            "vitals": self.settings.value("sector_print/sections/vitals", True, type=bool),
            "balance": self.settings.value("sector_print/sections/balance", True, type=bool),
            "prescriptions": self.settings.value("sector_print/sections/prescriptions", True, type=bool),
            "events": self.settings.value("sector_print/sections/events", True, type=bool),
            "ventilation": self.settings.value("sector_print/sections/ventilation", False, type=bool),
            "labs": self.settings.value("sector_print/sections/labs", False, type=bool),
            "procedures": self.settings.value("sector_print/sections/procedures", False, type=bool)
        }

class FullReportWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, remcard_service, admission_id, dates, config):
        super().__init__()
        self.remcard_service = remcard_service
        self.admission_id = admission_id
        self.dates = dates
        self.config = config

    def run(self):
        try:
            results = []
            for dt in self.dates:
                start_dt, end_dt = self.remcard_service.get_day_period(dt)
                
                patient = self.remcard_service.get_patient(self.admission_id)
                if patient:
                    patient_name = f"{patient.last_name or ''} {patient.first_name or ''} {patient.middle_name or ''}".strip()
                    diagnosis = getattr(patient, 'diagnosis_text', None) or "—"
                    icu_day = "Неизвестно"
                    if patient.admission_datetime:
                        delta = start_dt.date() - patient.admission_datetime.date()
                        icu_day = str(delta.days + 1)
                else:
                    patient_name = "Неизвестный пациент"
                    diagnosis = "—"
                    icu_day = "?"

                day_data = {
                    "admission_id": self.admission_id,
                    "patient_name": patient_name,
                    "diagnosis": diagnosis,
                    "icu_day": icu_day,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "vitals": [],
                    "prescriptions": [],
                    "events": [],
                    "fluids_raw": [],
                    "ventilation_events": [],
                }

                if self.config.get("vitals", True):
                    day_data["vitals"] = self.remcard_service.get_vitals(self.admission_id, dt)
                
                day_data["prescriptions"] = self.remcard_service.get_orders(self.admission_id, dt, only_committed=True)

                if self.config.get("balance", True):
                    if hasattr(self.remcard_service, 'get_fluids'):
                        day_data["fluids_raw"] = self.remcard_service.get_fluids(self.admission_id, dt)

                if self.config.get("events", True):
                    if hasattr(self.remcard_service, 'status_service') and self.remcard_service.status_service:
                        day_data["events"] = self.remcard_service.status_service.get_events_in_range(self.admission_id, start_dt, end_dt)
                if self.config.get("ventilation", False):
                    day_data["ventilation_events"] = DataCollectorWorker.collect_ventilation_events(
                        self.remcard_service,
                        self.admission_id,
                        start_dt,
                        end_dt,
                    )

                processed_day = DataCollectorWorker.transform_data_static(day_data, self.remcard_service, self.config)
                results.append(processed_day)

            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Error in FullReport DataCollector: {str(e)}")
            self.error.emit(str(e))

class DataCollectorWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, remcard_service, admission_id, date, config):
        super().__init__()
        self.remcard_service = remcard_service
        self.admission_id = admission_id
        self.date = date
        self.config = config

    @staticmethod
    def collect_ventilation_events(remcard_service, admission_id, start_dt, end_dt):
        if not hasattr(remcard_service, "get_ventilation_timeline"):
            return []
        events = remcard_service.get_ventilation_timeline(admission_id) or []
        result = []
        for ev in events:
            ts = getattr(ev, "timestamp", None)
            if not ts:
                continue
            if ts < start_dt or ts >= end_dt:
                continue
            result.append(ev)
        return result

    @staticmethod
    def build_ventilation_struct(events):
        items = []
        event_labels = {
            "START_VENT": "Старт ИВЛ",
            "MODE_CHANGE": "Смена режима",
            "EXTUBATION": "Экстубация",
            "TRACHEOSTOMY": "Трахеостомия",
            "TUBE_REPLACEMENT": "Замена трубки",
        }
        mode_labels = {
            "CONTROLLED_VCV": "Controlled VCV",
            "CONTROLLED_PCV": "Controlled PCV",
            "SIMV_VC": "SIMV VC",
            "SIMV_PC": "SIMV PC",
            "PSV": "PSV",
            "CPAP": "CPAP",
            "BIPAP": "BIPAP",
            "SPONTANEOUS": "Spontaneous",
        }
        for ev in events or []:
            ts = getattr(ev, "timestamp", None)
            if not ts:
                continue
            event_type_raw = getattr(getattr(ev, "event_type", None), "value", getattr(ev, "event_type", None))
            mode_raw = getattr(getattr(ev, "mode", None), "value", getattr(ev, "mode", None))
            params = getattr(ev, "parameters", None) or {}
            params_text = ", ".join(f"{k}={v}" for k, v in sorted(params.items())) if params else "—"
            indications_parts = []
            ext_reason = getattr(ev, "extubation_reason", None)
            if ext_reason:
                indications_parts.append(str(ext_reason))
            o2_flow = getattr(ev, "o2_flow", None)
            if o2_flow is not None:
                indications_parts.append(f"O2={o2_flow}")
            indications = "; ".join(indications_parts) if indications_parts else "—"
            items.append(
                {
                    "time": ts.strftime("%d.%m.%Y %H:%M"),
                    "event": event_labels.get(str(event_type_raw), str(event_type_raw or "—")),
                    "mode": mode_labels.get(str(mode_raw), str(mode_raw or "—")) if mode_raw else "—",
                    "params": params_text,
                    "indications": indications,
                }
            )
        return items

    @staticmethod
    def transform_data_static(data: dict, remcard_service, config) -> dict:
        start_dt = data["start_dt"]
        end_dt = data["end_dt"]
        current_time = datetime.datetime.now()
        if current_time > end_dt: current_time = end_dt

        # 1. ВИТАЛЬНЫЕ: Почасовая таблица с 30-минутными окнами без "дыр"
        # (старт/финиш суток обработаны отдельно).
        vitals = data.get("vitals", [])
        vitals_matrix = {}

        selected_by_hour = select_latest_vitals_by_report_hour(vitals, start_dt, end_dt)
        for i, chosen_v in selected_by_hour.items():
            vitals_matrix[i] = {}
            for k, attr in [('hr', 'pulse'), ('sys', 'sys'), ('dia', 'dia'), ('spo2', 'spo2'), ('temp', 'temp'), ('rr', 'rr'), ('cvp', 'cvp')]:
                val = getattr(chosen_v, attr, None)
                if val is not None: vitals_matrix[i][k] = val
            
        data["vitals_matrix"] = vitals_matrix
        data["vital_settings"] = remcard_service.get_vital_settings_cached(data.get("admission_id", 0) or data.get("id", 0), start_dt)

        # 2. НАЗНАЧЕНИЯ
        orders = data.get("prescriptions", [])
        prescriptions_matrix = []
        order_ids = [o.id for o in orders if o.id is not None]
        
        all_admins = []
        if order_ids:
            rows = remcard_service.get_latest_administrations_for_order_ids(
                order_ids=order_ids,
                start_dt=start_dt,
                end_dt=end_dt,
                only_committed=True,
                include_deleted=False,
                include_cancelled=False,
                include_deleted_orders=True,
            )
            all_admins = [dict(r) for r in rows]

        for o in orders:
            status_val = o.status.value if hasattr(o.status, 'value') else str(o.status)
            is_committed = getattr(o, 'is_committed', 1)
            
            # В отчете скрываем только те, что были окончательно удалены/отменены в базе.
            # Если это черновик (is_committed=0), то продолжаем показывать старое состояние.
            if status_val in ("deleted", "cancelled") and is_committed == 1:
                continue
            
            dose = f"{getattr(o, 'dose_value', 0):g} {getattr(o, 'dose_unit', '')}".strip()
            if dose == "0":
                dose = ""
            comment = getattr(o, "comment", "")
            m = re.search(r'(\d+)\s*мл', comment.lower())
            volume = f"{m.group(1)} мл" if m else ""
            
            unit = str(getattr(o, 'dose_unit', '')).lower()
            if unit in ("мл", "ml"): 
                dosage_str = f"{getattr(o, 'dose_value', 0):g} мл"
            else: 
                # Убираем (volume) из основной строки, так как растворитель идет новой строкой
                dosage_str = dose
            if getattr(o, 'is_per_kg', False) and dosage_str: dosage_str += "/кг"

            latin_name = getattr(o, 'latin', 'Без названия')
            display_parts = []
            
            # 1. Разбиваем основной состав по "+"
            if "+" in latin_name:
                display_parts = [p.strip() for p in latin_name.split("+")]
                # Добавляем дозировку к последнему компоненту, если она есть
                if dosage_str and display_parts:
                    display_parts[-1] = f"{display_parts[-1]} {dosage_str}".strip()
            else:
                display_parts = [f"{latin_name} {dosage_str}".strip()]

            # 2. Ищем растворитель в комментарии
            # Проверяем наличие явного тега [DIL:...]
            diluent_match = re.search(r'\[DIL:(.*?)\]', comment)
            if diluent_match:
                diluent_text = diluent_match.group(1).strip()
                if diluent_text:
                    # Очищаем от других возможных тегов внутри растворителя
                    diluent_text = re.sub(r'\[ROUTE:.*?\]', '', diluent_text).strip()
                    diluent_text = re.sub(r'\[DUR:.*?\]', '', diluent_text).strip()
                    if diluent_text:
                        display_parts.append(diluent_text)
            else:
                # Если тега нет, но в комментарии есть что-то похожее на растворитель (S. ...)
                # и это не совпадает с тем, что уже есть в latin
                comment_clean = re.sub(r'\[ROUTE:.*?\]', '', comment).strip()
                comment_clean = re.sub(r'\[DUR:.*?\]', '', comment_clean).strip()
                if comment_clean.startswith("+"): comment_clean = comment_clean[1:].strip()
                
                if comment_clean and "S." in comment_clean and comment_clean not in latin_name:
                    display_parts.append(comment_clean)

            # Передаем список строк. render_prescriptions должен уметь его готовить.
            display_name = display_parts
            marks = [None] * 24
            order_admins_rows = [a for a in all_admins if a['order_id'] == o.id]
            o.administrations = []
            
            for a in order_admins_rows:
                p_time = datetime.datetime.fromisoformat(str(a['planned_time']).replace(" ", "T"))
                admin_dto = AdministrationDTO(
                    id=a['id'], order_id=o.id, chain_id=a.get('chain_id'),
                    big_chain_id=a.get('big_chain_id'), cell_role=a.get('cell_role', 'single'),
                    planned_time=p_time, status=a.get('status', 'planned'),
                    volume_ml=a.get('volume_ml', 0.0), comment=a.get('comment', '')
                )
                o.administrations.append(admin_dto)
                idx = int((p_time - start_dt).total_seconds() / 3600)
                if 0 <= idx < 24:
                    marks[idx] = {
                        "role": a.get('cell_role', 'single'),
                        "nurse_mark": a.get('comment', ''),
                        "planned_time": p_time,
                        "chain_key": a.get('big_chain_id') or a.get('chain_id'),
                    }

            # Добавляем препарат в отчет всегда, даже если нет отметок времени (как просил пользователь)
            prescriptions_matrix.append({"name": display_name, "marks": marks, "created_at": o.created_at})
        
        data["prescriptions_matrix"] = prescriptions_matrix

        # 3. БАЛАНС
        balance_res = BalanceCalculator.calculate(orders, current_time, end_dt)
        oral_cur = 0
        oral_day = 0
        admission_id = data.get("admission_id") or data.get("id")
        if config.get("balance", True) and admission_id and hasattr(remcard_service, "get_oral_intake_totals"):
            try:
                oral_totals = remcard_service.get_oral_intake_totals(admission_id, start_dt, current_time=current_time)
                oral_cur = oral_totals.get("current", 0) or 0
                oral_day = oral_totals.get("daily", 0) or 0
            except Exception as exc:
                logger.warning("Failed to load oral intake totals for print balance: %s", exc)
        balance_res["current"]["oral"] = round(oral_cur, 1)
        balance_res["daily"]["oral"] = round(oral_day, 1)
        balance_res["current"]["total"] = round((balance_res["current"].get("total", 0) or 0) + oral_cur, 1)
        balance_res["daily"]["total"] = round((balance_res["daily"].get("total", 0) or 0) + oral_day, 1)
        fluids = data.get("fluids_raw", [])
        f_detail_cur = {"urine": 0, "drain": 0, "ng": 0, "stool": 0, "other": 0}
        f_detail_full = {"urine": 0, "drain": 0, "ng": 0, "stool": 0, "other": 0}
        out_hourly = {} 

        for f in fluids:
            idx = int((f.timestamp - start_dt).total_seconds() / 3600)
            if 0 <= idx < 24:
                if idx not in out_hourly: out_hourly[idx] = {"urine":0, "drain":0, "ng":0, "stool":0, "other":0}
                for k, fk in [("urine","urine"), ("drain","drain_output"), ("ng","ng_output"), ("stool","stool"), ("other","other_output")]:
                    val = getattr(f, fk, 0) or 0
                    out_hourly[idx][k] += val
                    if f.timestamp <= current_time: f_detail_cur[k] += val
                    f_detail_full[k] += val
        
        data["balance_final"] = {
            "current": balance_res["current"], "full": balance_res["daily"],
            "out_cur": f_detail_cur, "out_full": f_detail_full, "out_hourly": out_hourly
        }

        # 4. СОБЫТИЯ
        events = data.get("events", [])
        events_struct = []
        status_map = {"ACTIVE": "В отделении", "OUT": "Вне отд.", "OR": "Оперблок", "TRANSFERRED": "Переведен", "DEAD": "Умер"}

        for ev in events:
            status_val = str(getattr(ev.status, 'value', ev.status))
            st_time = getattr(ev, 'start_time', None)
            en_time = getattr(ev, 'end_time', None)
            desc = getattr(ev, "reason_text", None) or "—"
            
            time_str = st_time.strftime("%d.%m.%Y %H:%M") if st_time else ""
            if en_time:
                time_str += f" - {en_time.strftime('%H:%M')}"
                if en_time.date() != (st_time.date() if st_time else None):
                    time_str = st_time.strftime("%d.%m %H:%M") + " - " + en_time.strftime("%d.%m %H:%M")

            events_struct.append({
                "time": time_str,
                "status": status_map.get(status_val, status_val),
                "desc": desc
            })
        data["events_struct"] = events_struct

        # 5. ИВЛ
        data["ventilation_struct"] = DataCollectorWorker.build_ventilation_struct(
            data.get("ventilation_events", [])
        )
        return data

    def run(self):
        try:
            start_dt, end_dt = self.remcard_service.get_day_period(self.date)
            patient = self.remcard_service.get_patient(self.admission_id)
            
            data = {
                "admission_id": self.admission_id,
                "patient_name": f"{patient.last_name or ''} {patient.first_name or ''} {patient.middle_name or ''}".strip() if patient else "Неизвестный",
                "diagnosis": getattr(patient, 'diagnosis_text', None) or "—" if patient else "—",
                "icu_day": str((start_dt.date() - patient.admission_datetime.date()).days + 1) if patient and patient.admission_datetime else "?",
                "start_dt": start_dt, "end_dt": end_dt, "vitals": [], "prescriptions": [], "events": [], "fluids_raw": [],
                "ventilation_events": []
            }

            if self.config.get("vitals", True):
                data["vitals"] = self.remcard_service.get_vitals(self.admission_id, self.date)
            
            data["prescriptions"] = self.remcard_service.get_orders(self.admission_id, self.date, only_committed=True)

            if self.config.get("balance", True):
                if hasattr(self.remcard_service, 'get_fluids'):
                    data["fluids_raw"] = self.remcard_service.get_fluids(self.admission_id, self.date)

            if self.config.get("events", True):
                if hasattr(self.remcard_service, 'status_service') and self.remcard_service.status_service:
                    data["events"] = self.remcard_service.status_service.get_events_in_range(self.admission_id, start_dt, end_dt)
            if self.config.get("ventilation", False):
                data["ventilation_events"] = self.collect_ventilation_events(
                    self.remcard_service,
                    self.admission_id,
                    start_dt,
                    end_dt,
                )

            data = self.transform_data_static(data, self.remcard_service, self.config)
            self.finished.emit(data)
        except Exception as e:
            logger.error(f"Error in Print DataCollector: {str(e)}")
            self.error.emit(str(e))

class SectorPrint(BaseSectorWidget):
    def __init__(self, parent=None):
        super().__init__("Печать", parent)
        self.label.hide()
        # Отступ: 3px сверху и снизу, 0px слева, 1px справа
        self.container_layout.setContentsMargins(0, 3, 1, 3)
        self.remcard_service = None
        self.admission_id = None
        self.card_date = None
        self.config = PrintConfig()
        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        main_frame = QFrame()
        main_frame.setStyleSheet('QFrame { border: 1.5px solid #bdc3c7; border-radius: 5px; background-color: #ffffff; }')
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_label = QLabel("Печать карты")
        header_label.setFixedHeight(30)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet('font-weight: bold; color: #495057; background: #e9ecef; border: none; border-bottom: 0.5px solid #bdc3c7; border-top-left-radius: 3px; border-top-right-radius: 3px;')
        
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(10)
        
        self.cb_vitals = QCheckBox("Таблица показателей")
        self.cb_balance = QCheckBox("Баланс")
        self.cb_prescriptions = QCheckBox("Назначения")
        self.cb_events = QCheckBox("События")
        self.cb_ventilation = QCheckBox("ИВЛ")
        self.cb_labs = QCheckBox("Анализы")
        self.cb_labs.setEnabled(False)
        self.cb_procedures = QCheckBox("Процедуры")
        self.cb_procedures.setEnabled(False)
        
        for cb in [self.cb_vitals, self.cb_prescriptions, self.cb_balance, self.cb_events, self.cb_ventilation, self.cb_labs, self.cb_procedures]:
            body_layout.addWidget(cb)
            
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; border: none;")
        self.status_label.setAlignment(Qt.AlignCenter)
        body_layout.addWidget(self.status_label)
        
        btn_layout = QHBoxLayout()
        btn_style = """
            QPushButton { background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 4px; color: #495057; font-weight: bold; }
            QPushButton:hover { background-color: #e2e6ea; }
            QPushButton:pressed { background-color: #dae0e5; }
            QPushButton:disabled { background-color: #e9ecef; color: #adb5bd; }
        """
        self.btn_generate = QPushButton("Отчет за сутки")
        self.btn_generate.setFixedHeight(32)
        self.btn_generate.setStyleSheet(btn_style)
        self.btn_generate.clicked.connect(self.generate_pdf)
        
        self.btn_open = QPushButton("Открыть PDF")
        self.btn_open.setFixedHeight(32)
        self.btn_open.setStyleSheet(btn_style)
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self.open_pdf)
        
        self.btn_print = QPushButton("Общий отчет")
        self.btn_print.setFixedHeight(32)
        self.btn_print.setStyleSheet(btn_style)
        self.btn_print.setEnabled(True)
        self.btn_print.clicked.connect(self.generate_full_report)
        
        btn_layout.addWidget(self.btn_generate)
        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_print)
        
        body_layout.addStretch()
        body_layout.addLayout(btn_layout)
        layout.addWidget(header_label)
        layout.addWidget(body_widget)
        self.set_content(main_frame)
        self.last_generated_pdf = None

    def set_context(self, remcard_service, admission_id, date):
        self.remcard_service, self.admission_id, self.card_date = remcard_service, admission_id, date

    def load_settings(self):
        cfg = self.config.load()
        self.cb_vitals.setChecked(cfg["vitals"])
        self.cb_balance.setChecked(cfg["balance"])
        self.cb_prescriptions.setChecked(cfg["prescriptions"])
        self.cb_events.setChecked(cfg["events"])
        self.cb_ventilation.setChecked(cfg.get("ventilation", False))

    def save_settings(self):
        self.config.save(
            self.cb_vitals.isChecked(),
            self.cb_balance.isChecked(),
            self.cb_prescriptions.isChecked(),
            self.cb_events.isChecked(),
            self.cb_ventilation.isChecked(),
            False,
            False,
        )

    def _get_context_from_parents(self):
        p = self.parent()
        while p:
            if hasattr(p, 'admission_id') and hasattr(p, 'current_date') and hasattr(p, 'service'):
                return p.service, p.admission_id, p.current_date
            p = p.parent()
        return None, None, None

    def generate_pdf(self):
        srv, adm, dt = self._get_context_from_parents()
        if adm and dt and srv: self.set_context(srv, adm, dt)
        if not self.admission_id: return
        self.save_settings()
        self.status_label.setText("Формирование...")
        self.worker = DataCollectorWorker(self.remcard_service, self.admission_id, self.card_date, self.config.load())
        self.worker.finished.connect(self.on_data_collected)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def generate_full_report(self):
        srv, adm, dt = self._get_context_from_parents()
        if adm and dt and srv: self.set_context(srv, adm, dt)
        if not self.admission_id: return
        self.save_settings()
        try:
            dates = self.remcard_service.get_all_card_dates(self.admission_id)
            if not dates: return
            self.worker = FullReportWorker(self.remcard_service, self.admission_id, dates, self.config.load())
            self.worker.finished.connect(self.on_full_data_collected)
            self.worker.error.connect(self.on_error)
            self.worker.start()
        except Exception as e: self.on_error(str(e))

    def on_error(self, msg):
        self.status_label.setText("Ошибка")
        CustomMessageBox.critical(self, "Ошибка", msg)

    def on_data_collected(self, data):
        try:
            from rem_card.app.paths import REPORT_DIR
            report_dir = pathlib.Path(REPORT_DIR)
            report_dir.mkdir(parents=True, exist_ok=True)
            p_name = data['patient_name'].replace(' ', '_').replace('/', '_')
            pdf_path = report_dir / f"{p_name}_{data['start_dt'].strftime('%Y-%m-%d')}_day{data['icu_day']}.pdf"
            from rem_card.ui.rem_card_sectors.s_print.builder import ReportBuilder
            ReportBuilder.build_pdf(data, self.config.load(), pdf_path)
            self.last_generated_pdf = pdf_path
            self.status_label.setText("Готово!")
            self.btn_open.setEnabled(True)
        except Exception as e: self.on_error(str(e))

    def on_full_data_collected(self, results):
        try:
            if not results: return
            from rem_card.app.paths import REPORT_DIR
            report_dir = pathlib.Path(REPORT_DIR)
            report_dir.mkdir(parents=True, exist_ok=True)
            p_name = results[0]['patient_name'].replace(' ', '_').replace('/', '_')
            pdf_path = report_dir / f"FULL_{p_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            from rem_card.ui.rem_card_sectors.s_print.builder import ReportBuilder
            ReportBuilder.build_pdf(results, self.config.load(), pdf_path)
            self.last_generated_pdf = pdf_path
            self.status_label.setText("Общий отчет готов!")
            self.open_pdf()
        except Exception as e: self.on_error(str(e))

    def open_pdf(self):
        if self.last_generated_pdf and self.last_generated_pdf.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_generated_pdf)))
