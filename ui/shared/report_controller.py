from __future__ import annotations

from datetime import datetime
import pathlib

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from rem_card.app.paths import REPORT_DIR
from rem_card.ui.shared.custom_message_box import CustomMessageBox


class RemCardReportController:
    """
    Контроллер генерации PDF-отчетов.
    Вынесен из doctor/nurse виджетов, чтобы разгрузить UI-классы без изменения поведения.
    """

    def __init__(self, service, parent_widget):
        self.service = service
        self.parent = parent_widget
        self.daily_worker = None
        self.full_worker = None

    def run_daily_report(self, admission_id: int, shift_date: datetime):
        if not admission_id or not self.service:
            return

        from ..rem_card_sectors.sector_print import DataCollectorWorker, PrintConfig
        from ..rem_card_sectors.s_print.builder import ReportBuilder

        cfg = PrintConfig().load()
        try:
            self.daily_worker = DataCollectorWorker(self.service, admission_id, shift_date, cfg)

            def on_finished(data):
                if not data:
                    return
                report_dir = pathlib.Path(REPORT_DIR)
                report_dir.mkdir(parents=True, exist_ok=True)
                patient_name = data["patient_name"].replace(" ", "_").replace("/", "_")
                pdf_path = report_dir / f"{patient_name}_{data['start_dt'].strftime('%Y-%m-%d')}_day{data['icu_day']}.pdf"
                ReportBuilder.build_pdf(data, cfg, pdf_path)
                if pdf_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

            def on_error(msg):
                CustomMessageBox.critical(
                    self.parent,
                    "Ошибка",
                    f"Не удалось собрать данные для отчета за сутки:\n{msg}",
                )

            self.daily_worker.finished.connect(on_finished)
            self.daily_worker.error.connect(on_error)
            self.daily_worker.start()
        except Exception as exc:
            CustomMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Ошибка при инициализации отчета: {exc}",
            )

    def run_full_report(self, admission_id: int):
        if not admission_id or not self.service:
            return

        from ..rem_card_sectors.sector_print import FullReportWorker, PrintConfig
        from ..rem_card_sectors.s_print.builder import ReportBuilder

        cfg = PrintConfig().load()
        try:
            dates = self.service.get_all_card_dates(admission_id)
            if not dates:
                CustomMessageBox.information(
                    self.parent,
                    "Инфо",
                    "Нет данных для формирования общего отчета.",
                )
                return

            self.full_worker = FullReportWorker(self.service, admission_id, dates, cfg)

            def on_finished(results):
                if not results:
                    return
                report_dir = pathlib.Path(REPORT_DIR)
                report_dir.mkdir(parents=True, exist_ok=True)
                patient_name = results[0]["patient_name"].replace(" ", "_").replace("/", "_")
                pdf_path = report_dir / f"FULL_CARD_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                ReportBuilder.build_pdf(results, cfg, pdf_path)
                if pdf_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

            def on_error(msg):
                CustomMessageBox.critical(
                    self.parent,
                    "Ошибка",
                    f"Не удалось собрать данные для общего отчета:\n{msg}",
                )

            self.full_worker.finished.connect(on_finished)
            self.full_worker.error.connect(on_error)
            self.full_worker.start()
        except Exception as exc:
            CustomMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Ошибка при инициализации отчета: {exc}",
            )

