import os
import sys

def is_compiled() -> bool:
    """Проверяет, запущено ли приложение в скомпилированном виде (PyInstaller/Nuitka)."""
    if getattr(sys, 'frozen', False):
        return True
    if "__compiled__" in globals():
        return True
    exe_name = os.path.basename(sys.executable).lower()
    if exe_name not in ('python.exe', 'pythonw.exe'):
        return True
    return False

def get_resources_dir() -> str:
    """
    Универсальное определение корня ресурсов:
    - PyInstaller onefile → _MEIPASS
    - PyInstaller onedir → _internal
    - Nuitka → папка exe
    - dev → корень проекта
    """
    import os
    import sys

    # PyInstaller onefile
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS

    # Любая compiled версия (PyInstaller onedir + Nuitka)
    if getattr(sys, 'frozen', False) or "__compiled__" in globals():
        base = os.path.dirname(os.path.abspath(sys.executable))

        # 🔴 PyInstaller onedir кладёт ресурсы в _internal
        internal = os.path.join(base, "_internal")
        if os.path.exists(internal):
            return internal

        # Nuitka (ресурсы рядом с exe)
        return base

    # dev режим
    return get_base_dir()
    
def get_base_dir() -> str:
    """
    Определяет корневую сетевую папку (Project) в зависимости от того,
    как запущена программа (скомпилирована или из исходников).
    """
    if is_compiled():
        exe_dir = os.path.dirname(sys.executable)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller: Baza_rao3_jurnal/Prog/app.exe (поднимаемся на 2 уровня к Project)
            return os.path.abspath(os.path.join(exe_dir, "..", ".."))
        else:
            # Nuitka: Baza_rao3_jurnal/Prog/launcher.dist/launcher.exe (поднимаемся на 3 уровня к Project)
            return os.path.abspath(os.path.join(exe_dir, "..", "..", ".."))
    else:
        # исходники: rem_card/app/paths.py -> app -> rem_card -> Project
        # os.path.dirname(__file__) == C:\Project\rem_card\app
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def get_seed_dir() -> str:
    if is_compiled():
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, "rem_card", "data", "dictionaries")
        else:
            return os.path.join(os.path.dirname(sys.executable), "rem_card", "data", "dictionaries")
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "dictionaries"))

def get_icon_dir() -> str:
    if is_compiled():
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, "rem_card", "icon")
        else:
            return os.path.join(os.path.dirname(sys.executable), "rem_card", "icon")
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icon"))

def get_user_dict_dir() -> str:
    return get_seed_dir()

NETWORK_ROOT = get_base_dir()
if os.path.basename(NETWORK_ROOT) == "Baza_rao3_jurnal":
    BAZA_DIR = NETWORK_ROOT
else:
    BAZA_DIR = os.path.join(NETWORK_ROOT, "Baza_rao3_jurnal")

LOGS_DIR = os.path.join(BAZA_DIR, "logs")
ARCHIV_DIR = os.path.join(BAZA_DIR, "archiv")
REM_CARD_DIR = os.path.join(BAZA_DIR, "rem_card")
REPORT_DIR = os.path.join(BAZA_DIR, "report")
BACKUPS_RC_DIR = os.path.join(BAZA_DIR, "backups")
CORRUPTED_DB_DIR = os.path.join(BAZA_DIR, "corrupted_db")
BACKUP_HEALTH_DIR = os.path.join(BAZA_DIR, "backup_health")
BACKUP_VALIDATION_REPORTS_DIR = os.path.join(BACKUP_HEALTH_DIR, "reports")
INVALID_BACKUPS_DIR = os.path.join(BACKUP_HEALTH_DIR, "invalid_backups")
ROLE_LOCKS_DIR = os.path.join(BAZA_DIR, "session_locks")
DB_CYCLE_ARCHIVE_DIR = os.path.join(ARCHIV_DIR, "db_cycle_archive")

SEED_DIR = get_seed_dir()
USER_DICT_DIR = get_user_dict_dir()

# Пути к базам данных и координации записи
JOURNAL_DB_PATH = os.path.join(ARCHIV_DIR, "rao_journal.db")
REMCARD_DB_PATH = JOURNAL_DB_PATH
LEGACY_REMCARD_DB_PATH = os.path.join(REM_CARD_DIR, "rem_cards_data.db")
DB_LOCK_PATH = os.path.join(ARCHIV_DIR, "db.lock")
DB_ROTATION_LOCK_PATH = os.path.join(ARCHIV_DIR, "db_rotation.lock")

LOCAL_APPDATA = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
LOCAL_CACHE_DIR = os.path.join(LOCAL_APPDATA, "RemCard", "cache")
LOCAL_CACHE_SUFFIX = str(
    os.environ.get("REMCARD_LOCAL_CACHE_SUFFIX")
    or f"{os.getpid()}"
).strip()
LOCAL_REMCARD_REPLICA_PATH = os.path.join(LOCAL_CACHE_DIR, f"rao_journal_local_replica_{LOCAL_CACHE_SUFFIX}.db")
LOCAL_JOURNAL_REPLICA_PATH = os.path.join(LOCAL_CACHE_DIR, f"rao_journal_local_replica_journal_{LOCAL_CACHE_SUFFIX}.db")
LOCAL_REMCARD_OUTBOX_PATH = os.path.join(LOCAL_CACHE_DIR, f"remcard_outbox_{LOCAL_CACHE_SUFFIX}.db")
LOCAL_JOURNAL_OUTBOX_PATH = os.path.join(LOCAL_CACHE_DIR, f"journal_outbox_{LOCAL_CACHE_SUFFIX}.db")

def get_role_lock_path(role: str) -> str:
    safe_role = str(role or "unknown").lower()
    return os.path.join(ROLE_LOCKS_DIR, f"{safe_role}.lock")

# Убедимся, что папки существуют
def ensure_directories():
    os.makedirs(BAZA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(ARCHIV_DIR, exist_ok=True)
    os.makedirs(REM_CARD_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(BACKUPS_RC_DIR, exist_ok=True)
    os.makedirs(CORRUPTED_DB_DIR, exist_ok=True)
    os.makedirs(BACKUP_HEALTH_DIR, exist_ok=True)
    os.makedirs(BACKUP_VALIDATION_REPORTS_DIR, exist_ok=True)
    os.makedirs(INVALID_BACKUPS_DIR, exist_ok=True)
    os.makedirs(ROLE_LOCKS_DIR, exist_ok=True)
    os.makedirs(DB_CYCLE_ARCHIVE_DIR, exist_ok=True)
    os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
