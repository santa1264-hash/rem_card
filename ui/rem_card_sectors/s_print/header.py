from html import escape


def render_header(data, start_str, end_str):
    patient_name = escape(str(data.get("patient_name", "—")))
    diagnosis = escape(str(data.get("diagnosis", "—")))
    icu_day = escape(str(data.get("icu_day", "—")))
    start_label = escape(str(start_str))
    end_label = escape(str(end_str))

    return f"""
    <table class="print-header" width="100%">
        <tr>
            <td class="print-header-details">
                <div><strong>Пациент:</strong> {patient_name} &nbsp;&nbsp; <strong>Диагноз:</strong> {diagnosis}</div>
                <div><strong>Сутки в РАО:</strong> {icu_day} &nbsp;&nbsp; <strong>Период:</strong> {start_label} - {end_label}</div>
            </td>
            <td class="print-header-title">РЕАНИМАЦИОННАЯ КАРТА</td>
        </tr>
    </table>
    """
