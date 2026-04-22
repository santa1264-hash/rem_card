from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QWidget, QHBoxLayout, QScrollArea, QLabel
from rem_card.Rao_jornal.ui.custom_dialogs import CustomMessageBox
from PySide6.QtCore import Qt, QDateTime, QPoint, QSize, QSettings
from PySide6.QtGui import QColor, QMouseEvent, QCursor
from rem_card.Rao_jornal.database.db_manager import DBManager
from rem_card.Rao_jornal.services.patient_service import PatientService
from rem_card.Rao_jornal.services.mkb_service import MKBService
from rem_card.Rao_jornal.domain.patient import Patient
from rem_card.Rao_jornal.domain.admission import Admission
from rem_card.Rao_jornal.domain.ivl_episode import IVLEpisode
from datetime import datetime

from rem_card.Rao_jornal.ui.tabs.general_tab import GeneralTabWidget
from rem_card.Rao_jornal.ui.tabs.diagnosis_tab import DiagnosisTabWidget
from rem_card.Rao_jornal.ui.tabs.transfusions_tab import TransfusionsTabWidget
from rem_card.Rao_jornal.ui.tabs.ivl_tab import IVLTabWidget
from rem_card.Rao_jornal.ui.tabs.transfer_tab import TransferTabWidget

class PatientForm(QDialog):
    def __init__(self, db_manager: DBManager, patient_service: PatientService, bed_number: int, patient: Patient = None, admission: Admission = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.patient_service = patient_service
        self.mkb_service = MKBService()
        self.bed_number = bed_number
        self.patient = patient
        self.admission = admission
        self.is_new_admission = (patient is None and admission is None)
        self.patient_transfered_or_dead = False
        
        self._margin = 10
        self._cursor = QCursor()
        self._resizing = False
        self._dragging = False
        self._drag_pos = QPoint()
        self._resize_edges = Qt.Edge(0)

        self.bg_color = "#f5f2e9"
        self.border_color = "#d1d1bc"

        self.setWindowTitle(f"Карта пациента - Койка {self.bed_number}")
        self.setMinimumSize(800, 600)
        self.resize(980, 770)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        # Main background container
        self.bg_container = QWidget(self)
        self.bg_container.setObjectName("bg_container")
        self.bg_container.setMouseTracking(True)
        self.bg_container.setStyleSheet(f"""
            QWidget#bg_container {{
                background-color: {self.bg_color};
                border: 2px solid {self.border_color};
                border-radius: 5px;
            }}
        """)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.shadow.setOffset(0, 5)
        self.bg_container.setGraphicsEffect(self.shadow)

        self.layout_container = QVBoxLayout(self)
        self.layout_container.setContentsMargins(10, 10, 10, 10)
        self.layout_container.addWidget(self.bg_container)

        self.main_layout = QVBoxLayout(self.bg_container)
        self.main_layout.setContentsMargins(16, 8, 16, 16)
        self.main_layout.setSpacing(10)

        controls_layout = QHBoxLayout()
        self.header_panel = QWidget()
        self.header_panel.setFixedHeight(40)
        self.header_panel.setStyleSheet("background: transparent;")
        self.header_panel_layout = QHBoxLayout(self.header_panel)
        self.header_panel_layout.setContentsMargins(10, 0, 0, 0)
        
        self.title_label = QLabel(f"КАРТОЧКА ПАЦИЕНТА — КОЙКА {self.bed_number}")
        self.title_label.setStyleSheet("color: #4a4a3a; font-size: 13px; font-weight: 800; letter-spacing: 1px; background: transparent;")
        self.header_panel_layout.addWidget(self.title_label)
        self.header_panel_layout.addStretch()
        
        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setCursor(Qt.PointingHandCursor)
        self.minimize_button.setStyleSheet("""
            QPushButton { background: transparent; color: #7a7a6a; font-size: 18px; border: none; }
            QPushButton:hover { background: #e8e4d5; color: #1e293b; border-radius: 5px; }
        """)
        self.minimize_button.clicked.connect(self.showMinimized)
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton { background: transparent; color: #7a7a6a; font-size: 22px; border: none; }
            QPushButton:hover { background: #ef4444; color: white; border-radius: 5px; }
        """)
        self.close_button.clicked.connect(self.reject)
        
        self.header_panel_layout.addWidget(self.minimize_button)
        self.header_panel_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.header_panel)

        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.main_layout.addWidget(self.content_container, 1)

        self._init_ui()
        self._load_data()
        self._restore_geometry()

    def _init_ui(self):
        self.general_tab = GeneralTabWidget(self)
        self.diagnosis_tab = DiagnosisTabWidget(self.mkb_service, self, show_operations=False)
        self.transfusions_tab = TransfusionsTabWidget(self.patient_service, self)
        self.ivl_tab = IVLTabWidget(self)
        self.transfer_tab = TransferTabWidget(self)

        # Синхронизация коллбэков для валидации дат и статусов
        self.ivl_tab.set_datetime_getters(
            get_adm=lambda: self.general_tab.admission_datetime_input.dateTime(),
            get_transfer=lambda: self.transfer_tab.transfer_datetime_input.dateTime(),
            get_death=lambda: self.transfer_tab.death_datetime_input.dateTime()
        )
        self.transfer_tab.set_callbacks(
            get_adm=lambda: self.general_tab.admission_datetime_input.dateTime(),
            get_main_prof=lambda: self.general_tab.department_profile_input.currentText(),
            on_death_cb=self.ivl_tab.close_active_ivl_if_dead,
            on_dur_cb=None,
            is_ivl_active=self.ivl_tab.is_currently_on_ivl,
            get_last_extubation=self.ivl_tab.get_last_extubation_dt
        )

        # Возвращаем стандартный вид ComboBox и SpinBox с базовой стилизацией рамок
        tab_styling = f"""
            QWidget {{ background-color: {self.bg_color}; }}
            QLabel {{ color: #4a4a3f; font-size: 13px; font-weight: 600; background: transparent; }}
            
            QLineEdit, QComboBox, QSpinBox, QDateTimeEdit {{
                padding: 8px;
                border: 1px solid #c9c9b4;
                border-radius: 5px;
                background: #fdfdfa;
                color: #2d2d24;
            }}
            
            QSpinBox::up-button {{
                width: 20px;
            }}
            
            QSpinBox::down-button {{
                width: 20px;
            }}
            
            QDateTimeEdit::up-button, QDateTimeEdit::down-button {{
                width: 0px;
                border: none;
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateTimeEdit:focus {{
                border: 1px solid #8a8a68;
                background: white;
            }}
            
            QGroupBox {{
                border: 1px solid #c9c9b4;
                border-radius: 5px;
                margin-top: 20px;
                padding-top: 15px;
                font-weight: 800;
                color: #4a4a3a;
                background-color: #f0ede4;
            }}
            
            QPushButton {{
                background: #e8e4d5;
                border: 1px solid #c9c9b4;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: 600;
                color: #4a4a3a;
            }}
            QPushButton:hover {{ background: #dad6c2; }}
            
            /* Стилизация календаря */
            QCalendarWidget QToolButton {{
                color: #7a7a6a;
                background-color: transparent;
                border: none;
            }}
            QCalendarWidget QToolButton:hover {{
                color: #000000;
            }}
            QCalendarWidget QToolButton#qt_calendar_monthbutton {{
                margin-left: -6px;
            }}
            QCalendarWidget QToolButton::menu-indicator {{
                subcontrol-position: center;
                image: none;
            }}
            QCalendarWidget QMenu {{
                margin-left: -6px;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: #f0ede4;
                border-bottom: 1px solid #c9c9b4;
            }}
            QDateTimeEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #c9c9b4;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}
            QDateTimeEdit::down-arrow {{
                image: none; /* Убираем блокировку изображения */
                /* Используем стандартную стрелочку, если она есть, или не переопределяем */
            }}
        """
        
        self.general_tab.setStyleSheet(tab_styling)
        self.diagnosis_tab.setStyleSheet(tab_styling)
        label_column_width = 250
        if hasattr(self.general_tab, "set_label_column_width"):
            self.general_tab.set_label_column_width(label_column_width)
        if hasattr(self.diagnosis_tab, "set_label_column_width"):
            self.diagnosis_tab.set_label_column_width(label_column_width)

        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setFrameShape(QScrollArea.NoFrame)
        self.form_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {self.border_color};
                background: {self.bg_color};
                border-radius: 5px;
            }}
        """)

        self.form_page = QWidget()
        self.form_page.setStyleSheet(f"background-color: {self.bg_color};")
        self.form_page_layout = QVBoxLayout(self.form_page)
        self.form_page_layout.setContentsMargins(0, 0, 0, 0)
        self.form_page_layout.setSpacing(2)

        self.general_section_title = QLabel("ОБЩИЕ ДАННЫЕ")
        self.general_section_title.setStyleSheet(
            "color: #4a4a3a; font-size: 12px; font-weight: 800; letter-spacing: 1px; margin: 10px 24px 0 24px; background: transparent;"
        )

        self.diagnosis_section_title = QLabel("ДИАГНОЗ")
        self.diagnosis_section_title.setStyleSheet(
            "color: #4a4a3a; font-size: 12px; font-weight: 800; letter-spacing: 1px; margin: 0 24px 0 24px; background: transparent;"
        )

        # В журнале оставляем единую страницу: общие данные + блок диагноза.
        # Клинические вкладки (ИВЛ/трансфузии/перевод) скрыты из UI и остаются в коде.
        self.form_page_layout.addWidget(self.general_section_title)
        self.form_page_layout.addWidget(self.general_tab)
        self.form_page_layout.addWidget(self.diagnosis_section_title)
        self.form_page_layout.addWidget(self.diagnosis_tab)
        self.form_page_layout.addStretch(1)

        self.form_scroll.setWidget(self.form_page)
        self.content_layout.addWidget(self.form_scroll)

        btns_layout = QHBoxLayout()
        btns_layout.setContentsMargins(0, 10, 0, 0)
        
        self.cancel_button = QPushButton("ОТМЕНИТЬ")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setFixedHeight(45)
        self.cancel_button.setStyleSheet("""
            QPushButton { background: #f5f3e9; border: 1px solid #dcdcc6; border-radius: 5px; color: #7e7e6d; font-weight: 700; font-size: 12px; }
            QPushButton:hover { background: #ebe8d5; color: #2d2d24; }
        """)
        self.cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("СОХРАНИТЬ КАРТОЧКУ")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setFixedHeight(45)
        self.save_button.setStyleSheet("""
            QPushButton { background: #5d5d3d; border: none; border-radius: 5px; color: white; font-weight: 800; font-size: 12px; }
            QPushButton:hover { background: #4a4a31; }
            QPushButton:pressed { background: #3a3a26; }
        """)
        self.save_button.clicked.connect(self._save_data)
        
        btns_layout.addWidget(self.cancel_button, 1)
        btns_layout.addWidget(self.save_button, 2)
        self.main_layout.addLayout(btns_layout)

    def _load_data(self):
        if not self.is_new_admission:
            self.general_tab.set_data(self.patient, self.admission)
            self.transfusions_tab.set_admission(self.admission)
            if self.admission:
                self.diagnosis_tab.set_data(self.admission, [])
                ivl_episodes = self.patient_service.get_ivl_episodes_by_admission(self.admission.id)
                self.ivl_tab.set_data(ivl_episodes)
                self.transfer_tab.set_data(self.admission)

    def _restore_geometry(self):
        settings = QSettings("RAO3", "PatientForm")
        geom = settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(980, 770)
        pos = settings.value("pos")
        # Если restoreGeometry() отработал, отдельный pos не применяем, чтобы
        # не создавать конфликты/дергание геометрии.
        if pos and not geom:
            self.move(pos)
        self._clamp_to_screen()

    def _save_geometry(self):
        settings = QSettings("RAO3", "PatientForm")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("pos", self.pos())

    def _clamp_to_screen(self):
        screen = self.screen()
        if not screen:
            return

        available = screen.availableGeometry()
        min_w = self.minimumWidth()
        min_h = self.minimumHeight()

        # Не даем форме быть больше рабочей области экрана.
        target_w = min(self.width(), max(min_w, available.width() - 24))
        target_h = min(self.height(), max(min_h, available.height() - 24))
        target_w = max(min_w, target_w)
        target_h = max(min_h, target_h)
        if target_w != self.width() or target_h != self.height():
            self.resize(target_w, target_h)

        # Возвращаем окно в видимую область.
        x = min(max(self.x(), available.left()), available.right() - self.width() + 1)
        y = min(max(self.y(), available.top()), available.bottom() - self.height() + 1)
        if x != self.x() or y != self.y():
            self.move(x, y)

    def _validate_input(self):
        gen = self.general_tab.get_data()
        if not gen["history_number"] or not gen["full_name"]:
            CustomMessageBox.show_info(self, "Ошибка", "Заполните номер ИБ и ФИО пациента")
            return False
        if not self.diagnosis_tab.get_data()["diagnosis_text"]:
            CustomMessageBox.show_info(self, "Ошибка", "Необходимо указать диагноз")
            return False
        return True

    def _save_data(self):
        if not self._validate_input(): return
        try:
            gen_data = self.general_tab.get_data()
            diag_data = self.diagnosis_tab.get_data()
            transfer_data = self.transfer_tab.get_data()
            patient_data = {"full_name": gen_data["full_name"]}
            admission_data = {
                "patient_id": self.patient.id if self.patient else 0,
                "bed_number": self.bed_number,
                "history_number": gen_data["history_number"],
                "admission_datetime": gen_data["admission_datetime"],
                "patient_age": gen_data["age_value"],
                "patient_months": gen_data["months"],
                "patient_age_unit": gen_data["age_unit"],
                "patient_gender": gen_data["gender"],
                "diagnosis_code": diag_data["diagnosis_code"],
                "diagnosis_text": diag_data["diagnosis_text"],
                "department_profile": gen_data["department_profile"],
                "source_department": gen_data["source_department"],
                "transfer_datetime": transfer_data["transfer_datetime"],
                "transfer_department": transfer_data["transfer_department"],
                "transfer_lpu": transfer_data["transfer_lpu"],
                "transfer_lpu_other": transfer_data["transfer_lpu_other"],
                "death_datetime": transfer_data["death_datetime"],
                "outcome": transfer_data["outcome"],
                "updated_at": datetime.now()
            }
            ivls = [IVLEpisode(admission_id=self.admission.id if self.admission else 0, **ep) for ep in self.ivl_tab.get_data()]
            if self.is_new_admission:
                adm_id = self.patient_service.create_patient_and_admission(Patient(**patient_data), Admission(**admission_data))
                if adm_id:
                    self.patient_service.update_ivl_episodes(adm_id, ivls)
                    
                    # Сохраняем трансфузии для нового поступления
                    pending_transfusions = self.transfusions_tab.get_pending_transfusions()
                    if pending_transfusions:
                        self.patient_service.update_transfusions(adm_id, pending_transfusions)
                        self.transfusions_tab.clear_pending()
                        
                    self._save_geometry()
                    self.accept()
            else:
                self.patient.full_name = patient_data["full_name"]
                for k, v in admission_data.items(): setattr(self.admission, k, v)

                if self.patient_service.update_patient_and_admission(self.patient, self.admission):
                    self.patient_service.update_ivl_episodes(self.admission.id, ivls)
                    
                    # Для существующих поступлений трансфузии уже могут быть в БД, 
                    # но сохраним pending, если они появились (например, добавлены до сохранения карточки)
                    pending_transfusions = self.transfusions_tab.get_pending_transfusions()
                    if pending_transfusions:
                        self.patient_service.update_transfusions(self.admission.id, pending_transfusions)
                        self.transfusions_tab.clear_pending()
                        
                    self._save_geometry()
                    self.accept()
        except Exception as e:
            CustomMessageBox.show_info(self, "Ошибка", f"Не удалось сохранить данные:\n{e}")

    def reject(self):
        self._save_geometry()
        self.mkb_service.close_connection()
        super().reject()

    def accept(self):
        self._save_geometry()
        self.mkb_service.close_connection()
        super().accept()

    def _get_resize_edges(self, pos):
        edges = Qt.Edge(0)
        if pos.x() < self._margin: edges |= Qt.LeftEdge
        if pos.x() > self.width() - self._margin: edges |= Qt.RightEdge
        if pos.y() < self._margin: edges |= Qt.TopEdge
        if pos.y() > self.height() - self._margin: edges |= Qt.BottomEdge
        return edges

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            edges = self._get_resize_edges(event.pos())
            if edges:
                self._resizing = True
                self._dragging = False
                self._resize_edges = edges
                wh = self.windowHandle()
                if wh:
                    wh.startSystemResize(edges)
                event.accept()
                return
            elif self.childAt(event.pos()) in [self.bg_container, self.header_panel, self.title_label, None]:
                self._resizing = False
                self._drag_pos = event.globalPosition().toPoint() - self.pos()
                self._dragging = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            super().mouseMoveEvent(event)
            return

        edges = self._get_resize_edges(event.pos())
        if edges == (Qt.LeftEdge | Qt.TopEdge) or edges == (Qt.RightEdge | Qt.BottomEdge): self.setCursor(Qt.SizeFDiagCursor)
        elif edges == (Qt.RightEdge | Qt.TopEdge) or edges == (Qt.LeftEdge | Qt.BottomEdge): self.setCursor(Qt.SizeBDiagCursor)
        elif edges & (Qt.LeftEdge | Qt.RightEdge): self.setCursor(Qt.SizeHorCursor)
        elif edges & (Qt.TopEdge | Qt.BottomEdge): self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)

        if event.buttons() & Qt.LeftButton and getattr(self, '_dragging', False) and not self._resizing:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

        super().mouseMoveEvent(event)
