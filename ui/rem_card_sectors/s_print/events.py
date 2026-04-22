def render_events(data):
    html = '<div class="section">'
    html += '<table class="data-table" width="100%">'
    html += '<tr><th colspan="3" style="font-size: 12px; color: #2c3e50; padding: 5px; text-align: center; background-color: #f8f9fa;">ЖУРНАЛ СОБЫТИЙ</th></tr>'
    html += '<tr><th class="event-time">Дата и Время</th><th class="event-status">Где / Статус</th><th class="event-desc">Комментарий</th></tr>'
    
    evs = data.get("events_struct", [])
    if not evs:
        html += '<tr><td colspan="3" style="padding:20px;">Нет событий за период</td></tr>'
    else:
        for ev in evs:
            html += f'<tr><td class="event-time">{ev["time"]}</td><td class="event-status">{ev["status"]}</td><td class="event-desc">{ev["desc"]}</td></tr>'
            
    html += '</table></div>'
    return html
