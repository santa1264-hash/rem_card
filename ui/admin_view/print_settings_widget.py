import pathlib
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from rem_card.ui.shared.custom_message_box import CustomMessageBox
from rem_card.ui.rem_card_sectors.sector_print import (
    PrintConfig, DataCollectorWorker, FullReportWorker
)

class PrintSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remcard_service = None
        self.admission_id = None
        self.card_date = None
        self.config = PrintConfig()
        self.last_generated_pdf = None
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.frame = QFrame()
        self.frame.setObjectName("adminDictFrame")
        self.frame.setStyleSheet("""
            QFrame#adminDictFrame {
                border: 1.5px solid #bdc3c7;
                border-radius: 5px;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(self.frame)
        
        header = QLabel("Настройки печати отчетов")
        header.setProperty("heading", "true")
        header.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(header)

        # Чекбоксы выбора разделов
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
            layout.addWidget(cb)

        layout.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; border: none;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Кнопки генерации
        btn_layout = QHBoxLayout()
        self.btn_daily = QPushButton("Отчет за сутки")
        self.btn_full = QPushButton("Общий отчет")
        self.btn_save = QPushButton("Сохранить настройки")
        
        for btn in [self.btn_daily, self.btn_full, self.btn_save]:
            btn.setObjectName("DialogOkBtn")
            btn.setFixedHeight(40)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)

        # Кнопка назад
        self.btn_back = QPushButton("← Вернуться в меню")
        self.btn_back.setObjectName("DialogOkBtn")
        self.btn_back.setFixedHeight(40)
        layout.addWidget(self.btn_back)

        main_layout.addWidget(self.frame)

        # Коннекты
        self.btn_daily.clicked.connect(self.generate_daily)
        self.btn_full.clicked.connect(self.generate_full)
        self.btn_save.clicked.connect(self.on_save_clicked)

    def on_save_clicked(self):
        self.save_settings()
        self.status_label.setText("Настройки сохранены")

    def set_context(self, service, admission_id, date):
        self.remcard_service = service
        self.admission_id = admission_id
        self.card_date = date
        
        # Кнопки активны только если выбран пациент
        can_print = admission_id is not None
        self.btn_daily.setEnabled(can_print)
        self.btn_full.setEnabled(can_print)
        if not can_print:
            self.status_label.setText("Выберите пациента для печати отчета")
        else:
            self.status_label.setText("")

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
            self.cb_ventilation.isChecked(), False, False
        )

    def generate_daily(self):
        if not self.admission_id: return
        # Мы НЕ сохраняем настройки здесь принудительно, 
        # но загружаем актуальные перед печатью (на всякий случай)
        self.load_settings()
        self.status_label.setText("Формирование отчета за сутки...")
        self.worker = DataCollectorWorker(self.remcard_service, self.admission_id, self.card_date, self.config.load())
        self.worker.finished.connect(self.on_data_collected)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def generate_full(self):
        if not self.admission_id: return
        self.load_settings()
        try:
            dates = self.remcard_service.get_all_card_dates(self.admission_id)
            if not dates:
                CustomMessageBox.information(self, "Инфо", "Нет данных для формирования общего отчета.")
                return
            self.status_label.setText("Формирование общего отчета...")
            self.worker = FullReportWorker(self.remcard_service, self.admission_id, dates, self.config.load())
            self.worker.finished.connect(self.on_full_data_collected)
            self.worker.error.connect(self.on_error)
            self.worker.start()
        except Exception as e:
            self.on_error(str(e))

    def on_error(self, msg):
        self.status_label.setText("Ошибка")
        CustomMessageBox.critical(self, "Ошибка", msg)

    def on_data_collected(self, data):
        try:
            from rem_card.app.paths import REPORT_DIR
            from rem_card.ui.rem_card_sectors.s_print.builder import ReportBuilder
            report_dir = pathlib.Path(REPORT_DIR)
            report_dir.mkdir(parents=True, exist_ok=True)
            p_name = data['patient_name'].replace(' ', '_').replace('/', '_')
            pdf_path = report_dir / f"{p_name}_{data['start_dt'].strftime('%Y-%m-%d')}_day{data['icu_day']}.pdf"
            
            ReportBuilder.build_pdf(data, self.config.load(), pdf_path)
            self.last_generated_pdf = pdf_path
            self.status_label.setText("Готово!")
            self.open_pdf()
        except Exception as e:
            self.on_error(str(e))

    def on_full_data_collected(self, results):
        try:
            if not results: return
            from rem_card.app.paths import REPORT_DIR
            from rem_card.ui.rem_card_sectors.s_print.builder import ReportBuilder
            report_dir = pathlib.Path(REPORT_DIR)
            report_dir.mkdir(parents=True, exist_ok=True)
            p_name = results[0]['patient_name'].replace(' ', '_').replace('/', '_')
            pdf_path = report_dir / f"FULL_{p_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            ReportBuilder.build_pdf(results, self.config.load(), pdf_path)
            self.last_generated_pdf = pdf_path
            self.status_label.setText("Общий отчет готов!")
            self.open_pdf()
        except Exception as e:
            self.on_error(str(e))

    def open_pdf(self):
        if self.last_generated_pdf and self.last_generated_pdf.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_generated_pdf)))
