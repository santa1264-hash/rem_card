def render_balance(data, hours):
    bf = data.get("balance_final", {})
    out_hourly = bf.get("out_hourly", {})
    
    html = '<div class="section"><table class="data-table" width="100%" align="center">'
    html += '<tr><th colspan="25" style="font-size: 12px; color: #2c3e50; padding: 5px; text-align: center; background-color: #f8f9fa;">ПОЧАСОВОЕ ВЫВЕДЕНИЕ</th></tr>'
    html += '<tr><th class="name-cell">Тип</th>' + "".join(f'<th class="matrix-cell">{h}</th>' for h in hours) + '</tr>'
    for lab, k in [("Диурез", "urine"), ("Дренажи", "drain"), ("ЖКТ (зонд)", "ng"), ("Рвота", "stool"), ("Другое", "other")]:
        row = f'<tr><td class="name-cell">{lab}</td>'
        for i in range(24):
            val = out_hourly.get(i, {}).get(k, "")
            if val:
                val = str(int(round(float(val))))
            else:
                val = ""
            row += f'<td>{val}</td>'
        html += row + '</tr>'
    html += '</table></div>'

    # Подсчет гидробаланса
    # Используем данные на текущий час ("current" и "out_cur") вместо полных суток
    cur_bal = bf.get("current", {})
    cur_bal_data = cur_bal.get("daily", cur_bal) if isinstance(cur_bal, dict) else {}
    out_cur = bf.get("out_cur", {})
    
    total_in = int(cur_bal_data.get("total", 0) if cur_bal_data.get("total") is not None else 0)
    total_out = int(sum(out_cur.values()))
    net_balance = total_in - total_out
    
    html += f'<div style="text-align: left; font-size: 11pt; font-weight: bold; margin-top: 15px; margin-bottom: 10px; margin-left: 1%;">'
    html += f'Гидробаланс: Введено на текущий час ({total_in} мл) - Выведено на текущий час ({total_out} мл) = {net_balance} мл'
    html += '</div>'
    
    return html
