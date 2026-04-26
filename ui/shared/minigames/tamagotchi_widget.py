from __future__ import annotations

from typing import Dict

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from rem_card.services.minigames.tamagotchi_service import TamagotchiService, animal_label, format_weight, stage_label


class TamagotchiWidget(QWidget):
    def __init__(self, user_id: str, service: TamagotchiService, parent=None):
        super().__init__(parent)
        self.user_id = str(user_id)
        self.service = service
        self.state: Dict = self.service.load_state(self.user_id)
        self._tick_count = 0
        self.setFocusPolicy(Qt.StrongFocus)

        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self._tick)
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(180)
        self.animation_timer.timeout.connect(self._animate)

        self._build_ui()
        self._refresh()
        if self.state.get("alive", True):
            self.timer.start()
        self.animation_timer.start()

    def stop_game(self) -> None:
        self.timer.stop()
        self.animation_timer.stop()
        self.state = self.service.save_state(self.user_id, self.state)

    def reset_pet(self) -> None:
        self.state, message = self.service.perform_action(self.user_id, self.state, "reset")
        self.state["last_event"] = message
        if not self.timer.isActive():
            self.timer.start()
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self._refresh()

    def closeEvent(self, event) -> None:
        self.stop_game()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.canvas = _TamagotchiCanvas(self.state)

        meta_row = QHBoxLayout()
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #6c757d;")
        meta_row.addWidget(self.name_label)
        meta_row.addStretch()
        meta_row.addWidget(self.meta_label)

        bars = QGridLayout()
        bars.setHorizontalSpacing(10)
        bars.setVerticalSpacing(6)
        self.bars = {
            "hunger": self._make_bar("#f39c12"),
            "happiness": self._make_bar("#e84393"),
            "cleanliness": self._make_bar("#00a8ff"),
            "energy": self._make_bar("#8e44ad"),
            "health": self._make_bar("#27ae60"),
            "anger": self._make_bar("#e74c3c"),
            "stress": self._make_bar("#6f42c1"),
            "discipline": self._make_bar("#607d8b"),
        }
        labels = [
            ("Сытость", "hunger"),
            ("Радость", "happiness"),
            ("Чистота", "cleanliness"),
            ("Энергия", "energy"),
            ("Здоровье", "health"),
            ("Злость", "anger"),
            ("Стресс", "stress"),
            ("Послушание", "discipline"),
        ]
        for index, (title, key) in enumerate(labels):
            row = index // 2
            col = (index % 2) * 2
            label = QLabel(title)
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            bars.addWidget(label, row, col)
            bars.addWidget(self.bars[key], row, col + 1)

        actions = QGridLayout()
        actions.setHorizontalSpacing(8)
        actions.setVerticalSpacing(8)
        for index, (text, action, color) in enumerate(
            [
                ("Корм", "feed", "#f39c12"),
                ("Сладость", "snack", "#e84393"),
                ("Играть", "play", "#27ae60"),
                ("Убрать", "clean", "#00a8ff"),
                ("Лекарство", "medicine", "#c0392b"),
                ("Сон", "sleep", "#8e44ad"),
            ]
        ):
            button = QPushButton(text)
            button.setStyleSheet(_button_style(color))
            button.clicked.connect(lambda checked=False, act=action: self._action(act))
            actions.addWidget(button, index // 4, index % 4)

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setFixedHeight(38)
        self.message_label.setStyleSheet("color: #2c3e50; font-weight: bold;")

        layout.addLayout(meta_row)
        layout.addWidget(self.canvas, 0, Qt.AlignCenter)
        layout.addLayout(bars)
        layout.addLayout(actions)
        layout.addWidget(self.message_label)

    def _make_bar(self, color: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(True)
        bar.setFixedHeight(16)
        bar.setMaximumWidth(170)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: #f8f9fa;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
            """
        )
        return bar

    def _tick(self) -> None:
        self._tick_count += 1
        self.state = self.service.tick(
            self.user_id,
            self.state,
            minutes=1,
            save=(self._tick_count % 6 == 0),
        )
        self._refresh()

    def _animate(self) -> None:
        self.canvas.advance_frame()

    def _action(self, action: str) -> None:
        self.state, message = self.service.perform_action(self.user_id, self.state, action)
        self.state["last_event"] = message
        self._refresh()

    def _refresh(self) -> None:
        age_minutes = int(self.state.get("age_minutes") or 0)
        age_hours = age_minutes // 60
        age_tail = age_minutes % 60
        self.name_label.setText(str(self.state.get("name") or "Тама"))
        self.meta_label.setText(
            f"{animal_label(self.state.get('animal'))} | {stage_label(self.state.get('stage'))} | {age_hours}ч {age_tail}м | "
            f"{format_weight(self.state.get('weight'))}"
        )
        for key, bar in self.bars.items():
            bar.setValue(int(self.state.get(key) or 0))
        self.message_label.setText(str(self.state.get("last_event") or ""))
        self.canvas.set_state(self.state)
        if not self.state.get("alive", True):
            self.timer.stop()


class _TamagotchiCanvas(QWidget):
    def __init__(self, state: Dict, parent=None):
        super().__init__(parent)
        self.state = dict(state or {})
        self.frame = 0
        self.setFixedSize(420, 300)

    def set_state(self, state: Dict) -> None:
        self.state = dict(state or {})
        self.update()

    def advance_frame(self) -> None:
        self.frame = (self.frame + 1) % 10000
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._draw_room(painter)
        self._draw_mess(painter)
        self._draw_pet(painter)
        self._draw_status(painter)

    def _draw_room(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor("#bde0fe"))
        painter.fillRect(QRect(0, 190, self.width(), 110), QColor("#caffbf"))
        painter.setPen(QPen(QColor("#8ecae6"), 2))
        for x in range(20, self.width(), 40):
            painter.drawLine(x, 0, x - 25, 190)
        painter.setBrush(QColor("#ffd166"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(28, 24, 54, 54)
        painter.setBrush(QColor("#f1faee"))
        painter.drawEllipse(285, 38, 70, 26)
        painter.drawEllipse(324, 30, 58, 34)
        painter.drawEllipse(245, 48, 62, 30)

    def _draw_pet(self, painter: QPainter) -> None:
        state = self.state
        alive = bool(state.get("alive", True))
        sleeping = bool(state.get("sleeping"))
        sick = bool(state.get("sick"))
        stage = str(state.get("stage") or "egg")
        animal = str(state.get("animal") or "")

        if not alive or stage == "dead":
            self._draw_coffin(painter)
            return

        pose = [0, 1, 2, 1][self.frame % 4]
        movement = 0 if sleeping else [-12, 0, 12, 0][pose]
        bob = 0 if sleeping else [0, -4, 0, -4][pose]
        cx, cy = 210 + movement, 160 - bob
        if stage == "egg":
            self._draw_egg(painter, cx, cy, 0.72)
            return

        scale = _stage_scale(stage)
        self._draw_animal_shape(painter, animal, stage, cx, cy, scale, pose, sick)
        self._draw_stage_marks(painter, stage, cx, cy, scale)

    def _draw_animal_shape(
        self,
        painter: QPainter,
        animal: str,
        stage: str,
        cx: int,
        cy: int,
        scale: float,
        pose: int,
        sick: bool,
    ) -> None:
        body_color = _animal_color(animal, stage)
        if sick:
            body_color = QColor("#9bc53d")
        if animal == "elephant":
            self._draw_elephant(painter, cx, cy, scale, body_color, mammoth=False, pose=pose)
        elif animal == "giraffe":
            self._draw_giraffe(painter, cx, cy, scale, body_color, pose)
        elif animal == "chipmunk":
            self._draw_chipmunk(painter, cx, cy, scale, body_color, pose)
        elif animal == "dog":
            self._draw_dog(painter, cx, cy, scale, body_color, pose)
        elif animal == "cat":
            self._draw_cat(painter, cx, cy, scale, body_color, pose)
        elif animal == "mammoth":
            self._draw_elephant(painter, cx, cy, scale, body_color, mammoth=True, pose=pose)
        elif animal == "unicorn":
            self._draw_unicorn(painter, cx, cy, scale, body_color, pose)
        else:
            self._draw_tiger(painter, cx, cy, scale, body_color, pose)

    def _draw_base_quadruped(
        self,
        painter: QPainter,
        cx: int,
        cy: int,
        scale: float,
        color: QColor,
        pose: int,
        *,
        head_long: bool = False,
        tail_style: str = "curve",
    ) -> tuple[int, int, int, int]:
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
        painter.setBrush(color)
        body_w = int(126 * scale)
        body_h = int(64 * scale)
        body_x = cx - body_w // 2
        body_y = cy - body_h // 2 + int(12 * (1 - scale))
        painter.drawEllipse(body_x, body_y, body_w, body_h)

        head_w = int((52 if not head_long else 66) * scale)
        head_h = int(46 * scale)
        head_x = body_x + body_w - int(18 * scale)
        head_y = body_y - int(22 * scale)
        painter.drawEllipse(head_x, head_y, head_w, head_h)

        leg_shift = int((pose - 1) * 5 * scale)
        painter.setBrush(color.darker(110))
        for idx, leg_x in enumerate((body_x + int(22 * scale), body_x + int(48 * scale), body_x + int(78 * scale), body_x + int(104 * scale))):
            shift = leg_shift if idx % 2 == 0 else -leg_shift
            painter.drawRoundedRect(leg_x + shift, body_y + int(48 * scale), int(13 * scale), int(40 * scale), 5, 5)

        if tail_style == "curve":
            painter.setPen(QPen(QColor("#2c3e50"), max(2, int(4 * scale))))
            painter.drawArc(body_x - int(38 * scale), body_y + int(2 * scale), int(58 * scale), int(56 * scale), 100 * 16, 210 * 16)
        elif tail_style == "fluffy":
            painter.setBrush(color.lighter(120))
            painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
            painter.drawEllipse(body_x - int(44 * scale), body_y - int(18 * scale), int(54 * scale), int(86 * scale))

        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#2c3e50"), max(1, int(2 * scale))))
        eye_x = head_x + int(33 * scale)
        eye_y = head_y + int(16 * scale)
        painter.drawEllipse(eye_x, eye_y, int(11 * scale), int(10 * scale))
        painter.setBrush(QColor("#2c3e50"))
        painter.drawEllipse(eye_x + int(4 * scale), eye_y + int(3 * scale), max(3, int(4 * scale)), max(3, int(4 * scale)))
        return body_x, body_y, body_w, body_h

    def _draw_tiger(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, body_h = self._draw_base_quadruped(painter, cx, cy, scale, color, pose)
        painter.setBrush(QColor("#2c3e50"))
        painter.setPen(Qt.NoPen)
        for offset in (22, 48, 74):
            painter.drawRect(body_x + int(offset * scale), body_y + int(8 * scale), int(7 * scale), int(38 * scale))
        self._draw_triangle(painter, body_x + body_w - int(4 * scale), body_y - int(28 * scale), body_x + body_w + int(16 * scale), body_y - int(6 * scale), body_x + body_w - int(18 * scale), body_y - int(4 * scale), color)

    def _draw_dog(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, _ = self._draw_base_quadruped(painter, cx, cy, scale, color, pose, head_long=True)
        painter.setBrush(color.darker(115))
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
        painter.drawEllipse(body_x + body_w + int(14 * scale), body_y - int(14 * scale), int(24 * scale), int(50 * scale))
        painter.setBrush(QColor("#2c3e50"))
        painter.drawEllipse(body_x + body_w + int(36 * scale), body_y + int(4 * scale), int(9 * scale), int(8 * scale))

    def _draw_cat(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, _ = self._draw_base_quadruped(painter, cx, cy, scale, color, pose)
        self._draw_triangle(painter, body_x + body_w + int(2 * scale), body_y - int(34 * scale), body_x + body_w + int(24 * scale), body_y - int(8 * scale), body_x + body_w - int(13 * scale), body_y - int(8 * scale), color)
        self._draw_triangle(painter, body_x + body_w + int(44 * scale), body_y - int(31 * scale), body_x + body_w + int(26 * scale), body_y - int(8 * scale), body_x + body_w + int(60 * scale), body_y - int(8 * scale), color)
        painter.setPen(QPen(QColor("#2c3e50"), max(1, int(2 * scale))))
        for y in (6, 14):
            painter.drawLine(body_x + body_w + int(24 * scale), body_y + int(y * scale), body_x + body_w + int(66 * scale), body_y + int((y - 8) * scale))
            painter.drawLine(body_x + body_w + int(20 * scale), body_y + int(y * scale), body_x + body_w - int(18 * scale), body_y + int((y - 6) * scale))

    def _draw_chipmunk(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, body_h = self._draw_base_quadruped(painter, cx, cy, scale, color, pose, tail_style="fluffy")
        painter.setPen(QPen(QColor("#fefae0"), max(2, int(4 * scale))))
        for offset in (15, 30):
            painter.drawLine(body_x + int(offset * scale), body_y + int(6 * scale), body_x + int((offset + 12) * scale), body_y + body_h - int(6 * scale))

    def _draw_unicorn(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, _ = self._draw_base_quadruped(painter, cx, cy, scale, color, pose, head_long=True)
        painter.setPen(QPen(QColor("#8338ec"), max(2, int(4 * scale))))
        painter.drawArc(body_x - int(36 * scale), body_y + int(2 * scale), int(64 * scale), int(62 * scale), 90 * 16, 220 * 16)
        horn = QPainterPath()
        horn.moveTo(body_x + body_w + int(32 * scale), body_y - int(48 * scale))
        horn.lineTo(body_x + body_w + int(18 * scale), body_y - int(16 * scale))
        horn.lineTo(body_x + body_w + int(42 * scale), body_y - int(15 * scale))
        horn.closeSubpath()
        painter.setBrush(QColor("#ffcad4"))
        painter.setPen(QPen(QColor("#ff006e"), max(1, int(2 * scale))))
        painter.drawPath(horn)
        painter.setPen(QPen(QColor("#ff006e"), max(2, int(3 * scale))))
        painter.drawLine(body_x + int(22 * scale), body_y - int(20 * scale), body_x + int(78 * scale), body_y - int(34 * scale))

    def _draw_elephant(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, *, mammoth: bool, pose: int) -> None:
        body_x, body_y, body_w, _ = self._draw_base_quadruped(painter, cx, cy, scale * 1.08, color, pose, head_long=True, tail_style="short")
        painter.setBrush(color.lighter(112))
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
        painter.drawEllipse(body_x + body_w - int(8 * scale), body_y - int(10 * scale), int(48 * scale), int(62 * scale))
        painter.drawRoundedRect(body_x + body_w + int(34 * scale), body_y + int(10 * scale), int(24 * scale), int(70 * scale), 10, 10)
        painter.setPen(QPen(QColor("#fff8dc"), max(3, int(5 * scale))))
        painter.drawArc(body_x + body_w + int(10 * scale), body_y + int(28 * scale), int(34 * scale), int(48 * scale), 250 * 16, 110 * 16)
        if mammoth:
            painter.setPen(QPen(QColor("#5a3e2b"), max(2, int(4 * scale))))
            for x in range(body_x + 8, body_x + body_w, max(8, int(14 * scale))):
                painter.drawLine(x, body_y + int(5 * scale), x - int(8 * scale), body_y + int(28 * scale))

    def _draw_giraffe(self, painter: QPainter, cx: int, cy: int, scale: float, color: QColor, pose: int) -> None:
        body_x, body_y, body_w, _ = self._draw_base_quadruped(painter, cx, cy + int(18 * scale), scale, color, pose, tail_style="short")
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
        painter.drawRoundedRect(body_x + body_w - int(12 * scale), body_y - int(76 * scale), int(30 * scale), int(82 * scale), 12, 12)
        painter.drawEllipse(body_x + body_w, body_y - int(98 * scale), int(56 * scale), int(34 * scale))
        painter.setBrush(QColor("#8d5524"))
        painter.setPen(Qt.NoPen)
        for x, y in ((12, 10), (44, 18), (72, 4), (95, 26)):
            painter.drawEllipse(body_x + int(x * scale), body_y + int(y * scale), int(18 * scale), int(15 * scale))
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(2 * scale))))
        painter.drawLine(body_x + body_w + int(14 * scale), body_y - int(96 * scale), body_x + body_w + int(10 * scale), body_y - int(116 * scale))
        painter.drawLine(body_x + body_w + int(34 * scale), body_y - int(96 * scale), body_x + body_w + int(38 * scale), body_y - int(116 * scale))
        painter.setBrush(QColor("#8d5524"))
        painter.drawEllipse(body_x + body_w + int(5 * scale), body_y - int(122 * scale), int(10 * scale), int(10 * scale))
        painter.drawEllipse(body_x + body_w + int(33 * scale), body_y - int(122 * scale), int(10 * scale), int(10 * scale))

    def _draw_stage_marks(self, painter: QPainter, stage: str, cx: int, cy: int, scale: float) -> None:
        if stage == "elder":
            painter.setPen(QPen(QColor("#ced4da"), max(2, int(4 * scale))))
            painter.drawLine(cx + int(42 * scale), cy + int(46 * scale), cx + int(70 * scale), cy + int(86 * scale))
            painter.setBrush(QColor("#ced4da"))
            painter.drawEllipse(cx + int(30 * scale), cy - int(42 * scale), int(26 * scale), int(16 * scale))
        elif stage == "dementia":
            painter.setPen(QPen(QColor("#6c757d"), max(2, int(3 * scale))))
            painter.drawLine(cx + int(44 * scale), cy + int(40 * scale), cx + int(76 * scale), cy + int(92 * scale))
            painter.setFont(QFont("Segoe UI", max(14, int(18 * scale)), QFont.Bold))
            painter.setPen(QColor("#8338ec"))
            painter.drawText(cx - int(82 * scale), cy - int(76 * scale), "?")
            painter.drawText(cx + int(70 * scale), cy - int(62 * scale), "?")

    def _draw_coffin(self, painter: QPainter) -> None:
        cx, cy = 210, 168
        coffin = QPainterPath()
        coffin.moveTo(cx - 54, cy - 84)
        coffin.lineTo(cx + 54, cy - 84)
        coffin.lineTo(cx + 72, cy + 70)
        coffin.lineTo(cx + 36, cy + 102)
        coffin.lineTo(cx - 36, cy + 102)
        coffin.lineTo(cx - 72, cy + 70)
        coffin.closeSubpath()
        painter.setBrush(QColor("#6f4e37"))
        painter.setPen(QPen(QColor("#2c3e50"), 4))
        painter.drawPath(coffin)
        painter.setPen(QPen(QColor("#f8f9fa"), 5))
        painter.drawLine(cx, cy - 38, cx, cy + 38)
        painter.drawLine(cx - 24, cy - 6, cx + 24, cy - 6)

    def _draw_egg(self, painter: QPainter, cx: int, cy: int, scale: float = 1.0) -> None:
        cy = cy + (3 if [0, 1, 2, 1][self.frame % 4] == 1 else -2)
        w = int(108 * scale)
        h = int(132 * scale)
        painter.setPen(QPen(QColor("#2c3e50"), max(2, int(3 * scale))))
        painter.setBrush(QColor("#fff3b0"))
        painter.drawEllipse(cx - w // 2, cy - h // 2, w, h)
        painter.setPen(QPen(QColor("#ff006e"), max(2, int(3 * scale))))
        painter.drawLine(cx - int(30 * scale), cy - int(4 * scale), cx - int(10 * scale), cy + int(14 * scale))
        painter.drawLine(cx - int(10 * scale), cy + int(14 * scale), cx + int(10 * scale), cy - int(4 * scale))
        painter.drawLine(cx + int(10 * scale), cy - int(4 * scale), cx + int(30 * scale), cy + int(14 * scale))

    def _draw_animal_features(self, painter: QPainter, animal: str, cx: int, cy: int, body_color: QColor, movement: int) -> None:
        painter.setPen(QPen(QColor("#2c3e50"), 3))
        if animal == "tiger":
            painter.setBrush(QColor("#2c3e50"))
            for x in (-38, -8, 24):
                painter.drawRect(cx + x, cy - 47, 8, 34)
            self._draw_triangle(painter, cx - 34, cy - 68, cx - 12, cy - 50, cx - 52, cy - 48, body_color)
            self._draw_triangle(painter, cx + 34, cy - 68, cx + 12, cy - 50, cx + 52, cy - 48, body_color)
            painter.drawArc(cx + 48, cy + 6, 58, 42, 20 * 16, 250 * 16)
        elif animal == "elephant":
            painter.setBrush(body_color.lighter(120))
            painter.drawEllipse(cx - 106, cy - 28, 56, 76)
            painter.drawEllipse(cx + 50, cy - 28, 56, 76)
            painter.setBrush(body_color.darker(110))
            painter.drawRoundedRect(cx - 14, cy + 8, 28, 66, 12, 12)
        elif animal == "giraffe":
            painter.setBrush(body_color)
            painter.drawRoundedRect(cx - 20, cy - 112, 40, 68, 18, 18)
            painter.setBrush(QColor("#8d5524"))
            for x, y in [(-34, -30), (16, -40), (-8, 0), (28, 12)]:
                painter.drawEllipse(cx + x, cy + y, 18, 16)
            painter.drawLine(cx - 14, cy - 112, cx - 18, cy - 130)
            painter.drawLine(cx + 14, cy - 112, cx + 18, cy - 130)
            painter.drawEllipse(cx - 23, cy - 136, 10, 10)
            painter.drawEllipse(cx + 13, cy - 136, 10, 10)
        elif animal == "chipmunk":
            painter.setBrush(QColor("#a47148"))
            painter.drawArc(cx + 42, cy - 34, 84, 100, 80 * 16, 235 * 16)
            painter.setPen(QPen(QColor("#fefae0"), 4))
            painter.drawLine(cx - 34, cy - 42, cx - 42, cy + 28)
            painter.drawLine(cx + 34, cy - 42, cx + 42, cy + 28)
        elif animal == "dog":
            painter.setBrush(body_color.darker(112))
            painter.drawEllipse(cx - 91, cy - 50, 34, 78)
            painter.drawEllipse(cx + 57, cy - 50, 34, 78)
            painter.drawArc(cx + 50, cy + 4, 64, 48, 40 * 16, 210 * 16)
        elif animal == "cat":
            self._draw_triangle(painter, cx - 34, cy - 74, cx - 10, cy - 50, cx - 58, cy - 48, body_color)
            self._draw_triangle(painter, cx + 34, cy - 74, cx + 10, cy - 50, cx + 58, cy - 48, body_color)
            painter.setPen(QPen(QColor("#2c3e50"), 2))
            for y in (6, 14):
                painter.drawLine(cx - 18, cy + y, cx - 58, cy + y - 8)
                painter.drawLine(cx + 18, cy + y, cx + 58, cy + y - 8)
            painter.drawArc(cx + 48, cy + 0, 66, 66, 35 * 16, 245 * 16)
        elif animal == "mammoth":
            painter.setPen(QPen(QColor("#fff8dc"), 7))
            painter.drawArc(cx - 56, cy + 0, 42, 68, 260 * 16, 130 * 16)
            painter.drawArc(cx + 14, cy + 0, 42, 68, 150 * 16, 130 * 16)
            painter.setPen(QPen(QColor("#2c3e50"), 3))
            painter.setBrush(body_color.darker(105))
            painter.drawRoundedRect(cx - 15, cy + 10, 30, 58, 12, 12)
        elif animal == "unicorn":
            horn = QPainterPath()
            horn.moveTo(cx, cy - 102)
            horn.lineTo(cx - 14, cy - 56)
            horn.lineTo(cx + 14, cy - 56)
            horn.closeSubpath()
            painter.setBrush(QColor("#ffcad4"))
            painter.setPen(QPen(QColor("#ff006e"), 2))
            painter.drawPath(horn)
            painter.setPen(QPen(QColor("#8338ec"), 5))
            painter.drawArc(cx + 46, cy - 18 + movement // 3, 70, 60, 40 * 16, 220 * 16)

    def _draw_triangle(self, painter: QPainter, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, color: QColor) -> None:
        path = QPainterPath()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        path.lineTo(x3, y3)
        path.closeSubpath()
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#2c3e50"), 3))
        painter.drawPath(path)

    def _draw_mess(self, painter: QPainter) -> None:
        count = int(self.state.get("poops") or 0)
        painter.setPen(QPen(QColor("#5a3e2b"), 2))
        painter.setBrush(QColor("#8d5524"))
        for index in range(min(5, count)):
            x = 24 + index * 34
            y = 236
            painter.drawEllipse(x, y + 17, 28, 14)
            painter.drawEllipse(x + 5, y + 8, 18, 13)
            painter.drawEllipse(x + 10, y, 10, 11)

        pees = int(self.state.get("pees") or 0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 214, 10, 150))
        for index in range(min(5, pees)):
            painter.drawEllipse(240 + index * 27, 255 + (index % 2) * 8, 42, 16)

        vomits = int(self.state.get("vomits") or 0)
        painter.setBrush(QColor(126, 217, 87, 190))
        for index in range(min(4, vomits)):
            painter.drawEllipse(178 + index * 36, 222 + (index % 2) * 6, 34, 20)

    def _draw_status(self, painter: QPainter) -> None:
        state = self.state
        painter.setFont(QFont("Segoe UI", 18, QFont.Bold))
        painter.setPen(QColor("#2c3e50"))
        if state.get("sick"):
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(323, 206, 48, 40, 6, 6)
            painter.setPen(QPen(QColor("#d90429"), 5))
            painter.drawLine(347, 214, 347, 238)
            painter.drawLine(335, 226, 359, 226)
        if state.get("sleeping"):
            painter.setPen(QColor("#3a86ff"))
            painter.drawText(320, 80, "Z z z")
        if not state.get("alive", True):
            painter.setPen(QColor("#6c757d"))
            painter.drawText(QRect(0, 18, self.width(), 36), Qt.AlignCenter, "Нужен перезапуск")


def _button_style(color: str) -> str:
    return f"""
    QPushButton {{
        background-color: {color};
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 7px 12px;
    }}
    QPushButton:hover {{
        background-color: {_darken(color)};
    }}
    QPushButton:pressed {{
        background-color: #2c3e50;
    }}
    """


def _darken(color: str) -> str:
    qcolor = QColor(color)
    return qcolor.darker(115).name()


def _stage_scale(stage: str) -> float:
    if stage == "child":
        return 0.58
    if stage == "teen":
        return 0.76
    if stage == "adult":
        return 1.0
    if stage == "elder":
        return 0.88
    if stage == "dementia":
        return 0.76
    return 0.7


def _animal_color(animal: str, stage: str) -> QColor:
    colors = {
        "tiger": "#fb8500",
        "elephant": "#9aa0a6",
        "giraffe": "#ffbe0b",
        "chipmunk": "#a47148",
        "dog": "#d4a373",
        "cat": "#b8c0ff",
        "mammoth": "#7f5539",
        "unicorn": "#f8f9fa",
    }
    if animal in colors:
        return QColor(colors[animal])
    if stage == "child":
        return QColor("#fb8500")
    if stage == "teen":
        return QColor("#8338ec")
    if stage == "adult":
        return QColor("#06d6a0")
    return QColor("#ffbe0b")
