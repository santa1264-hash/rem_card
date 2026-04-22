# --- ЦЕНТРАЛЬНАЯ ТЕМА ПРИЛОЖЕНИЯ РЕМКАРТА ---
# Все цвета и стилистические параметры собраны здесь для удобства настройки через админку.

# --- ОБЩИЕ ЦВЕТА ФОНА ---
BG_MAIN = "#f8f9fa"             # Основной фон окон и секторов
BG_LIGHT = "#e9ecef"            # Светло-серый фон (заголовки, подложки)
BG_CARD = "#ffffff"             # Чисто белый фон для карточек и полей ввода
BG_ALT_ROW = "#fdfdfd"          # Цвет чередующихся строк в таблицах

# --- ЦВЕТА ТЕКСТА ---
TEXT_PRIMARY = "#2c3e50"        # Основной темный текст
TEXT_SECONDARY = "#495057"      # Вторичный серый текст
TEXT_MUTED = "#adb5bd"          # Приглушенный текст (disabled)
TEXT_ON_DARK = "#ffffff"        # Белый текст для темных кнопок

# --- СОСТОЯНИЯ И АКЦЕНТЫ ---
COLOR_PRIMARY = "#007bff"       # Основной синий цвет (активные элементы)
COLOR_PRIMARY_DARK = "#0056b3"  # Темно-синий (ховер, заголовки)
COLOR_SUCCESS = "#28a745"       # Зеленый (успех, сохранение, норма)
COLOR_SUCCESS_DARK = "#218838"  # Темно-зеленый
COLOR_DANGER = "#e74c3c"        # Красный (ошибки, удаление, тревога)
COLOR_WARNING = "#f39c12"       # Оранжевый (предупреждения)
COLOR_INFO = "#3498db"          # Голубой (инфо, шаблоны)
COLOR_SECONDARY = "#6c757d"     # Серый (кнопки "Назад", нейтральные действия)

# --- ГРАНИЦЫ И РАМКИ ---
BORDER_COLOR = "#bdc3c7"        # Основной цвет рамок секторов
BORDER_LIGHT = "#dee2e6"        # Светлая граница (разделители)
BORDER_WIDTH = "1.5px"          # Толщина основных рамок
BORDER_RADIUS_LG = "15px"       # Большой радиус скругления (сектора)
BORDER_RADIUS_MD = "8px"        # Средний радиус (кнопки, поля)
BORDER_RADIUS_SM = "4px"        # Малый радиус

# --- СПЕЦИФИЧЕСКИЕ ЦВЕТА ИНТЕРФЕЙСА ---
COLOR_BED_FREE = "#28a745"      # Цвет свободной койки
COLOR_BED_BUSY = "#dc3545"      # Цвет занятой койки
COLOR_CHART_GRID = "#e0e0e0"    # Сетка графика

# --- ЦВЕТА ЛЕГЕНДЫ И ГРАФИКОВ (Витальные функции) ---
# АД (Артериальное давление)
COLOR_VITAL_AD_LINE = "#e74c3c" 
COLOR_VITAL_AD_BG = "#ffdada"
# Пульс / ЧСС
COLOR_VITAL_PULSE = "#0000ff"
COLOR_VITAL_PULSE_BG = "#dadaff"
# ЧДД (Дыхание)
COLOR_VITAL_RESP = "#e67e22"
COLOR_VITAL_RESP_BG = "#fff0da"
# SpO2 (Насыщение)
COLOR_VITAL_SPO2 = "#03a9f4"
COLOR_VITAL_SPO2_BG = "#e1f5fe"
# Температура
COLOR_VITAL_TEMP = "#27ae60"
COLOR_VITAL_TEMP_BG = "#dafada"
# ЦВД
COLOR_VITAL_CVP = "#ed5cf7"
COLOR_VITAL_CVP_BG = "#f8c0fc"

# --- ЦВЕТА ЯЧЕЕК НАЗНАЧЕНИЙ ---
COLOR_CELL_CANCELLED = "#f08989" # Цвет отмененного назначения (Отм)
COLOR_CELL_DRAFT = "#7cf7ca"     # Цвет добавленного черновика (X)

# --- ЦВЕТА КНОПОК (Индивидуальные настройки из кода) ---
COLOR_BTN_SAVE = "#2ecc71"       # Кнопка СОХРАНИТЬ (ярко-зеленый)
COLOR_BTN_CLEAR = "#fab1a0"      # Кнопка ОЧИСТИТЬ (нежно-красный)
COLOR_BTN_BACK = "#007bff"       # Кнопка НАЗАД (синий)
COLOR_BTN_TPL_GEN = "#3498db"    # Кнопка Генерировать в шаблонах
COLOR_BTN_TPL_APPLY = "#27ae60"  # Кнопка Утвердить в шаблонах
COLOR_BTN_DICT_ORANGE = "#e67e22" # Оранжевые кнопки в справочниках

# --- КНОПКИ ВЕРХНЕЙ ПАНЕЛИ (СЕКТОР 8) ---
# Кнопка НАЗАД (Сектор 8)
COLOR_S8_BACK_BG = "#007bff"     # Цвет фона кнопки
COLOR_S8_BACK_TEXT = "#ffffff"   # Цвет текста (белый)

# Кнопка ЗАГЛУШКА (Сектор 8)
COLOR_S8_PLACEHOLDER_BG = "#e9ecef"   # Цвет фона кнопки
COLOR_S8_PLACEHOLDER_TEXT = "#95a5a6" # Цвет текста (серый)

# Кнопка НАСТРОЙКИ (Сектор 8)
COLOR_S8_SETTINGS_BG = "#007bff"      # Цвет фона кнопки
COLOR_S8_SETTINGS_TEXT = "#000000"    # Цвет текста (черный)

# Кнопка ВЫХОД (Сектор 8)
COLOR_S8_EXIT_BG = "#007bff"          # Цвет фона кнопки
COLOR_S8_EXIT_TEXT = "#000000"        # Цвет текста (черный)

# --- КНОПКИ ПАНЕЛИ УПРАВЛЕНИЯ (СЕКТОР 2а) ---
# Кнопка СОХРАНИТЬ
COLOR_S2_SAVE_BG = "#007bff"          # Цвет фона кнопки
COLOR_S2_SAVE_TEXT = "#000000"        # Цвет текста (черный)

# Кнопка ОЧИСТИТЬ ЛИСТ
COLOR_S2_CLEAN_SHEET_BG = "#007bff"   # Цвет фона кнопки
COLOR_S2_CLEAN_SHEET_TEXT = "#000000" # Цвет текста (черный)

# Кнопка ОЧИСТИТЬ НАЗНАЧЕНИЯ
COLOR_S2_CLEAR_BG = "#007bff"         # Цвет фона кнопки
COLOR_S2_CLEAR_TEXT = "#000000"       # Цвет текста (черный)

# Кнопка ВЧЕРАШНИЕ НАЗНАЧЕНИЯ
COLOR_S2_YESTERDAY_BG = "#007bff"     # Цвет фона кнопки
COLOR_S2_YESTERDAY_TEXT = "#000000"   # Цвет текста (черный)

# Кнопка ОТМЕНИТЬ ИЗМЕНЕНИЯ
COLOR_S2_ROLLBACK_BG = "#007bff"      # Цвет фона кнопки
COLOR_S2_ROLLBACK_TEXT = "#000000"    # Цвет текста (черный)

# --- КАСТОМНЫЕ ДИАЛОГОВЫЕ ОКНА (ПРЕДУПРЕЖДЕНИЯ, ОШИБКИ) ---
CUSTOM_DIALOG_RADIUS = "5px"
CUSTOM_DIALOG_BG = "#ffffff"
CUSTOM_DIALOG_TITLE_BG = "#e9ecef" # BG_LIGHT
CUSTOM_DIALOG_TITLE_TEXT = "#2c3e50"
CUSTOM_DIALOG_BORDER = "#bdc3c7"

# --- ГЛОБАЛЬНЫЙ QSS СТИЛЬ ---
GLOBAL_STYLE = f"""
QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 14px;
}}

QMainWindow, QDialog {{
    background-color: {BG_MAIN};
}}

/* Подсказки - форсированный стиль для читаемости */
QToolTip {{
    background-color: #ffffff !important;
    color: #2c3e50 !important;
    border: 1px solid #bdc3c7 !important;
    padding: 5px !important;
    font-size: 13px !important;
}}

/* Поля ввода */
QLineEdit, QDateEdit, QDateTimeEdit, QComboBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_LIGHT};
    border-radius: {BORDER_RADIUS_SM};
    padding: 5px;
    color: {TEXT_PRIMARY};
}}

QLineEdit:focus, QDateEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
    border: 2px solid {BORDER_COLOR};
}}

/* Кнопки */
QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: {TEXT_ON_DARK};
    border: none;
    border-radius: {BORDER_RADIUS_MD};
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY_DARK};
}}

QPushButton:disabled {{
    background-color: {TEXT_MUTED};
    color: {BG_LIGHT};
}}

QDialog QPushButton, QMessageBox QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: white;
    padding: 6px 12px;
    min-width: 90px;
    border: 1px solid {COLOR_PRIMARY_DARK};
    border-radius: {BORDER_RADIUS_SM};
    font-weight: bold;
}}

/* Фикс для QMessageBox и стандартных диалогов, чтобы кнопки были в едином стиле */
QMessageBox QPushButton, QDialogButtonBox QPushButton {{
    color: white !important;
    background-color: {COLOR_PRIMARY} !important;
    border: none !important;
    border-radius: {BORDER_RADIUS_MD} !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    min-width: 90px !important;
}}

QDialog QPushButton:hover, QMessageBox QPushButton:hover {{
    background-color: {COLOR_PRIMARY_DARK} !important;
}}

/* Стиль самого бокса сообщения */
QMessageBox {{
    background-color: white !important;
}}

QMessageBox QLabel {{
    color: #2c3e50 !important;
    background-color: transparent !important;
    font-size: 15px !important;
    font-weight: bold !important;
}}

/* Таблицы */
QTableView, QTableWidget {{
    background-color: {BG_CARD};
    alternate-background-color: {BG_ALT_ROW};
    border: 1px solid {BORDER_COLOR};
    gridline-color: {BORDER_LIGHT};
}}

QHeaderView::section {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
    padding: 6px;
    border: none;
    border-right: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    font-weight: bold;
}}

/* Кастомный стиль кнопок предупреждений (бежевый, рамка, темный текст) */
QPushButton#DialogOkBtn {{
    background-color: {BG_LIGHT} !important;
    color: {TEXT_PRIMARY} !important;
    font-size: 13px !important;
    font-weight: bold !important;
    padding: 6px 20px !important;
    border: 1px solid {CUSTOM_DIALOG_BORDER} !important;
    border-radius: {CUSTOM_DIALOG_RADIUS} !important;
}}
QPushButton#DialogOkBtn:hover {{
    background-color: #d8dde2 !important;
}}
QPushButton#DialogOkBtn:disabled {{
    background-color: #f8f9fa !important;
    color: #adb5bd !important;
}}

/* СТИЛИ ГЛАВНОГО ЗАГОЛОВКА ПРИЛОЖЕНИЯ */
QFrame#MainTitleBar {{
    background-color: {CUSTOM_DIALOG_TITLE_BG} !important;
    border-bottom: 1px solid {CUSTOM_DIALOG_BORDER} !important;
    border-top-left-radius: {CUSTOM_DIALOG_RADIUS} !important;
    border-top-right-radius: {CUSTOM_DIALOG_RADIUS} !important;
}}
QLabel#MainTitleText {{
    color: {CUSTOM_DIALOG_TITLE_TEXT} !important;
    font-weight: bold !important;
    font-size: 14px !important;
    background-color: transparent !important;
}}
QPushButton#TitleControlBtn {{
    background-color: transparent !important;
    color: {CUSTOM_DIALOG_TITLE_TEXT} !important;
    font-weight: bold !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 0px !important;
    min-width: 40px !important;
    margin: 2px 1px !important;
}}
QPushButton#TitleControlBtn:hover {{
    background-color: rgba(0, 0, 0, 0.1) !important;
}}
QPushButton#TitleCloseBtn {{
    background-color: transparent !important;
    color: {CUSTOM_DIALOG_TITLE_TEXT} !important;
    font-weight: bold !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 0px !important;
    min-width: 40px !important;
    margin: 2px 1px !important;
}}
QPushButton#TitleCloseBtn:hover {{
    background-color: #e74c3c !important;
    color: white !important;
}}
"""

STYLE_CUSTOM_DIALOG = f"""
    QDialog {{
        background-color: transparent;
    }}
    QFrame#DialogMainFrame {{
        background-color: {CUSTOM_DIALOG_BG};
        border: 1px solid {CUSTOM_DIALOG_BORDER};
        border-radius: {CUSTOM_DIALOG_RADIUS};
    }}
    QFrame#DialogTitleBar {{
        background-color: {CUSTOM_DIALOG_TITLE_BG};
        border-top-left-radius: {CUSTOM_DIALOG_RADIUS};
        border-top-right-radius: {CUSTOM_DIALOG_RADIUS};
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
        border-bottom: 1px solid {CUSTOM_DIALOG_BORDER};
    }}
    QLabel#DialogTitleText {{
        color: {CUSTOM_DIALOG_TITLE_TEXT};
        font-weight: bold;
        font-size: 14px;
        padding-left: 5px;
        background-color: transparent;
    }}
    QPushButton#DialogCloseBtn {{
        background-color: transparent;
        color: {CUSTOM_DIALOG_TITLE_TEXT};
        font-weight: bold;
        font-size: 14px;
        border: none;
        padding: 2px 10px;
        border-top-right-radius: {CUSTOM_DIALOG_RADIUS};
    }}
    QPushButton#DialogCloseBtn:hover {{
        background-color: #e74c3c;
        color: white;
    }}
    QLabel#DialogMessageText {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: bold;
        background-color: transparent;
    }}
    QPushButton#DialogOkBtn {{
        background-color: {BG_LIGHT};
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: bold;
        padding: 6px 20px;
        border: 1px solid {CUSTOM_DIALOG_BORDER};
        border-radius: {CUSTOM_DIALOG_RADIUS};
    }}
    QPushButton#DialogOkBtn:hover {{
        background-color: #d8dde2;
    }}
"""

def get_bed_style(is_occupied: bool) -> str:
    color = COLOR_BED_BUSY if is_occupied else COLOR_BED_FREE
    return f"""
        QFrame {{
            background-color: {BG_CARD};
            border-radius: 12px;
            border: 2px solid {color};
        }}
        QLabel {{
            color: {TEXT_PRIMARY};
            background: transparent;
        }}
    """
