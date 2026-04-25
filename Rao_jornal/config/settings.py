import os
from rem_card.app.paths import BAZA_DIR, BAZA_LOGS_DIR, ensure_directories, get_base_dir, get_resources_dir, get_icon_dir

# 1. Основные корни
PROJECT_ROOT = get_base_dir()        # Корень данных (Project)
RESOURCES_ROOT = get_resources_dir() # Корень ресурсов (внутри EXE или Project)

# 2. Директории ресурсов
# Путь к Журналу внутри ресурсов
BASE_DIR = os.path.join(RESOURCES_ROOT, "rem_card", "Rao_jornal")

ICONS_DIR = get_icon_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
MKB_DB_PATH = os.path.join(BASE_DIR, "mkb", "mkb10.db")

# 3. Директории данных (архив, логи, бэкапы) - они ВСЕГДА ВНЕ EXE
APP_DATA_DIR = BAZA_DIR

DATABASE_DIR = os.path.join(APP_DATA_DIR, 'database')
ARCHIVE_DIR = os.path.join(APP_DATA_DIR, 'archiv')
LOG_DIR = BAZA_LOGS_DIR
BACKUP_DIR = os.path.join(APP_DATA_DIR, 'backups')
REPORT_DIR = os.path.join(APP_DATA_DIR, 'report')

if os.environ.get("RAO_DEBUG_PATHS") == "1":
    print(f"DEBUG: PROJECT_ROOT = {PROJECT_ROOT}")
    print(f"DEBUG: RESOURCES_ROOT = {RESOURCES_ROOT}")
    print(f"DEBUG: APP_DATA_DIR = {APP_DATA_DIR}")
    print(f"DEBUG: BASE_DIR = {BASE_DIR}")

ensure_directories()

LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Настройки
MAX_BACKUPS = 5
BACKUP_INTERVAL = 10
NUM_BEDS = 12
