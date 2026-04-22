from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect, QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont

class CustomMessageBox(QDialog):
    """Кастомное окно уведомлений в стиле карточки пациента (оливковая гамма)."""
    def __init__(self, title, message, is_question=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.title = title
        self.message = message
        self.is_question = is_question
        self._drag_pos = QPoint()
        
        self.bg_color = "#f5f2e9"
        self.border_color = "#d1d1bc"
        self.accent_color = "#8a8a68"
        
        self._init_ui()

    def _init_ui(self):
        self.setMinimumWidth(450)
        self.setMinimumHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер
        self.bg_container = QWidget()
        self.bg_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.bg_color};
                border: 2px solid {self.border_color};
                border-radius: 15px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 5)
        self.bg_container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.bg_container)
        container_layout.setContentsMargins(25, 15, 25, 25)
        container_layout.setSpacing(15)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_lbl = QLabel(self.title.upper())
        title_lbl.setStyleSheet(f"color: {self.accent_color}; font-weight: 800; font-size: 13px; border: none; letter-spacing: 1px;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { color: #7a7a6a; font-size: 20px; border: none; background: transparent; } QPushButton:hover { color: #ef4444; }")
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Текст сообщения
        msg_lbl = QLabel(self.message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #2d2d24; font-size: 14px; border: none; line-height: 140%;")
        msg_lbl.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(msg_lbl, 1)
        
        # Кнопки
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        
        if self.is_question:
            self.yes_btn = QPushButton("ДА")
            self.no_btn = QPushButton("НЕТ")
            for b in [self.yes_btn, self.no_btn]:
                b.setFixedHeight(40)
                b.setMinimumWidth(100)
                b.setCursor(Qt.PointingHandCursor)
            
            self.yes_btn.setStyleSheet("""
                QPushButton { background: #5d5d3d; color: white; border: none; border-radius: 6px; font-weight: 800; }
                QPushButton:hover { background: #4a4a31; }
            """)
            self.no_btn.setStyleSheet("""
                QPushButton { background: #fdfdfa; color: #7e7e6d; border: 1px solid #c9c9b4; border-radius: 6px; font-weight: 700; }
                QPushButton:hover { background: #ebe8d5; }
            """)
            
            self.yes_btn.clicked.connect(self.accept)
            self.no_btn.clicked.connect(self.reject)
            
            btns_layout.addStretch()
            btns_layout.addWidget(self.no_btn)
            btns_layout.addWidget(self.yes_btn)
            btns_layout.addStretch()
        else:
            self.ok_btn = QPushButton("ПОНЯТНО")
            self.ok_btn.setFixedHeight(40)
            self.ok_btn.setMinimumWidth(150)
            self.ok_btn.setCursor(Qt.PointingHandCursor)
            self.ok_btn.setStyleSheet("""
                QPushButton { background: #5d5d3d; color: white; border: none; border-radius: 6px; font-weight: 800; }
                QPushButton:hover { background: #4a4a31; }
            """)
            self.ok_btn.clicked.connect(self.accept)
            
            btns_layout.addStretch()
            btns_layout.addWidget(self.ok_btn)
            btns_layout.addStretch()
            
        container_layout.addLayout(btns_layout)
        
        layout.addWidget(self.bg_container)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._dragging = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and getattr(self, '_dragging', False):
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPosition().toPoint()

    @staticmethod
    def show_info(parent, title, message):
        dlg = CustomMessageBox(title, message, is_question=False, parent=parent)
        return dlg.exec()

    @staticmethod
    def show_question(parent, title, message):
        dlg = CustomMessageBox(title, message, is_question=True, parent=parent)
        return dlg.exec() == QDialog.Accepted
