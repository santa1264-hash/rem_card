from .table_layout import (
    cell_attrs,
    cell_content,
    colspan_cell_attrs,
    hourly_widths,
    render_hourly_colgroup,
    table_width_attrs,
)

BALANCE_NAME_WIDTH_PT = 120.0


def render_balance(data, hours, table_width_pt):
    col_widths = hourly_widths(table_width_pt, BALANCE_NAME_WIDTH_PT)
    name_width = col_widths[0]
    matrix_widths = col_widths[1:]

    bf = data.get("balance_final", {})
    out_hourly = bf.get("out_hourly", {})
    
    html = f'<div class="section section-avoid balance-section"><table class="report-table data-table" {table_width_attrs(table_width_pt)}>'
    html += render_hourly_colgroup(table_width_pt, BALANCE_NAME_WIDTH_PT)
    html += '<thead>'
    html += f'<tr class="table-title-row"><th colspan="25" {colspan_cell_attrs()}>ПОЧАСОВОЕ ВЫВЕДЕНИЕ</th></tr>'
    html += f'<tr><th class="name-cell" {cell_attrs(name_width, "text-align: left;")}>Тип</th>'
    html += "".join(f'<th class="matrix-cell" {cell_attrs(matrix_widths[i])}>{h}</th>' for i, h in enumerate(hours))
    html += '</tr>'
    html += '</thead><tbody>'
    for lab, k in [("Диурез", "urine"), ("Дренажи", "drain"), ("ЖКТ (зонд)", "ng"), ("Рвота", "stool"), ("Другое", "other")]:
        row = f'<tr><td class="name-cell" {cell_attrs(name_width, "text-align: left;")}>{lab}</td>'
        for i in range(24):
            val = out_hourly.get(i, {}).get(k, "")
            if val:
                val = str(int(round(float(val))))
            else:
                val = ""
            row += f'<td class="matrix-cell" {cell_attrs(matrix_widths[i])}>{cell_content(val)}</td>'
        html += row + '</tr>'
    html += '</tbody></table>'

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
