import logging
import os
import sys
import time
import functools
from datetime import datetime

from rem_card.app.paths import LOGS_DIR, ensure_directories

def setup_logger():
    ensure_directories()

    log_file = os.path.join(LOGS_DIR, f"rem_card_{datetime.now().strftime('%Y%m%d')}.log")
    
    logger = logging.getLogger("RemCard")
    # Меняем уровень на INFO, чтобы избежать спама DEBUG логов (например, SQL-запросов)
    logger.setLevel(logging.INFO)

    # Формат логирования
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')

    # Handler для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Создаем глобальный логгер
logger = setup_logger()

import threading
import faulthandler

def _extract_fault_payload(content: str) -> str:
    payload_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--- SESSION START:") and stripped.endswith("---"):
            continue
        payload_lines.append(line)
    if not payload_lines:
        return ""
    return "\n".join(payload_lines[-40:])

def init_crash_handler():
    """Инициализация расширенного перехватчика фатальных сбоев (C++ и Python)."""
    ensure_directories()
        
    fault_log_path = os.path.join(LOGS_DIR, "faults.log")
    
    # 1. Проверяем, были ли сбои в прошлом сеансе
    if os.path.exists(fault_log_path) and os.path.getsize(fault_log_path) > 0:
        try:
            with open(fault_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                payload = _extract_fault_payload(content)
                if payload:
                    logger.warning(f"!!! FOUND PREVIOUS CRASH LOG (check faults.log) !!!\nLast state:\n{payload[-500:]}")
        except Exception:
            pass
            
    # 2. Настраиваем faulthandler (запись низкоуровневых ошибок Qt/C++)
    try:
        # Открываем файл в режиме добавления с принудительным сбросом буфера
        fault_file = open(fault_log_path, "a", encoding="utf-8")
        # Записываем разделитель сеанса
        fault_file.write(f"\n--- SESSION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        fault_file.flush()
        faulthandler.enable(file=fault_file)
    except Exception as e:
        logger.error(f"Failed to enable faulthandler: {e}")

def log_exception(exc_type, exc_value, exc_traceback):
    """Глобальный перехватчик исключений (Python)."""
    if issubclass(exc_type, KeyboardInterrupt):
        if hasattr(sys, '__excepthook__'):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    # Формируем детальное сообщение об ошибке
    import traceback
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    logger.critical(
        f"--- UNCAUGHT PYTHON EXCEPTION ---\n"
        f"Type: {exc_type.__name__}\n"
        f"Value: {exc_value}\n"
        f"{tb_text}"
    )

# Установка перехватчиков
sys.excepthook = log_exception

def log_execution_time(threshold_ms=50):
    """Декоратор для замера времени выполнения функции. Логирует только если превышен порог threshold_ms."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000
            if execution_time_ms > threshold_ms:
                logger.debug(f"PERF: {func.__name__} took {execution_time_ms:.2f}ms")
            return result
        return wrapper
    return decorator

def _log_thread_exception(args):
    """Глобальный перехватчик исключений для потоков."""
    logger.critical(
        f"--- UNCAUGHT THREAD EXCEPTION ({args.thread.name if args.thread else 'unknown'}) ---\n"
        f"Type: {args.exc_type.__name__ if args.exc_type else 'Unknown'}\n"
        f"Value: {args.exc_value}\n",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )

threading.excepthook = _log_thread_exception
