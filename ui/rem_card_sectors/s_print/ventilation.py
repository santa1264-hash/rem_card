def render_ventilation(data):
    html = '<div class="section ventilation-section">'
    html += '<table class="vent-table" width="100%">'
    html += '<thead>'
    html += (
        '<tr><th colspan="5" style="font-size: 12px; color: #2c3e50; padding: 5px; '
        'text-align: center; background-color: #f8f9fa;">ИСТОРИЯ СОБЫТИЙ ИВЛ</th></tr>'
    )
    html += (
        '<tr>'
        '<th class="vent-time">Время</th>'
        '<th class="vent-event">Событие</th>'
        '<th class="vent-mode">Режим</th>'
        '<th class="vent-params">Параметры</th>'
        '<th class="vent-indications">Показания</th>'
        '</tr>'
    )
    html += '</thead><tbody>'

    rows = data.get("ventilation_struct", [])
    if not rows:
        html += '<tr><td colspan="5" style="padding:12px;">Нет событий ИВЛ за период</td></tr>'
    else:
        for row in rows:
            html += (
                f'<tr>'
                f'<td class="vent-time">{row.get("time", "—")}</td>'
                f'<td class="vent-event">{row.get("event", "—")}</td>'
                f'<td class="vent-mode">{row.get("mode", "—")}</td>'
                f'<td class="vent-params">{row.get("params", "—")}</td>'
                f'<td class="vent-indications">{row.get("indications", "—")}</td>'
                f'</tr>'
            )

    html += '</tbody></table></div>'
    return html
