import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Signal

class NurseSector8Panel(QWidget):
    """Панель управления медсестры в Секторе 8."""
    exit_clicked = Signal()
    refresh_clicked = Signal()
    add_patient_clicked = Signal()
    bonus_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Путь к иконкам (на уровень выше, чем у врача)
        self.icon_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "icon")
        self.icon_dir = os.path.normpath(self.icon_dir)
        self.init_ui()

    def init_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(10)

        self.layout.addStretch()

        # Общий стиль для кнопок
        button_style = """
            QPushButton {
                font-size: 13px; 
                font-weight: bold; 
                padding: 4px 12px; 
                background-color: #ecf0f1; 
                color: #2c3e50; 
                border-radius: 5px; 
                border: 1.5px solid #bdc3c7;
            }
            QPushButton:hover {
                background-color: #dcdde1;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
            QPushButton:disabled {
                background-color: #f1f2f6;
                color: #a4b0be;
                border: 1px solid #dcdde1;
            }
        """

        # 1. Кнопка Обновить
        self.btn_refresh = QPushButton(" Обновить")
        refresh_icon = os.path.join(self.icon_dir, "refresh.png")
        self.btn_refresh.setIcon(QIcon(refresh_icon))
        self.btn_refresh.setIconSize(QSize(18, 18))
        self.btn_refresh.setMinimumHeight(32)
        self.btn_refresh.setStyleSheet(button_style)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)

        # Кнопка Добавить пациента (доступна только в режиме списка коек)
        self.btn_add_patient = QPushButton(" Добавить пациента")
        add_icon = os.path.join(self.icon_dir, "add.png")
        self.btn_add_patient.setIcon(QIcon(add_icon))
        self.btn_add_patient.setIconSize(QSize(18, 18))
        self.btn_add_patient.setMinimumHeight(32)
        self.btn_add_patient.setStyleSheet(button_style)
        self.btn_add_patient.clicked.connect(self.add_patient_clicked.emit)

        # Кнопка Бонус
        self.btn_bonus = QPushButton(" Бонус")
        bonus_icon = os.path.join(self.icon_dir, "bonus.png")
        self.btn_bonus.setIcon(QIcon(bonus_icon))
        self.btn_bonus.setIconSize(QSize(18, 18))
        self.btn_bonus.setMinimumHeight(32)
        self.btn_bonus.setStyleSheet(button_style)
        self.btn_bonus.clicked.connect(self.bonus_clicked.emit)

        # 2. Кнопка Назад
        self.btn_back = QPushButton(" Назад")
        back_icon = os.path.join(self.icon_dir, "back.png")
        self.btn_back.setIcon(QIcon(back_icon))
        self.btn_back.setIconSize(QSize(18, 18))
        self.btn_back.setMinimumHeight(32)
        self.btn_back.setStyleSheet(button_style)

        # 3. Кнопка Выход
        self.btn_exit = QPushButton(" Выход")
        exit_icon = os.path.join(self.icon_dir, "exit.png")
        self.btn_exit.setIcon(QIcon(exit_icon))
        self.btn_exit.setIconSize(QSize(18, 18))
        self.btn_exit.setMinimumHeight(32)
        self.btn_exit.setStyleSheet(button_style)
        self.btn_exit.clicked.connect(self.exit_clicked.emit)

        # Добавляем только разрешенные кнопки
        self.layout.addWidget(self.btn_refresh)
        self.layout.addWidget(self.btn_add_patient)
        self.layout.addWidget(self.btn_bonus)
        self.layout.addWidget(self.btn_back)
        self.layout.addWidget(self.btn_exit)

    def set_add_patient_enabled(self, enabled: bool):
        if hasattr(self, "btn_add_patient"):
            self.btn_add_patient.setEnabled(enabled)
