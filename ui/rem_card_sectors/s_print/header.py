def render_header(data, start_str, end_str):
    diag = data.get('diagnosis', '—')
    return f"""
    <div class="header-info">
        <h1>РЕАНИМАЦИОННАЯ КАРТА</h1>
        <strong>Пациент:</strong> {data['patient_name']} &nbsp;&nbsp; 
        <strong>Диагноз:</strong> <span style="display:inline-block; max-width:400px; vertical-align:top;">{diag}</span><br>
        <strong>Сутки в РАО:</strong> {data['icu_day']} &nbsp;&nbsp; 
        <strong>Период:</strong> {start_str} - {end_str}
    </div>
    """