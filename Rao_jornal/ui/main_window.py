from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QDialog, QLabel, QGridLayout, QHBoxLayout, QGraphicsBlurEffect, QScrollArea, QGraphicsDropShadowEffect, QFrame
from PySide6.QtCore import Qt, QPoint, QRect, QSettings
from PySide6.QtGui import QFont, QColor, QMouseEvent, QCursor
from typing import TYPE_CHECKING

from rem_card.Rao_jornal.ui.bed_widget import BedWidget
from rem_card.Rao_jornal.ui.side_patient_card import SidePatientCard

if TYPE_CHECKING:
    from rem_card.Rao_jornal.database.db_manager import DBManager
    from rem_card.Rao_jornal.services.patient_service import PatientService

class MainWindow(QMainWindow):
    def __init__(
        self,
        db_manager: DBManager,
        patient_service: PatientService,
        parent=None,
        embedded: bool = False,
        show_db_button: bool = True,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.patient_service = patient_service
        self.embedded = embedded
        self.show_db_button = show_db_button
        
        self.setWindowTitle("Журнал больных — ОАР №3")
        self.setGeometry(100, 100, 1400, 850)

        if self.embedded:
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.bg_color = "#f2f3ee" 
        self.border_color = "#c9c9b4" 
        self.accent_color = "#8a8a68"
        self.text_color = "#2d2d24" 
        self.header_bg = "#e6e8de" 

        self._drag_pos = QPoint()
        self._is_maximized = False
        self._margin = 10
        self._resizing = False

        self._init_ui()
        if not self.embedded:
            self._load_settings()

    def _init_ui(self):
        self.central_container = QWidget()
        self.central_container.setMouseTracking(True)
        self.setCentralWidget(self.central_container)
        
        self.root_layout = QVBoxLayout(self.central_container)
        if self.embedded:
            # Небольшой верхний отступ рамки во встроенном режиме.
            self.root_layout.setContentsMargins(0, 5, 0, 0)
        else:
            self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(0)

        self.root_container = QWidget()
        self.root_container.setObjectName("root_container")
        self.root_container.setMouseTracking(True)
        container_radius = "10px" if self.embedded else "15px"
        self.root_container.setStyleSheet(f"""
            QWidget#root_container {{
                background-color: {self.bg_color};
                border: 2px solid {self.border_color};
                border-radius: {container_radius};
            }}
        """)
        
        if not self.embedded:
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(30)
            self.shadow.setColor(QColor(0, 0, 0, 40))
            self.shadow.setOffset(0, 5)
            self.root_container.setGraphicsEffect(self.shadow)
        
        self.root_layout.addWidget(self.root_container)

        self.main_layout = QVBoxLayout(self.root_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. CUSTOM TITLE BAR (только для отдельного окна)
        if not self.embedded:
            self.title_bar = QWidget()
            self.title_bar.setFixedHeight(45)
            self.title_bar.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.header_bg};
                    border-bottom: 1px solid {self.border_color};
                    border-top-left-radius: 13px;
                    border-top-right-radius: 13px;
                }}
            """)
            title_bar_layout = QHBoxLayout(self.title_bar)
            title_bar_layout.setContentsMargins(15, 0, 5, 0)

            self.window_title_label = QLabel("ЖУРНАЛ БОЛЬНЫХ — ОТДЕЛЕНИЕ РЕАНИМАЦИИ №3")
            self.window_title_label.setStyleSheet(f"color: {self.accent_color}; font-weight: 800; font-size: 11px; letter-spacing: 1px; border: none;")
            title_bar_layout.addWidget(self.window_title_label)
            title_bar_layout.addStretch()

            self.btn_min = self._create_window_btn("−", self.showMinimized)
            self.btn_max = self._create_window_btn("□", self._toggle_maximized)
            self.btn_close = self._create_window_btn("×", self._safe_close, is_close=True)
            
            title_bar_layout.addWidget(self.btn_min)
            title_bar_layout.addWidget(self.btn_max)
            title_bar_layout.addWidget(self.btn_close)
            self.main_layout.addWidget(self.title_bar)

        # 2. CONTENT AREA
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        content_margin = 12 if self.embedded else 20
        self.content_layout.setContentsMargins(content_margin, content_margin, content_margin, content_margin)
        self.content_layout.setSpacing(15) # УМЕНЬШИЛ СПЕЙСИНГ МЕЖДУ СЕТКОЙ И КАРТОЧКОЙ
        if self.embedded:
            # Центрируем весь контент журнала в области Rem-карты.
            self.main_layout.addStretch(1)
            self.main_layout.addWidget(self.content_container, 0, Qt.AlignCenter)
            self.main_layout.addStretch(1)
        else:
            self.main_layout.addWidget(self.content_container, 1)

        # Left Column
        self.left_column = QWidget()
        self.left_column.setFixedWidth(780)
        self.left_layout = QVBoxLayout(self.left_column)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)
        self.content_layout.addWidget(self.left_column, 0, Qt.AlignTop)

        # Header Card
        header_card = QFrame()
        header_card.setObjectName("header_card")
        header_card.setFixedHeight(80)
        header_card.setFixedWidth(250 * 3 + 15 * 2) # 780px - ширина 3 коек + отступы
        header_card.setStyleSheet(f"""
            QFrame#header_card {{
                background: #fdfdfa;
                border: 2px solid {self.border_color};
                border-radius: 12px;
            }}
        """)
        header_card_layout = QVBoxLayout(header_card)
        header_card_layout.setContentsMargins(15, 10, 15, 10)
        header_card_layout.setSpacing(2)

        self.header_label = QLabel("ЖУРНАЛ БОЛЬНЫХ")
        self.header_label.setStyleSheet(f"color: {self.text_color}; font-size: 24px; font-weight: 800; letter-spacing: 2px; background: transparent; border: none;")
        self.header_label.setAlignment(Qt.AlignCenter)
        
        self.sub_header_label = QLabel("ОАР №3 г. Амурск")
        self.sub_header_label.setStyleSheet(f"color: {self.accent_color}; font-size: 12px; font-weight: 600; background: transparent; text-transform: uppercase; border: none;")
        self.sub_header_label.setAlignment(Qt.AlignCenter)

        header_card_layout.addWidget(self.header_label)
        header_card_layout.addWidget(self.sub_header_label)
        self.left_layout.addWidget(header_card, 0, Qt.AlignLeft)

        # Grid for beds
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15) # УМЕНЬШИЛ СПЕЙСИНГ
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.left_layout.addWidget(self.grid_container)
        self.left_layout.addStretch()

        # Database button
        self.test_db_button = None
        if self.show_db_button:
            self.test_db_button = QPushButton("БАЗА ДАННЫХ")
            self.test_db_button.setCursor(Qt.PointingHandCursor)
            self.test_db_button.setFixedWidth(180)
            self.test_db_button.setFixedHeight(40)
            self.test_db_button.setStyleSheet(f"""
                QPushButton {{
                    background: #fdfdfa;
                    color: #5d5d4a;
                    font-weight: 800;
                    font-size: 12px;
                    border-radius: 8px;
                    border: 2px solid {self.accent_color};
                }}
                QPushButton:hover {{ background: {self.header_bg}; }}
            """)
            self.test_db_button.clicked.connect(self._show_db_viewer)
            self.left_layout.addWidget(self.test_db_button, 0, Qt.AlignLeft)

        # Side Card
        self.side_card = SidePatientCard()
        self.side_card.setFixedHeight(695) # 80 (header) + 15 (spacing) + 600 (3 beds * 190 + 2 * 15 spacing)
        self.side_card.open_card_clicked.connect(self._open_patient_card_by_number)
        self.content_layout.addWidget(self.side_card, 0, Qt.AlignTop)
        if not self.embedded:
            self.content_layout.addStretch()

        self.bed_widgets = []
        self._init_bed_widgets()
        self.refresh_bed_statuses()
        
        if self.bed_widgets:
            self._on_bed_clicked(1, self.bed_widgets[0].current_admission_id)

    def _create_window_btn(self, text, slot, is_close=False):
        btn = QPushButton(text)
        btn.setFixedSize(35, 35)
        btn.setCursor(Qt.PointingHandCursor)
        if is_close:
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #7a7a6a; font-size: 20px; border: none; }
                QPushButton:hover { background: #ef4444; color: white; border-radius: 5px; }
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: #7a7a6a; font-size: 18px; border: none; }}
                QPushButton:hover {{ background: {self.bg_color}; color: #1e293b; border-radius: 5px; }}
            """)
        btn.clicked.connect(slot)
        return btn

    def _toggle_maximized(self):
        if self.embedded:
            return
        if self._is_maximized:
            self.showNormal()
            self.root_layout.setContentsMargins(10, 10, 10, 10)
            self.root_container.setStyleSheet(self.root_container.styleSheet().replace("border-radius: 0px", "border-radius: 15px"))
            self.title_bar.setStyleSheet(self.title_bar.styleSheet().replace("border-top-left-radius: 0px", "border-top-left-radius: 13px"))
            self.btn_max.setText("□")
        else:
            self.showMaximized()
            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.root_container.setStyleSheet(self.root_container.styleSheet().replace("border-radius: 15px", "border-radius: 0px"))
            self.title_bar.setStyleSheet(self.title_bar.styleSheet().replace("border-top-left-radius: 13px", "border-top-left-radius: 0px"))
            self.btn_max.setText("❐")
        self._is_maximized = not self._is_maximized

    def _get_resize_edges(self, pos):
        if self.embedded:
            return Qt.Edge(0)
        edges = Qt.Edge(0)
        if pos.x() < self._margin: edges |= Qt.LeftEdge
        if pos.x() > self.width() - self._margin: edges |= Qt.RightEdge
        if pos.y() < self._margin: edges |= Qt.TopEdge
        if pos.y() > self.height() - self._margin: edges |= Qt.BottomEdge
        return edges

    def mousePressEvent(self, event: QMouseEvent):
        if self.embedded:
            return super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            edges = self._get_resize_edges(event.pos())
            if edges:
                self._resizing = True
                self.windowHandle().startSystemResize(edges)
            elif self.title_bar.underMouse():
                self._drag_pos = event.globalPosition().toPoint() - self.pos()
                self._dragging = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.embedded:
            return super().mouseReleaseEvent(event)
        self._resizing = False
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.embedded:
            return super().mouseMoveEvent(event)
        if not self._is_maximized:
            edges = self._get_resize_edges(event.pos())
            if edges == (Qt.LeftEdge | Qt.TopEdge) or edges == (Qt.RightEdge | Qt.BottomEdge): self.setCursor(Qt.SizeFDiagCursor)
            elif edges == (Qt.RightEdge | Qt.TopEdge) or edges == (Qt.LeftEdge | Qt.BottomEdge): self.setCursor(Qt.SizeBDiagCursor)
            elif edges & (Qt.LeftEdge | Qt.RightEdge): self.setCursor(Qt.SizeHorCursor)
            elif edges & (Qt.TopEdge | Qt.BottomEdge): self.setCursor(Qt.SizeVerCursor)
            else: self.setCursor(Qt.ArrowCursor)

            if event.buttons() & Qt.LeftButton and getattr(self, '_dragging', False) and not self._resizing:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def _load_settings(self):
        if self.embedded:
            return
        settings = QSettings("RAO3", "MainWindow")
        geo = settings.value("geometry")
        if geo: self.restoreGeometry(geo)
        pos = settings.value("pos")
        if pos: self.move(pos)
        is_max = settings.value("maximized", "false") == "true"
        if is_max: self._toggle_maximized()

    def _save_settings(self):
        if self.embedded:
            return
        settings = QSettings("RAO3", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("pos", self.pos())
        settings.setValue("maximized", "true" if self._is_maximized else "false")

    def _safe_close(self):
        self._save_settings()
        self.close()

    def _init_bed_widgets(self):
        beds = self.db_manager.get_all_beds()
        for i in range(9):
            self._create_bed_widget(beds[i])

    def _create_bed_widget(self, bed_data):
        admission_id = bed_data["current_admission_id"] if bed_data["current_admission_id"] is not None else 0
        bed_widget = BedWidget(bed_data["bed_number"], bed_data["status"], admission_id, self)
        bed_widget.clicked.connect(self._on_bed_clicked)
        index = len(self.bed_widgets)
        row = index // 3
        col = index % 3
        self.grid_layout.addWidget(bed_widget, row, col)
        self.bed_widgets.append(bed_widget)

    def _on_bed_clicked(self, bed_number: int, current_admission_id: int):
        patient, admission = None, None
        if current_admission_id:
            patient, admission = self.patient_service.get_patient_with_current_admission(bed_number)
        self.side_card.update_info(bed_number, patient, admission)

    def _open_patient_card_by_number(self, bed_number):
        patient, admission = self.patient_service.get_patient_with_current_admission(bed_number)
        self._open_patient_form(bed_number, patient, admission)

    def _open_patient_form(self, bed_number: int, patient=None, admission=None):
        from rem_card.Rao_jornal.ui.patient_form import PatientForm

        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.root_container.setGraphicsEffect(blur)
        patient_form = PatientForm(self.db_manager, self.patient_service, bed_number, patient, admission, self)
        if patient_form.exec() == QDialog.Accepted:
            self.refresh_bed_statuses()
            new_p, new_a = self.patient_service.get_patient_with_current_admission(bed_number)
            self.side_card.update_info(bed_number, new_p, new_a)
        self.root_container.setGraphicsEffect(None)

    def _show_db_viewer(self):
        from rem_card.Rao_jornal.ui.db_viewer import DatabaseViewerDialog

        viewer = DatabaseViewerDialog(self.db_manager, self)
        viewer.exec()
        self.refresh_bed_statuses()

    def move_patient(self, source_bed: int, target_bed: int):
        from rem_card.Rao_jornal.ui.custom_dialogs import CustomMessageBox

        source_bed_data = self.db_manager.get_bed_by_number(source_bed)
        target_bed_data = self.db_manager.get_bed_by_number(target_bed)
        if not source_bed_data or source_bed_data["status"] == "FREE": return
        source_adm_id = source_bed_data["current_admission_id"]
        
        msg = f"Переместить пациента с койки {source_bed} на койку {target_bed}?"
        if target_bed_data and target_bed_data["status"] != "FREE":
            msg = f"Койка {target_bed} занята. Поменять пациентов местами?"
            
        if not CustomMessageBox.show_question(self, "Перенос пациента", msg): return
        
        try:
            with self.db_manager.write_transaction(source="journal_move_patient") as cursor:
                if target_bed_data and target_bed_data["status"] != "FREE":
                    target_adm_id = target_bed_data["current_admission_id"]
                    cursor.execute("UPDATE beds SET current_admission_id = NULL, status = 'FREE' WHERE bed_number IN (?, ?)", (source_bed, target_bed))
                    cursor.execute("UPDATE admissions SET bed_number = ? WHERE id = ?", (target_bed, source_adm_id))
                    cursor.execute("UPDATE admissions SET bed_number = ? WHERE id = ?", (source_bed, target_adm_id))
                    cursor.execute("UPDATE beds SET current_admission_id = ?, status = 'OCCUPIED' WHERE bed_number = ?", (source_adm_id, target_bed))
                    cursor.execute("UPDATE beds SET current_admission_id = ?, status = 'OCCUPIED' WHERE bed_number = ?", (target_adm_id, source_bed))
                else:
                    cursor.execute("UPDATE beds SET current_admission_id = NULL, status = 'FREE' WHERE bed_number = ?", (source_bed,))
                    cursor.execute("UPDATE admissions SET bed_number = ? WHERE id = ?", (target_bed, source_adm_id))
                    cursor.execute("UPDATE beds SET current_admission_id = ?, status = 'OCCUPIED' WHERE bed_number = ?", (source_adm_id, target_bed))
            
            self.refresh_bed_statuses()
            new_p, new_a = self.patient_service.get_patient_with_current_admission(target_bed)
            self.side_card.update_info(target_bed, new_p, new_a)
        except Exception as e:
            CustomMessageBox.show_info(self, "Ошибка", str(e))

    def refresh_bed_statuses(self):
        rows = self.db_manager.get_beds_snapshot()
        by_bed = {int(row["bed_number"]): row for row in rows}

        for bed_widget in self.bed_widgets:
            bed_data = by_bed.get(int(bed_widget.bed_number))
            if not bed_data:
                continue

            admission_id = bed_data["current_admission_id"] if bed_data["current_admission_id"] is not None else 0
            bed_widget.set_status(bed_data["status"], admission_id)
            if bed_data["current_admission_id"]:
                bed_widget.set_patient_info(
                    str(bed_data["full_name"] or ""),
                    str(bed_data["history_number"] or ""),
                    str(bed_data["diagnosis_text"] or ""),
                )
            else:
                bed_widget.set_patient_info("")
