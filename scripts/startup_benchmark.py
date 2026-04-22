#!/usr/bin/env python
"""
Startup benchmark for RemCard and Journal entry paths.

Usage:
  set PYTHONPATH=C:\Project
  python C:\Project\rem_card\scripts\startup_benchmark.py --mode remcard
  python C:\Project\rem_card\scripts\startup_benchmark.py --mode journal
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class StepResult:
    step: str
    ms: float


def _now() -> float:
    return time.perf_counter()


def _ms(start: float) -> float:
    return round((_now() - start) * 1000.0, 2)


def _benchmark_remcard(role: str) -> dict:
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    steps: List[StepResult] = []
    container = None
    window = None
    role_widget = None

    t = _now()
    from rem_card.ui.main_window import MainWindow
    steps.append(StepResult("import_ui_main_window", _ms(t)))

    t = _now()
    from rem_card.app.bootstrap import bootstrap
    steps.append(StepResult("import_bootstrap", _ms(t)))

    t = _now()
    container = bootstrap()
    steps.append(StepResult("bootstrap", _ms(t)))

    t = _now()
    window = MainWindow(container=None, role=role)
    steps.append(StepResult("construct_main_window", _ms(t)))

    if role == "doctor":
        t = _now()
        from rem_card.ui.doctor_view.doctor_main_widget import DoctorMainWidget
        role_widget = DoctorMainWidget(container.patient_service, container.remcard_service)
        steps.append(StepResult("construct_doctor_main_widget", _ms(t)))
    elif role == "nurse":
        t = _now()
        from rem_card.ui.nurse_view.nurse_main_widget import NurseMainWidget
        role_widget = NurseMainWidget(container.patient_service, container.remcard_service)
        steps.append(StepResult("construct_nurse_main_widget", _ms(t)))

    total = round(sum(step.ms for step in steps), 2)
    result = {
        "mode": "remcard",
        "role": role,
        "steps": [asdict(step) for step in steps],
        "total_ms": total,
    }

    if role_widget is not None:
        role_widget.deleteLater()
    if window is not None:
        window.deleteLater()
    if container is not None:
        try:
            container.data_service.shutdown()
        except Exception:
            pass
        try:
            container.db_manager.close()
        except Exception:
            pass

    return result


def _benchmark_journal() -> dict:
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    steps: List[StepResult] = []
    db = None
    window = None

    t = _now()
    from rem_card.Rao_jornal.ui.main_window import MainWindow
    steps.append(StepResult("import_journal_main_window", _ms(t)))

    t = _now()
    from rem_card.Rao_jornal.database.db_manager import DBManager
    from rem_card.Rao_jornal.services.patient_service import PatientService
    steps.append(StepResult("import_journal_services", _ms(t)))

    t = _now()
    db = DBManager()
    patient_service = PatientService(db)
    steps.append(StepResult("init_journal_db_and_service", _ms(t)))

    t = _now()
    window = MainWindow(db, patient_service)
    steps.append(StepResult("construct_journal_main_window", _ms(t)))

    total = round(sum(step.ms for step in steps), 2)
    result = {
        "mode": "journal",
        "steps": [asdict(step) for step in steps],
        "total_ms": total,
    }

    if window is not None:
        window.deleteLater()
    if db is not None:
        try:
            db.close_connection()
        except Exception:
            pass

    return result


def main():
    parser = argparse.ArgumentParser(description="Startup benchmark for RemCard/Journal")
    parser.add_argument("--mode", choices=["remcard", "journal"], required=True)
    parser.add_argument("--role", choices=["doctor", "nurse"], default="doctor", help="Role for remcard mode")
    args = parser.parse_args()

    if args.mode == "remcard":
        result = _benchmark_remcard(args.role)
    else:
        result = _benchmark_journal()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
