from .table_layout import (
    cell_attrs,
    cell_content,
    colspan_cell_attrs,
    hourly_widths,
    render_hourly_colgroup,
    table_width_attrs,
)

BALANCE_NAME_WIDTH_PT = 120.0


def _format_hourly_value(value):
    if value:
        return str(int(round(float(value))))
    return ""


def _render_hourly_balance_table(title, rows, hourly_data, hours, table_width_pt, name_width, matrix_widths):
    html = f'<table class="report-table data-table" {table_width_attrs(table_width_pt)}>'
    html += render_hourly_colgroup(table_width_pt, BALANCE_NAME_WIDTH_PT)
    html += '<thead>'
    html += f'<tr class="table-title-row"><th colspan="25" {colspan_cell_attrs()}>{title}</th></tr>'
    html += f'<tr><th class="name-cell" {cell_attrs(name_width, "text-align: left;")}>Тип</th>'
    html += "".join(f'<th class="matrix-cell" {cell_attrs(matrix_widths[i])}>{h}</th>' for i, h in enumerate(hours))
    html += '</tr>'
    html += '</thead><tbody>'
    for label, key in rows:
        row = f'<tr><td class="name-cell" {cell_attrs(name_width, "text-align: left;")}>{label}</td>'
        for i in range(24):
            val = _format_hourly_value(hourly_data.get(i, {}).get(key, ""))
            row += f'<td class="matrix-cell" {cell_attrs(matrix_widths[i])}>{cell_content(val)}</td>'
        html += row + '</tr>'
    html += '</tbody></table>'
    return html


def render_balance(data, hours, table_width_pt):
    col_widths = hourly_widths(table_width_pt, BALANCE_NAME_WIDTH_PT)
    name_width = col_widths[0]
    matrix_widths = col_widths[1:]

    bf = data.get("balance_final", {})
    out_hourly = bf.get("out_hourly", {})
    in_hourly = bf.get("in_hourly", {})
    
    out_rows = [("Диурез", "urine"), ("Дренажи", "drain"), ("ЖКТ (зонд)", "ng"), ("Рвота", "stool"), ("Другое", "other")]
    in_rows = [("Инфузия", "infusion"), ("Препараты", "preparats"), ("Кровь", "blood"), ("Плазма", "plasma"), ("Перорально", "oral")]

    html = '<div class="section section-avoid balance-section">'
    html += _render_hourly_balance_table(
        "ПОЧАСОВОЕ ВЫВЕДЕНИЕ", out_rows, out_hourly, hours, table_width_pt, name_width, matrix_widths
    )
    html += _render_hourly_balance_table(
        "ПОЧАСОВОЕ ВВЕДЕНИЕ", in_rows, in_hourly, hours, table_width_pt, name_width, matrix_widths
    )

    # Подсчет гидробаланса
    # Используем данные на текущий час ("current" и "out_cur") вместо полных суток
    cur_bal = bf.get("current", {})
    cur_bal_data = cur_bal.get("daily", cur_bal) if isinstance(cur_bal, dict) else {}
    out_cur = bf.get("out_cur", {})
    
    total_in = int(cur_bal_data.get("total", 0) if cur_bal_data.get("total") is not None else 0)
    total_out = int(sum(out_cur.values()))
    net_balance = total_in - total_out
    
    html += f'<div class="balance-summary">'
    html += f'Гидробаланс: Введено на текущий час ({total_in} мл) - Выведено на текущий час ({total_out} мл) = {net_balance} мл'
    html += '</div></div>'
    
    return html
