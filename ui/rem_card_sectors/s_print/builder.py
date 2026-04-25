import os
import pathlib
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF

from .header import render_header
from .vitals import render_vitals
from .prescriptions import render_prescriptions
from .balance import render_balance
from .events import render_events
from .ventilation import render_ventilation

class ReportBuilder:
    @staticmethod
    def build_pdf(data, config, output_path):
        if isinstance(data, list):
            # Общий отчет за несколько дней
            html_content = ReportBuilder._build_multiple_days_html(data, config)
        else:
            # Отчет за одни сутки
            html_content = ReportBuilder._build_single_day_html(data, config)
            
        doc = QTextDocument()
        doc.setHtml(html_content)
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(output_path))
        
        layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Landscape, QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter)
        printer.setPageLayout(layout)
        
        doc.setDocumentMargin(0)
        rect_pts = layout.paintRect(QPageLayout.Point)
        doc.setTextWidth(rect_pts.width())
        doc.setPageSize(rect_pts.size())
        
        doc.print_(printer)

    @staticmethod
    def _get_css():
        return """
        <style>
            body {
                font-family: Arial;
                font-size: 10pt;
                margin: 0;
                padding: 0;
            }

            .section {
                width: 100%;
                margin-bottom: 10px;
                page-break-inside: avoid;
            }

            table.data-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                page-break-inside: auto;
            }

            table.data-table th, table.data-table td {
                border: 1px solid #999;
                padding: 1px;
                text-align: center;
                vertical-align: middle;
                font-size: 6pt;
                font-family: "Arial Narrow", Arial, sans-serif;
            }

            .name-cell {
                width: 16%;
                text-align: left;
            }

            .matrix-cell {
                width: 3.5%;
            }

            .prescription-mark-icon {
                width: 10px;
                height: 10px;
                vertical-align: middle;
            }

            .prescription-mark-icon-mini {
                width: 7px;
                height: 7px;
                vertical-align: middle;
            }

            .prescription-body-mark {
                white-space: nowrap;
            }

            .prescription-planned-mark {
                font-size: 8pt;
                color: #555;
                vertical-align: middle;
            }

            .prescription-arrow {
                font-size: 7pt;
                vertical-align: middle;
            }

            .event-time { width: 25%; white-space: nowrap; }
            .event-status { width: 20%; }
            .event-desc { width: 55%; text-align: left; }

            h1 { font-size: 14px; text-align: center; margin: 0 0 2px 0; }
            h2 { font-size: 12px; color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 1px; margin: 5px 0 2px 0; text-align: center; }
            .header-info { text-align: center; margin-bottom: 5px; font-size: 9pt; line-height: 1.1; }
            
            .day-container {
                width: 100%;
            }

            .ventilation-section {
                width: 100%;
                page-break-inside: auto;
            }
            table.vent-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                page-break-inside: auto;
            }
            table.vent-table thead {
                display: table-header-group;
            }
            table.vent-table th, table.vent-table td {
                border: 1px solid #999;
                padding: 2px 3px;
                text-align: center;
                font-size: 7pt;
                font-family: "Arial Narrow", Arial, sans-serif;
            }
            .vent-time { width: 20%; white-space: nowrap; }
            .vent-event { width: 16%; }
            .vent-mode { width: 16%; }
            .vent-params { width: 24%; text-align: left; }
            .vent-indications { width: 24%; text-align: left; }
        </style>
        """

    @staticmethod
    def _build_single_day_html(data, config):
        hours = [str((8+i)%24) for i in range(24)]
        start_str = data["start_dt"].strftime("%d.%m.%Y %H:%M")
        end_str = data["end_dt"].strftime("%d.%m.%Y %H:%M")
        
        html_body = ""
        if config.get("vitals", True): html_body += render_vitals(data, hours)
        if config.get("prescriptions", True): html_body += render_prescriptions(data, hours)
        if config.get("balance", True): html_body += render_balance(data, hours)
        if config.get("events", True): html_body += render_events(data)
        if config.get("ventilation", False): html_body += render_ventilation(data)

        return f"""<html><head>{ReportBuilder._get_css()}</head><body>
        <div style="width: 830pt;">
            {render_header(data, start_str, end_str)}
            {html_body}
        </div>
        </body></html>
        """

    @staticmethod
    def _build_multiple_days_html(results, config):
        hours = [str((8+i)%24) for i in range(24)]
        
        days_html = []
        for i, data in enumerate(results):
            start_str = data["start_dt"].strftime("%d.%m.%Y %H:%M")
            end_str = data["end_dt"].strftime("%d.%m.%Y %H:%M")
            
            html_body = ""
            if config.get("vitals", True): html_body += render_vitals(data, hours)
            if config.get("prescriptions", True): html_body += render_prescriptions(data, hours)
            if config.get("balance", True): html_body += render_balance(data, hours)
            if config.get("events", True): html_body += render_events(data)
            if config.get("ventilation", False): html_body += render_ventilation(data)

            # Добавляем разрыв страницы ПЕРЕД каждым днем, кроме первого
            page_style = 'style="page-break-before: always;"' if i > 0 else ""
            
            day_content = f"""
            <div class="day-container" {page_style}>
                <div style="width: 830pt;">
                    {render_header(data, start_str, end_str)}
                    {html_body}
                </div>
            </div>
            """
            days_html.append(day_content)

        return f"""<html><head>{ReportBuilder._get_css()}</head><body>
            {"".join(days_html)}
        </body></html>
        """
