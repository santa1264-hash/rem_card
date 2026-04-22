def render_vitals(data, hours):
    html = '<div class="section">'
    html += '<table class="data-table" width="100%" align="center">'
    html += '<tr><th colspan="25" style="font-size: 12px; color: #2c3e50; padding: 5px; text-align: center; background-color: #f8f9fa;">ТАБЛИЦА ПОКАЗАТЕЛЕЙ</th></tr>'
    html += '<tr><th class="name-cell">Час</th>' + "".join(f'<th class="matrix-cell">{h}</th>' for h in hours) + '</tr>'
    
    v_matrix = data.get("vitals_matrix", {})
    settings = data.get("vital_settings", {'ad': 1, 'pulse': 1, 'temp': 1, 'spo2': 1, 'rr': 0, 'cvp': 0})
    
    # Жесткий порядок согласно настройкам
    indicators = [
        ("АД", "ad", settings.get('ad')),
        ("ЧСС", "hr", settings.get('pulse')),
        ("Темп", "temp", settings.get('temp')),
        ("ЧДД", "rr", settings.get('rr')),
        ("SpO2", "spo2", settings.get('spo2')),
        ("ЦВД", "cvp", settings.get('cvp'))
    ]
    
    for label, key, is_visible in indicators:
        if not is_visible: continue
        
        row = f'<tr><td class="name-cell">{label}</td>'
        for i in range(24):
            val = ""
            if key == "ad":
                sys = v_matrix.get(i, {}).get("sys", "")
                dia = v_matrix.get(i, {}).get("dia", "")
                if sys or dia: val = f"{sys}/{dia}"
            elif key == "cvp":
                cvp_val = v_matrix.get(i, {}).get("cvp", "")
                val = "Н/Н" if cvp_val == -1 else cvp_val
            else:
                val = v_matrix.get(i, {}).get(key, "")
            row += f'<td>{val}</td>'
        html += row + '</tr>'
    html += '</table></div>'
    return html
