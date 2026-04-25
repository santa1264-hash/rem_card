from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class GameSelectPage(QWidget):
    snake_requested = Signal()
    leaderboard_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def set_user_name(self, full_name: str) -> None:
        pass

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        name = QLabel("1. Змейка")
        name.setStyleSheet("font-weight: bold; color: #2c3e50;")
        load_btn = QPushButton("Загрузить")
        leaders_btn = QPushButton("Лидеры")
        load_btn.clicked.connect(self.snake_requested.emit)
        leaders_btn.clicked.connect(self.leaderboard_requested.emit)

        grid.addWidget(name, 0, 0)
        grid.addWidget(load_btn, 0, 1)
        grid.addWidget(leaders_btn, 0, 2)

        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.back_requested.emit)

        layout.addLayout(grid)
        layout.addStretch()
        layout.addWidget(back_btn)
