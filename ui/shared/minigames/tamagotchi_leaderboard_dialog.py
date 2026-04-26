from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem

from rem_card.services.minigames.tamagotchi_service import animal_label, format_weight, stage_label
from rem_card.ui.shared.base_dialog import BaseStyledDialog
from rem_card.ui.shared.minigames.user_select_page import role_label


class TamagotchiLeaderboardDialog(BaseStyledDialog):
    def __init__(self, tamagotchi_service, parent=None):
        super().__init__("Лидеры: Тамагочи", parent)
        self.tamagotchi_service = tamagotchi_service
        self.resize(960, 420)
        self._build_ui()
        self._load_rows()

    def _build_ui(self) -> None:
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["ФИО", "Роль", "Питомец", "Животное", "Стадия", "Возраст", "Вес", "Здоровье", "Статус", "Обновлено"]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 10):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.empty_label = QLabel("Живых рекордов Тамагочи пока нет.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #6c757d;")
        self.content_layout.addWidget(self.table)
        self.content_layout.addWidget(self.empty_label)

    def _load_rows(self) -> None:
        entries = self.tamagotchi_service.get_tamagotchi_leaderboard()
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._set_row(row, entry)
        has_rows = bool(entries)
        self.table.setVisible(has_rows)
        self.empty_label.setVisible(not has_rows)

    def _set_row(self, row: int, entry: Dict[str, Any]) -> None:
        values: List[str] = [
            str(entry.get("full_name") or ""),
            role_label(entry.get("role")),
            str(entry.get("pet_name") or ""),
            animal_label(entry.get("animal")),
            stage_label(entry.get("stage")),
            _format_age(int(entry.get("age_minutes") or 0)),
            format_weight(entry.get("weight")),
            f"{int(entry.get('health') or 0)}%",
            "живой рекорд",
            _format_dt(entry.get("last_updated_at")),
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col in (5, 6, 7, 8, 9):
                item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)


def _format_age(age_minutes: int) -> str:
    clean = max(0, int(age_minutes or 0))
    days, rem = divmod(clean, 24 * 60)
    hours, minutes = divmod(rem, 60)
    if days:
        return f"{days}д {hours}ч {minutes}м"
    return f"{hours}ч {minutes}м"


def _format_dt(value) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return parsed.strftime("%d.%m.%Y %H:%M")
