from __future__ import annotations

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from rem_card.services.minigames.snake_service import SnakeGame


class SnakeWidget(QWidget):
    game_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = SnakeGame(width=40, height=40)
        self._result_emitted = False
        self.setFocusPolicy(Qt.StrongFocus)

        self.timer = QTimer(self)
        self.timer.setInterval(90)
        self.timer.timeout.connect(self._tick)

        self._build_ui()
        self.start_game()

    def start_game(self) -> None:
        self.game.reset()
        self._result_emitted = False
        self.restart_btn.setEnabled(False)
        self.save_label.setText("")
        self._update_labels()
        self.status_label.setText("Стрелки клавиатуры")
        self.board.update()
        self.timer.start()
        self.setFocus(Qt.OtherFocusReason)

    def stop_game(self) -> None:
        self.timer.stop()

    def set_save_status(self, text: str) -> None:
        self.save_label.setText(str(text or ""))

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key_Left:
            self.game.set_direction(-1, 0)
            event.accept()
            return
        if key == Qt.Key_Right:
            self.game.set_direction(1, 0)
            event.accept()
            return
        if key == Qt.Key_Up:
            self.game.set_direction(0, -1)
            event.accept()
            return
        if key == Qt.Key_Down:
            self.game.set_direction(0, 1)
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        self.stop_game()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        info_row = QHBoxLayout()
        self.score_label = QLabel("")
        self.length_label = QLabel("")
        self.time_label = QLabel("")
        for label in (self.score_label, self.length_label, self.time_label):
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        info_row.addWidget(self.score_label)
        info_row.addWidget(self.length_label)
        info_row.addWidget(self.time_label)
        info_row.addStretch()

        self.board = _SnakeBoard(self.game)

        bottom_row = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #2c3e50;")
        self.save_label = QLabel("")
        self.save_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.restart_btn = QPushButton("Новая игра")
        self.restart_btn.clicked.connect(self.start_game)
        bottom_row.addWidget(self.status_label)
        bottom_row.addWidget(self.save_label)
        bottom_row.addStretch()
        bottom_row.addWidget(self.restart_btn)

        layout.addLayout(info_row)
        layout.addWidget(self.board, 0, Qt.AlignCenter)
        layout.addLayout(bottom_row)

    def _tick(self) -> None:
        result = self.game.step()
        self._update_labels()
        self.board.update()
        if result.finished:
            self._finish_game(result.won)

    def _finish_game(self, won: bool) -> None:
        self.timer.stop()
        self.restart_btn.setEnabled(True)
        self.status_label.setText("Победа" if won else "Игра окончена")
        if not self._result_emitted:
            self._result_emitted = True
            self.game_finished.emit(dict(self.game.result()))

    def _update_labels(self) -> None:
        self.score_label.setText(f"Счёт: {self.game.score}")
        self.length_label.setText(f"Длина: {self.game.length}")
        self.time_label.setText(f"Время: {_format_duration(self.game.elapsed_sec())}")
        if self.timer.isActive():
            self.status_label.setText("Стрелки клавиатуры")


class _SnakeBoard(QWidget):
    CELL_SIZE = 15
    CELLS = 40
    BOARD_SIZE = CELL_SIZE * CELLS

    def __init__(self, game: SnakeGame, parent=None):
        super().__init__(parent)
        self.game = game
        self.setFixedSize(self.BOARD_SIZE, self.BOARD_SIZE)
        self.setFocusPolicy(Qt.NoFocus)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#f8f9fa"))

        grid_pen = QPen(QColor("#e2e6ea"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for pos in range(0, self.BOARD_SIZE + 1, self.CELL_SIZE):
            painter.drawLine(pos, 0, pos, self.BOARD_SIZE)
            painter.drawLine(0, pos, self.BOARD_SIZE, pos)

        if self.game.food is not None:
            self._fill_cell(painter, self.game.food, QColor("#e74c3c"))

        for index, point in enumerate(reversed(self.game.snake)):
            color = QColor("#27ae60") if index < len(self.game.snake) - 1 else QColor("#145a32")
            self._fill_cell(painter, point, color)

        border_pen = QPen(QColor("#2c3e50"))
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def _fill_cell(self, painter: QPainter, point, color: QColor) -> None:
        x, y = point
        rect = QRect(
            x * self.CELL_SIZE + 1,
            y * self.CELL_SIZE + 1,
            self.CELL_SIZE - 2,
            self.CELL_SIZE - 2,
        )
        painter.fillRect(rect, color)


def _format_duration(duration_sec: int) -> str:
    minutes, seconds = divmod(max(0, int(duration_sec or 0)), 60)
    return f"{minutes:02d}:{seconds:02d}"
