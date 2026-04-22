from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel)
from PySide6.QtCore import Qt
from rem_card.ui.shared.base_sector import BaseSectorWidget

class SectorW1b(BaseSectorWidget):
    """Сектор W1b, отображаемый в режиме списка коек (вместо 1б)."""
    def __init__(self, parent=None):
        super().__init__("W1b", parent)
        self.label.hide()
        self.setFrameStyle(BaseSectorWidget.NoFrame)
        self.setStyleSheet("background: transparent;")
        self.init_ui()

    def init_ui(self):
        # Отступ 5px сверху от границы сектора до рамки
        if self.layout():
            self.layout().setContentsMargins(0, 6, 0, 0)

        # 1. Основной контейнер с рамкой
        self.main_container = QWidget()
        self.main_container.setObjectName("sector_w1b_main_container")
        self.main_layout_v = QVBoxLayout(self.main_container)
        
        # Отступы 3px со всех сторон внутри контейнера
        self.main_layout_v.setContentsMargins(3, 3, 3, 3)
        self.main_layout_v.setSpacing(0)
        
        # 2. Надпись в центре
        self.empty_label = QLabel("Сектор W1b")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #bdc3c7; font-style: italic;")
        self.main_layout_v.addWidget(self.empty_label)

        # QSS стиль
        self.main_container.setStyleSheet("""
            QWidget#sector_w1b_main_container {
                background-color: #f8f9fa;
                border: 1.5px solid #bdc3c7;
                border-radius: 5px;
            }
        """)

        self.set_content(self.main_container)
