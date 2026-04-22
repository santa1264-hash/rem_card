import os
import threading
from datetime import datetime, timedelta

from rem_card.app.logger import logger

_JOURNAL_LOCK = threading.Lock()
_JOURNAL_DB_MANAGER = None
_JOURNAL_PATIENT_SERVICE = None
_JOURNAL_WARMUP_STARTED = False


def _ensure_journal_services():
    global _JOURNAL_DB_MANAGER, _JOURNAL_PATIENT_SERVICE
    with _JOURNAL_LOCK:
        if _JOURNAL_DB_MANAGER is None or _JOURNAL_PATIENT_SERVICE is None:
            from rem_card.Rao_jornal.database.db_manager import DBManager
            from rem_card.Rao_jornal.services.patient_service import PatientService

            _JOURNAL_DB_MANAGER = DBManager()
            _JOURNAL_PATIENT_SERVICE = PatientService(_JOURNAL_DB_MANAGER)
        return _JOURNAL_DB_MANAGER, _JOURNAL_PATIENT_SERVICE


def warmup_journal_services_async():
    global _JOURNAL_WARMUP_STARTED

    with _JOURNAL_LOCK:
        already_ready = _JOURNAL_DB_MANAGER is not None and _JOURNAL_PATIENT_SERVICE is not None
        if already_ready or _JOURNAL_WARMUP_STARTED:
            return
        _JOURNAL_WARMUP_STARTED = True

    def _runner():
        global _JOURNAL_WARMUP_STARTED
        try:
            _ensure_journal_services()
        finally:
            with _JOURNAL_LOCK:
                _JOURNAL_WARMUP_STARTED = False

    threading.Thread(target=_runner, name="JournalWarmup", daemon=True).start()


def create_embedded_journal_widget(parent=None):
    db_manager, patient_service = _ensure_journal_services()
    from rem_card.Rao_jornal.ui.main_window import MainWindow

    return MainWindow(
        db_manager=db_manager,
        patient_service=patient_service,
        parent=parent,
        embedded=True,
        show_db_button=False,
    )


def open_journal_db_viewer(parent=None):
    db_manager, _patient_service = _ensure_journal_services()
    from rem_card.Rao_jornal.ui.db_viewer import DatabaseViewerDialog

    dialog = DatabaseViewerDialog(db_manager, parent)
    dialog.exec()


def open_journal_report_dialog(
    parent=None,
    start_dt: str | None = None,
    end_dt: str | None = None,
    show_graph_button: bool = True,
    db_paths: list[str] | None = None,
):
    db_manager, _cleanup = _resolve_analytics_manager(
        start_dt=start_dt,
        end_dt=end_dt,
        db_paths=db_paths,
    )

    try:
        if not show_graph_button:
            from rem_card.Rao_jornal.ui.statistics_dialog import StatisticsDialog

            now = datetime.now()
            start_dt = start_dt or (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
            end_dt = end_dt or now.strftime("%Y-%m-%d 23:59:59")
            dialog = StatisticsDialog(
                db_manager,
                start_date_str=start_dt,
                end_date_str=end_dt,
                parent=parent,
            )
        else:
            from rem_card.Rao_jornal.ui.report_dialog import ReportDialog

            dialog = ReportDialog(
                db_manager,
                parent,
                start_dt=start_dt,
                end_dt=end_dt,
                show_graph_button=show_graph_button,
            )
        dialog.exec()
    finally:
        if _cleanup:
            _cleanup()


def open_journal_graphs_dialog(
    parent=None,
    start_dt: str | None = None,
    end_dt: str | None = None,
    db_paths: list[str] | None = None,
):
    now = datetime.now()
    if not start_dt:
        start_dt = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    if not end_dt:
        end_dt = now.strftime("%Y-%m-%d 23:59:59")

    db_manager, _cleanup = _resolve_analytics_manager(
        start_dt=start_dt,
        end_dt=end_dt,
        db_paths=db_paths,
    )
    from rem_card.Rao_jornal.ui.graphs_dialog import GraphsDialog

    try:
        dialog = GraphsDialog(db_manager, start_dt, end_dt, parent)
        dialog.exec()
    finally:
        if _cleanup:
            _cleanup()


def _resolve_analytics_manager(
    *,
    start_dt: str | None,
    end_dt: str | None,
    db_paths: list[str] | None,
):
    base_db_manager, _patient_service = _ensure_journal_services()
    if not db_paths:
        return base_db_manager, None

    # Нормализуем и фильтруем список БД.
    normalized = []
    seen = set()
    for raw in db_paths:
        if not raw:
            continue
        path = str(raw)
        if not path:
            continue

        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            continue
        key = os.path.normcase(abs_path)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(abs_path)

    if not normalized:
        return base_db_manager, None

    base_path = ""
    try:
        base_path = os.path.normcase(os.path.abspath(str(getattr(base_db_manager, "db_path", "") or "")))
    except Exception:
        base_path = ""
    if len(normalized) == 1 and base_path and os.path.normcase(normalized[0]) == base_path:
        return base_db_manager, None

    try:
        from rem_card.Rao_jornal.database.multi_db_analytics import create_multi_db_analytics_manager

        merged_manager = create_multi_db_analytics_manager(
            normalized,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        return merged_manager, merged_manager.close_connection
    except Exception as exc:
        logger.warning("Failed to build multi-DB analytics manager, fallback to primary DB: %s", exc)
        return base_db_manager, None


def close_journal_services():
    global _JOURNAL_DB_MANAGER, _JOURNAL_PATIENT_SERVICE
    with _JOURNAL_LOCK:
        if _JOURNAL_DB_MANAGER is not None:
            try:
                _JOURNAL_DB_MANAGER.close_connection()
            except Exception:
                pass
        _JOURNAL_DB_MANAGER = None
        _JOURNAL_PATIENT_SERVICE = None
