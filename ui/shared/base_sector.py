from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QWidget)
from PySide6.QtCore import Qt

class BaseSectorWidget(QFrame):
    """Базовый класс для всех секторов ремкарты"""
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        
        # Основной лейаут без отступов
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.label = QLabel(f"Сектор {name}")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; color: #495057; background: #e9ecef; border: 1px solid #dee2e6;")
        self.main_layout.addWidget(self.label)
        
        # Контейнер для реального контента - БЕЗ ФОНА И РАМОК
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent; border: none;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.main_layout.addWidget(self.container)

    def set_content(self, widget):
        """Вспомогательный метод для быстрой смены контента"""
        for i in reversed(range(self.container_layout.count())): 
            self.container_layout.itemAt(i).widget().setParent(None)
        if widget:
            # НЕ сбрасываем стили у вставляемого виджета, чтобы работали кастомные границы
            self.container_layout.addWidget(widget)

    def set_title(self, text):
        self.label.setText(text)
