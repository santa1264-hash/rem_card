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
    HORIZONTAL_MARGIN_MM = 7
    VERTICAL_MARGIN_MM = 15
    TABLE_WIDTH_GUARD_PT = 0

    @staticmethod
    def build_pdf(data, config, output_path):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(output_path))

        layout = QPageLayout(
            QPageSize(QPageSize.A4),
            QPageLayout.Landscape,
            QMarginsF(
                ReportBuilder.HORIZONTAL_MARGIN_MM,
                ReportBuilder.VERTICAL_MARGIN_MM,
                ReportBuilder.HORIZONTAL_MARGIN_MM,
                ReportBuilder.VERTICAL_MARGIN_MM,
            ),
            QPageLayout.Millimeter,
        )
        printer.setPageLayout(layout)
        rect_pts = layout.paintRect(QPageLayout.Point)
        table_width_pt = max(1, int(rect_pts.width()) - ReportBuilder.TABLE_WIDTH_GUARD_PT)

        if isinstance(data, list):
            # Общий отчет за несколько дней
            html_content = ReportBuilder._build_multiple_days_html(data, config, table_width_pt)
        else:
            # Отчет за одни сутки
            html_content = ReportBuilder._build_single_day_html(data, config, table_width_pt)
            
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setTextWidth(rect_pts.width())
        doc.setPageSize(rect_pts.size())
        doc.setHtml(html_content)
        
        doc.print_(printer)

    @staticmethod
    def _get_css(table_width_pt):
        table_width = f"{float(table_width_pt):.2f}pt"
        css = """
        <style>
            body {
                font-family: Arial;
                font-size: 10pt;
                margin: 0;
                padding: 0;
            }

            .section {
                width: __TABLE_WIDTH__;
                margin-bottom: 0;
                padding: 0;
            }

            .section-gap {
                height: 5px;
                line-height: 5px;
                font-size: 1px;
            }

            .report-page {
                width: __TABLE_WIDTH__;
                margin: 0;
                padding: 0;
            }

            table.report-table {
                width: __TABLE_WIDTH__;
                border-collapse: collapse;
                table-layout: fixed;
                margin-left: 0;
                margin-right: 0;
                max-width: __TABLE_WIDTH__;
                min-width: __TABLE_WIDTH__;
            }

            .section-avoid {
                page-break-inside: avoid;
                break-inside: avoid;
            }

            .prescriptions-section {
                page-break-inside: auto;
                break-inside: auto;
            }

            table.data-table {
                width: __TABLE_WIDTH__;
                border-collapse: collapse;
                table-layout: fixed;
                page-break-inside: auto;
            }

            .section-avoid table {
                page-break-inside: avoid;
                break-inside: avoid;
            }

            table.data-table thead {
                display: table-header-group;
                page-break-inside: avoid;
                page-break-after: avoid;
                break-inside: avoid;
                break-after: avoid;
            }

            table.prescriptions-table {
                page-break-inside: auto;
                break-inside: auto;
            }

            table.prescriptions-table tr {
                page-break-inside: avoid;
                break-inside: avoid;
            }

            table.data-table th, table.data-table td {
                border: 1px solid #999;
                padding: 1px;
                text-align: center;
                vertical-align: middle;
                font-size: 6pt;
                font-family: "Arial Narrow", Arial, sans-serif;
            }

            table.data-table .table-title-row th {
                font-size: 12px;
                color: #2c3e50;
                padding: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }

            .table-title-row {
                page-break-after: avoid;
                break-after: avoid;
            }

            .name-cell {
                text-align: left;
            }

            .vitals-section table.data-table th,
            .vitals-section table.data-table td {
                padding-left: 0;
                padding-right: 0;
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
            .print-header {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                margin-bottom: 5px;
            }
            table.print-header td {
                border: none;
                padding: 0;
                font-size: 9pt;
                line-height: 1.15;
                vertical-align: middle;
            }
            table.print-header td.print-header-details {
                width: 68%;
                text-align: left;
            }
            table.print-header td.print-header-title {
                width: 32%;
                text-align: center;
                font-size: 13px;
                font-weight: bold;
                white-space: nowrap;
            }

            .balance-summary {
                text-align: left;
                font-size: 11pt;
                font-weight: bold;
                margin-top: 5px;
                margin-bottom: 0;
                margin-left: 1%;
            }
            
            .day-container {
                width: __TABLE_WIDTH__;
            }

            .ventilation-section {
                width: __TABLE_WIDTH__;
                page-break-inside: avoid;
                break-inside: avoid;
            }
            table.vent-table {
                width: __TABLE_WIDTH__;
                border-collapse: collapse;
                table-layout: fixed;
                page-break-inside: avoid;
                break-inside: avoid;
            }
            table.vent-table thead {
                display: table-header-group;
                page-break-inside: avoid;
                page-break-after: avoid;
                break-inside: avoid;
                break-after: avoid;
            }
            table.vent-table th, table.vent-table td {
                border: 1px solid #999;
                padding: 2px 3px;
                text-align: center;
                font-size: 7pt;
                font-family: "Arial Narrow", Arial, sans-serif;
            }
            table.vent-table .table-title-row th {
                font-size: 12px;
                color: #2c3e50;
                padding: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }
            .vent-time { width: 20%; white-space: nowrap; }
            .vent-event { width: 16%; }
            .vent-mode { width: 16%; }
            .vent-params { width: 24%; text-align: left; }
            .vent-indications { width: 24%; text-align: left; }
        </style>
        """
        return css.replace("__TABLE_WIDTH__", table_width)

    @staticmethod
    def _build_day_body(data, config, hours, table_width_pt):
        sections = []
        if config.get("vitals", True): sections.append(render_vitals(data, hours, table_width_pt))
        if config.get("prescriptions", True): sections.append(render_prescriptions(data, hours, table_width_pt))
        if config.get("balance", True): sections.append(render_balance(data, hours, table_width_pt))
        if config.get("ventilation", False): sections.append(render_ventilation(data, table_width_pt))
        if config.get("events", True): sections.append(render_events(data, table_width_pt))
        visible_sections = [section for section in sections if section]
        return '<div class="section-gap">&nbsp;</div>'.join(visible_sections)

    @staticmethod
    def _build_single_day_html(data, config, table_width_pt):
        hours = [str((8+i)%24) for i in range(24)]
        start_str = data["start_dt"].strftime("%d.%m.%Y %H:%M")
        end_str = data["end_dt"].strftime("%d.%m.%Y %H:%M")

        html_body = ReportBuilder._build_day_body(data, config, hours, table_width_pt)

        return f"""<html><head>{ReportBuilder._get_css(table_width_pt)}</head><body>
        <div class="report-page">
            {render_header(data, start_str, end_str)}
            {html_body}
        </div>
        </body></html>
        """

    @staticmethod
    def _build_multiple_days_html(results, config, table_width_pt):
        hours = [str((8+i)%24) for i in range(24)]

        days_html = []
        for i, data in enumerate(results):
            start_str = data["start_dt"].strftime("%d.%m.%Y %H:%M")
            end_str = data["end_dt"].strftime("%d.%m.%Y %H:%M")

            html_body = ReportBuilder._build_day_body(data, config, hours, table_width_pt)

            # Добавляем разрыв страницы ПЕРЕД каждым днем, кроме первого
            page_style = 'style="page-break-before: always;"' if i > 0 else ""

            day_content = f"""
            <div class="day-container" {page_style}>
                <div class="report-page">
                    {render_header(data, start_str, end_str)}
                    {html_body}
                </div>
            </div>
            """
            days_html.append(day_content)

        return f"""<html><head>{ReportBuilder._get_css(table_width_pt)}</head><body>
            {"".join(days_html)}
        </body></html>
        """
