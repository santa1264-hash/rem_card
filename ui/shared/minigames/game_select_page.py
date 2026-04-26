from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class GameSelectPage(QWidget):
    snake_requested = Signal()
    tamagotchi_requested = Signal()
    leaderboard_requested = Signal()
    tamagotchi_leaderboard_requested = Signal()
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

        snake_name = QLabel("1. Змейка")
        snake_name.setStyleSheet("font-weight: bold; color: #2c3e50;")
        snake_load_btn = QPushButton("Загрузить")
        snake_leaders_btn = QPushButton("Лидеры")
        snake_load_btn.clicked.connect(self.snake_requested.emit)
        snake_leaders_btn.clicked.connect(self.leaderboard_requested.emit)

        tamagotchi_name = QLabel("2. Тамагочи")
        tamagotchi_name.setStyleSheet("font-weight: bold; color: #2c3e50;")
        tamagotchi_load_btn = QPushButton("Загрузить")
        tamagotchi_leaders_btn = QPushButton("Лидеры")
        tamagotchi_load_btn.clicked.connect(self.tamagotchi_requested.emit)
        tamagotchi_leaders_btn.clicked.connect(self.tamagotchi_leaderboard_requested.emit)

        grid.addWidget(snake_name, 0, 0)
        grid.addWidget(snake_load_btn, 0, 1)
        grid.addWidget(snake_leaders_btn, 0, 2)
        grid.addWidget(tamagotchi_name, 1, 0)
        grid.addWidget(tamagotchi_load_btn, 1, 1)
        grid.addWidget(tamagotchi_leaders_btn, 1, 2)

        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.back_requested.emit)

        layout.addLayout(grid)
        layout.addStretch()
        layout.addWidget(back_btn)
