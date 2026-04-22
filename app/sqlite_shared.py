import json
import logging
import os
import queue
import random
import shutil
import socket
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

SQLITE_BUSY_TIMEOUT_MS = max(100, int(os.environ.get("REMCARD_SQLITE_BUSY_TIMEOUT_MS", "5000")))
_SQLITE_ALLOWED_CONNECTION_PROFILES = {"network", "local_replica", "local_outbox"}
_SQLITE_ALLOWED_JOURNAL_MODES = {"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"}
_SQLITE_ALLOWED_SYNCHRONOUS = {"OFF", "NORMAL", "FULL", "EXTRA"}
_SQLITE_ALLOWED_TEMP_STORE = {"DEFAULT", "FILE", "MEMORY"}
_LOCK_READ_UNAVAILABLE = object()


def _safe_env_int(name: str) -> Optional[int]:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def _resolve_sqlite_profile_settings(profile: str = "network") -> dict[str, Any]:
    normalized_profile = str(profile or "network").strip().lower()
    if normalized_profile not in _SQLITE_ALLOWED_CONNECTION_PROFILES:
        normalized_profile = "network"

    settings_by_profile: dict[str, dict[str, Any]] = {
        "network": {
            "profile": "network",
            "journal_mode": "TRUNCATE",
            "synchronous": "NORMAL",
            "temp_store": "MEMORY",
            "cache_kb": 8 * 1024,
            "mmap_mb": 64,
        },
        "local_replica": {
            "profile": "local_replica",
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "temp_store": "MEMORY",
            "cache_kb": 32 * 1024,
            "mmap_mb": 128,
        },
        "local_outbox": {
            "profile": "local_outbox",
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "temp_store": "MEMORY",
            "cache_kb": 16 * 1024,
            "mmap_mb": 64,
        },
    }
    settings = dict(settings_by_profile[normalized_profile])

    env_prefix = f"REMCARD_SQLITE_{normalized_profile.upper()}"
    journal_override = str(
        os.environ.get(f"{env_prefix}_JOURNAL_MODE", os.environ.get("REMCARD_SQLITE_JOURNAL_MODE", ""))
    ).strip().upper()
    if journal_override in _SQLITE_ALLOWED_JOURNAL_MODES:
        settings["journal_mode"] = journal_override

    synchronous_override = str(
        os.environ.get(f"{env_prefix}_SYNCHRONOUS", os.environ.get("REMCARD_SQLITE_SYNCHRONOUS", ""))
    ).strip().upper()
    if synchronous_override in _SQLITE_ALLOWED_SYNCHRONOUS:
        settings["synchronous"] = synchronous_override

    temp_store_override = str(
        os.environ.get(f"{env_prefix}_TEMP_STORE", os.environ.get("REMCARD_SQLITE_TEMP_STORE", ""))
    ).strip().upper()
    if temp_store_override in _SQLITE_ALLOWED_TEMP_STORE:
        settings["temp_store"] = temp_store_override

    cache_override = _safe_env_int(f"{env_prefix}_CACHE_KB")
    if cache_override is None:
        cache_override = _safe_env_int("REMCARD_SQLITE_CACHE_KB")
    if cache_override and cache_override > 0:
        settings["cache_kb"] = cache_override

    mmap_override = _safe_env_int(f"{env_prefix}_MMAP_MB")
    if mmap_override is None:
        mmap_override = _safe_env_int("REMCARD_SQLITE_MMAP_MB")
    if mmap_override and mmap_override >= 0:
        settings["mmap_mb"] = mmap_override

    return settings


def configure_connection(
    conn: sqlite3.Connection,
    *,
    readonly: bool = False,
    profile: str = "network",
):
    settings = _resolve_sqlite_profile_settings(profile)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if readonly:
        conn.execute("PRAGMA query_only = ON")
    else:
        conn.execute(f"PRAGMA journal_mode = {settings['journal_mode']}")
        conn.execute(f"PRAGMA synchronous = {settings['synchronous']}")
    if settings["temp_store"] != "DEFAULT":
        conn.execute(f"PRAGMA temp_store = {settings['temp_store']}")
    if settings["cache_kb"]:
        conn.execute(f"PRAGMA cache_size = {-int(settings['cache_kb'])}")
    if settings["mmap_mb"] is not None:
        conn.execute(f"PRAGMA mmap_size = {int(settings['mmap_mb']) * 1024 * 1024}")
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")


def run_integrity_check(conn: sqlite3.Connection) -> tuple[bool, str]:
    row = conn.execute("PRAGMA integrity_check").fetchone()
    if not row:
        return False, "integrity_check returned no result"
    result = row[0]
    return result == "ok", str(result)

def run_quick_check(conn: sqlite3.Connection) -> tuple[bool, str]:
    row = conn.execute("PRAGMA quick_check").fetchone()
    if not row:
        return False, "quick_check returned no result"
    result = row[0]
    return result == "ok", str(result)


def backup_connection(conn: sqlite3.Connection, backup_path: str):
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    backup_conn = sqlite3.connect(backup_path)
    try:
        with backup_conn:
            conn.backup(backup_conn)
    finally:
        backup_conn.close()


def restore_database(db_path: str, backup_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    shutil.copy2(backup_path, db_path)


def find_latest_backup(backup_dir: str, prefix: Optional[str] = None) -> Optional[str]:
    candidates = list_backup_candidates(backup_dir=backup_dir, prefix=prefix)
    return candidates[0] if candidates else None


def list_backup_candidates(backup_dir: str, prefix: Optional[str] = None) -> list[str]:
    if not os.path.isdir(backup_dir):
        return []

    candidates = []
    for name in os.listdir(backup_dir):
        if not name.endswith(".db"):
            continue
        if prefix and not name.startswith(prefix):
            continue
        full_path = os.path.join(backup_dir, name)
        if os.path.isfile(full_path):
            candidates.append(full_path)

    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates


def validate_sqlite_file(file_path: str) -> tuple[bool, str]:
    if not file_path:
        return False, "empty file path"
    if not os.path.exists(file_path):
        return False, "file does not exist"
    if os.path.getsize(file_path) <= 0:
        return False, "file size is zero"

    conn = None
    try:
        uri = f"file:{file_path}?mode=ro"
        conn = sqlite3.connect(
            uri,
            uri=True,
            check_same_thread=False,
            isolation_level=None,
            timeout=5.0,
        )
        configure_connection(conn, readonly=True)

        ok, result = run_quick_check(conn)
        if not ok:
            return False, f"quick_check failed: {result}"

        ok, result = run_integrity_check(conn)
        if not ok:
            return False, f"integrity_check failed: {result}"

        return True, "ok"
    except Exception as exc:
        return False, str(exc)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def quarantine_corrupted_db_file(
    db_path: str,
    logger: Optional[logging.Logger] = None,
    *,
    quarantine_dir: Optional[str] = None,
    reason: Optional[str] = None,
) -> Optional[str]:
    if not db_path or not os.path.exists(db_path):
        return None

    logger = logger or logging.getLogger(__name__)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if quarantine_dir:
        os.makedirs(quarantine_dir, exist_ok=True)
        quarantine_path = os.path.join(quarantine_dir, f"{os.path.basename(db_path)}.corrupt_{timestamp}")
    else:
        quarantine_path = f"{db_path}.corrupt_{timestamp}"
    counter = 1
    while os.path.exists(quarantine_path):
        if quarantine_dir:
            quarantine_path = os.path.join(quarantine_dir, f"{os.path.basename(db_path)}.corrupt_{timestamp}_{counter}")
        else:
            quarantine_path = f"{db_path}.corrupt_{timestamp}_{counter}"
        counter += 1

    try:
        os.replace(db_path, quarantine_path)
    except Exception as exc:
        logger.warning("Failed to move corrupted DB to quarantine (%s): %s", db_path, exc)
        return None

    for suffix in ("-journal", "-wal", "-shm"):
        src = f"{db_path}{suffix}"
        if not os.path.exists(src):
            continue
        try:
            os.replace(src, f"{quarantine_path}{suffix}")
        except Exception as exc:
            logger.warning("Failed to move DB sidecar %s to quarantine: %s", src, exc)

    if reason:
        meta_path = f"{quarantine_path}.reason.txt"
        try:
            with open(meta_path, "w", encoding="utf-8") as fh:
                fh.write(f"time={datetime.now().isoformat()}\n")
                fh.write(f"original_path={db_path}\n")
                fh.write(f"quarantined_path={quarantine_path}\n")
                fh.write(f"reason={reason}\n")
        except Exception as exc:
            logger.warning("Failed to write quarantine metadata %s: %s", meta_path, exc)

    return quarantine_path


def restore_from_best_available_source(
    *,
    db_path: str,
    backup_dir: str,
    preferred_sources: Optional[list[str]] = None,
    backup_prefix: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    quarantine_dir: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    logger = logger or logging.getLogger(__name__)

    def _norm(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    candidates: list[str] = []
    seen: set[str] = set()
    primary_norm = _norm(db_path)

    for source in preferred_sources or []:
        if not source:
            continue
        if not os.path.exists(source):
            continue
        source_norm = _norm(source)
        if source_norm == primary_norm or source_norm in seen:
            continue
        seen.add(source_norm)
        candidates.append(source)

    for source in list_backup_candidates(backup_dir=backup_dir, prefix=backup_prefix):
        source_norm = _norm(source)
        if source_norm == primary_norm or source_norm in seen:
            continue
        seen.add(source_norm)
        candidates.append(source)

    if not candidates:
        raise RuntimeError(f"No recovery candidates found in backup dir: {backup_dir}")

    selected_source: Optional[str] = None
    for candidate in candidates:
        ok, reason = validate_sqlite_file(candidate)
        if ok:
            selected_source = candidate
            break
        logger.warning("Recovery candidate skipped (invalid): %s | %s", candidate, reason)

    if not selected_source:
        raise RuntimeError("No healthy recovery source found (all candidates failed validation)")

    quarantined_path = quarantine_corrupted_db_file(
        db_path,
        logger=logger,
        quarantine_dir=quarantine_dir,
        reason=failure_reason,
    )
    restore_database(db_path, selected_source)
    return selected_source, quarantined_path


class FileWriteLock:
    def __init__(self, lock_path: str, stale_timeout_sec: float = 60.0, logger: Optional[logging.Logger] = None):
        self.lock_path = lock_path
        self.stale_timeout_sec = stale_timeout_sec
        self.logger = logger or logging.getLogger(__name__)
        self._owner_token = None
        self._owner_thread_id = None
        self._reentrancy = 0
        self._mutex = threading.Lock()

    def _build_payload(self, owner_id: str, source: str) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "user_id": owner_id,
            "source": source,
            "thread_id": threading.get_ident(),
        }

    def _try_read_payload(self) -> Optional[dict[str, Any]]:
        try:
            with open(self.lock_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None
        except Exception as exc:
            self.logger.warning("Failed to read db lock %s: %s", self.lock_path, exc)
            return _LOCK_READ_UNAVAILABLE

    def _is_stale(self, payload: Optional[dict[str, Any]]) -> bool:
        if payload is _LOCK_READ_UNAVAILABLE:
            # Ошибка чтения lock-файла не означает "stale".
            # В этой ситуации безопаснее считать lock занятым.
            return False
        if not payload:
            return True
        ts = payload.get("timestamp")
        if not isinstance(ts, (int, float)):
            return True
        return (time.time() - ts) > self.stale_timeout_sec

    @staticmethod
    def _is_self_orphan(payload: Optional[dict[str, Any]], owner_id: str, thread_id: int) -> bool:
        if not payload:
            return False
        try:
            return (
                payload.get("user_id") == owner_id
                and int(payload.get("pid")) == os.getpid()
                and int(payload.get("thread_id")) == int(thread_id)
            )
        except Exception:
            return False

    def acquire(self, owner_id: str, source: str) -> bool:
        thread_id = threading.get_ident()
        with self._mutex:
            if self._owner_thread_id == thread_id and self._owner_token is not None:
                self._reentrancy += 1
                return True

        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        payload = self._build_payload(owner_id, source)
        raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")

        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    os.write(fd, raw)
                finally:
                    os.close(fd)
                with self._mutex:
                    self._owner_token = payload
                    self._owner_thread_id = thread_id
                    self._reentrancy = 1
                return True
            except FileExistsError:
                existing = self._try_read_payload()
                if existing is _LOCK_READ_UNAVAILABLE:
                    return False
                if self._is_self_orphan(existing, owner_id, thread_id):
                    try:
                        os.remove(self.lock_path)
                        self.logger.warning("Removed orphan self-owned db lock at %s", self.lock_path)
                        continue
                    except FileNotFoundError:
                        continue
                    except Exception as exc:
                        self.logger.warning("Failed to remove orphan self-owned db lock %s: %s", self.lock_path, exc)
                if self._is_stale(existing):
                    try:
                        os.remove(self.lock_path)
                        self.logger.warning("Removed stale db lock at %s", self.lock_path)
                        continue
                    except FileNotFoundError:
                        continue
                    except Exception as exc:
                        self.logger.warning("Failed to remove stale db lock %s: %s", self.lock_path, exc)
                return False

    def release(self):
        thread_id = threading.get_ident()
        with self._mutex:
            if self._owner_thread_id != thread_id or self._owner_token is None:
                return

            self._reentrancy -= 1
            if self._reentrancy > 0:
                return

            self._owner_token = None
            self._owner_thread_id = None
            self._reentrancy = 0

        try:
            for attempt in range(10):
                try:
                    os.remove(self.lock_path)
                    return
                except FileNotFoundError:
                    return
                except PermissionError as exc:
                    if attempt >= 9:
                        raise
                    time.sleep(0.03)
                except OSError as exc:
                    # На Windows возможен sharing violation (WinError 32) на короткое время.
                    if getattr(exc, "winerror", None) == 32 and attempt < 9:
                        time.sleep(0.03)
                        continue
                    raise
        except FileNotFoundError:
            pass
        except Exception as exc:
            self.logger.warning("Failed to remove db lock %s: %s", self.lock_path, exc)


class SQLiteWriteController:
    def __init__(
        self,
        db_path: str,
        lock_path: str,
        owner_id: str,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 20,
        retry_delay_ms: int = 200,
        stale_timeout_sec: float = 60.0,
    ):
        self.db_path = db_path
        self.lock_path = lock_path
        self.owner_id = owner_id
        self.logger = logger or logging.getLogger(__name__)
        self.max_retries = max_retries
        self.retry_delay_sec = retry_delay_ms / 1000.0
        self.lock = FileWriteLock(lock_path, stale_timeout_sec=stale_timeout_sec, logger=self.logger)
        self._conn_locks: dict[int, threading.RLock] = {}
        self._conn_locks_mutex = threading.Lock()

    def _is_retryable(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "database is locked" in message or "database table is locked" in message

    def _get_conn_lock(self, conn: sqlite3.Connection) -> threading.RLock:
        key = id(conn)
        with self._conn_locks_mutex:
            lock = self._conn_locks.get(key)
            if lock is None:
                lock = threading.RLock()
                self._conn_locks[key] = lock
            return lock

    @contextmanager
    def connection_guard(self, conn: sqlite3.Connection):
        lock = self._get_conn_lock(conn)
        with lock:
            yield

    @contextmanager
    def transaction(self, conn: sqlite3.Connection, source: str = "unknown"):
        with self.connection_guard(conn):
            if conn.in_transaction:
                cursor = conn.cursor()
                yield cursor
                return

            cursor = None
            lock_acquired = False
            last_exc = None
            try:
                for attempt in range(1, self.max_retries + 1):
                    if not self.lock.acquire(self.owner_id, source):
                        time.sleep(self.retry_delay_sec)
                        continue

                    lock_acquired = True
                    try:
                        conn.execute("BEGIN IMMEDIATE")
                        cursor = conn.cursor()
                        break
                    except sqlite3.OperationalError as exc:
                        last_exc = exc
                        if conn.in_transaction:
                            conn.execute("ROLLBACK")
                        self.lock.release()
                        lock_acquired = False
                        if self._is_retryable(exc) and attempt < self.max_retries:
                            time.sleep(self.retry_delay_sec)
                            continue
                        raise

                if cursor is None:
                    if last_exc:
                        raise last_exc
                    raise sqlite3.OperationalError("Could not acquire sequential write lock for SQLite")

                yield cursor
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
            finally:
                if lock_acquired:
                    self.lock.release()

    def execute(self, conn: sqlite3.Connection, query: str, params: tuple = (), source: str = "unknown"):
        with self.transaction(conn, source=source) as cursor:
            cursor.execute(query, params)
            return cursor


@dataclass
class QueuedWriteTask:
    func: Callable[[], Any]
    description: str
    on_success: Optional[Callable[[Any], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None
    retryable: bool = True
    retries_left: int = 10


class LocalWriteQueue:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._queue: queue.Queue[QueuedWriteTask] = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, name="SQLiteLocalWriteQueue", daemon=True)
        self._thread.start()

    def submit(
        self,
        func: Callable[[], Any],
        description: str,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        retryable: bool = True,
        retries_left: int = 10,
    ):
        self._queue.put(
            QueuedWriteTask(
                func=func,
                description=description,
                on_success=on_success,
                on_error=on_error,
                retryable=retryable,
                retries_left=retries_left,
            )
        )

    def shutdown(self, timeout: float = 1.0):
        self._stop.set()
        self._queue.put(
            QueuedWriteTask(
                func=lambda: None,
                description="shutdown",
                retryable=False,
            )
        )
        self._thread.join(timeout=timeout)

    def _worker(self):
        while not self._stop.is_set():
            task = self._queue.get()
            if self._stop.is_set():
                return

            while not self._stop.is_set():
                try:
                    result = task.func()
                    if task.on_success:
                        task.on_success(result)
                    break
                except sqlite3.OperationalError as exc:
                    if task.retryable and task.retries_left > 0 and self._is_retryable_operational_error(exc):
                        task.retries_left -= 1
                        time.sleep(random.uniform(0.10, 0.30))
                        continue
                    if task.on_error:
                        task.on_error(exc)
                    else:
                        self.logger.error("Queued SQLite write failed for %s: %s", task.description, exc)
                    break
                except Exception as exc:
                    if task.on_error:
                        task.on_error(exc)
                    else:
                        self.logger.error("Queued SQLite write failed for %s: %s", task.description, exc)
                    break

    @staticmethod
    def _is_retryable_operational_error(exc: Exception) -> bool:
        message = str(exc).lower()
        if "database is locked" in message or "database table is locked" in message:
            return True
        if "could not acquire sequential write lock" in message:
            return True
        if "busy" in message and "sqlite" in message:
            return True
        return False
