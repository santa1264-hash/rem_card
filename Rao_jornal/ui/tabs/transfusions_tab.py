from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox, QLabel, QHBoxLayout, QDialog, QFormLayout, QComboBox, QSpinBox, QDateTimeEdit, QGraphicsDropShadowEffect, QScrollArea, QStyledItemDelegate
from rem_card.Rao_jornal.ui.custom_dialogs import CustomMessageBox
from PySide6.QtCore import Qt, QDateTime, QPoint
from PySide6.QtGui import QColor, QCursor
from rem_card.Rao_jornal.domain.transfusion import Transfusion
from rem_card.Rao_jornal.services.patient_service import PatientService
from rem_card.Rao_jornal.domain.admission import Admission

class TransfusionDialog(QDialog):
    def __init__(self, admission_id, parent=None):
        super().__init__(parent)
        self.admission_id = admission_id
        
        self._drag_pos = QPoint()
        
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.bg_color = "#f5f2e9"
        self.border_color = "#d1d1bc"
        
        self._init_ui()

    def _init_ui(self):
        # Основной контейнер
        self.bg_container = QWidget(self)
        self.bg_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.bg_color};
                border: 2px solid {self.border_color};
                border-radius: 20px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.bg_container.setGraphicsEffect(shadow)

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(10, 10, 10, 10)
        window_layout.addWidget(self.bg_container)

        self.main_layout = QVBoxLayout(self.bg_container)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        self.main_layout.setSpacing(15)

        self.header_panel = QWidget()
        self.header_panel.setFixedHeight(40)
        self.header_panel.setStyleSheet("background: transparent; border: none;")
        header_panel_layout = QHBoxLayout(self.header_panel)
        header_panel_layout.setContentsMargins(10, 0, 0, 0)
        
        self.title_label = QLabel("НОВАЯ ТРАНСФУЗИЯ")
        self.title_label.setStyleSheet("color: #4a4a3a; font-size: 14px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
        header_panel_layout.addWidget(self.title_label)
        header_panel_layout.addStretch()
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton { background: transparent; color: #7a7a6a; font-size: 26px; border: none; padding: 0px; margin: 0px; font-weight: bold; }
            QPushButton:hover { background: #ef4444; color: white; border-radius: 5px; }
        """)
        self.close_button.clicked.connect(self.reject)
        header_panel_layout.addWidget(self.close_button, 0, Qt.AlignRight | Qt.AlignTop)
        self.main_layout.addWidget(self.header_panel)

        self.content_group = QGroupBox("Данные переливания")
        self.content_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self.border_color};
                background-color: {self.bg_color};
                border-radius: 6px;
                margin-top: 18px; 
                padding-top: 25px;
                font-weight: 800;
                color: #4a4a3a;
                border-top-left-radius: 0px; 
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 8px 20px;
                background: {self.bg_color};
                border: 1px solid {self.border_color};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                left: 0px;
                top: 0px;
                font-size: 14px;
                color: #2d2d24;
                font-weight: 600;
            }}
        """)
        
        group_layout = QVBoxLayout(self.content_group)
        group_layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 1. Поле КОМПОНЕНТА - СТАНДАРТНОЕ (без QHBoxLayout и Stretch)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Кровь", "Плазма", "Тромбоциты"])
        # Принудительная стилизация как у "Пол" (копируем tab_styling из patient_form)
        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #c9c9b4;
                border-radius: 4px;
                background: #fdfdfa;
                color: #2d2d24;
            }
            QComboBox:focus {
                border: 1px solid #8a8a68;
                background: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #c9c9b4;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #2d2d24;
                selection-background-color: #8a8a68;
                selection-color: white;
                border: 1px solid #c9c9b4;
                outline: 0px;
            }
        """)
        
        # 2. Поле ОБЪЕМА - ВОЗВРАЩАЕМ КАК БЫЛО (с кнопками)
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(10, 5000)
        self.volume_spin.setSingleStep(10)
        self.volume_spin.setValue(250)
        self.volume_spin.setSuffix(" мл")
        self.volume_spin.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.volume_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #c9c9b4;
                border-radius: 4px;
                background: #fdfdfa;
                color: #2d2d24;
            }
            QSpinBox:focus {
                border: 1px solid #8a8a68;
                background: white;
            }
            QSpinBox::up-button { width: 20px; }
            QSpinBox::down-button { width: 20px; }
        """)
        
        # 3. Поле ДАТЫ - как было
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setFixedWidth(250)
        self.datetime_edit.setStyleSheet("""
            QDateTimeEdit { background-color: #fdfdfa; color: #2d2d24; border: 1px solid #c9c9b4; padding: 8px; border-radius: 4px; }
            QDateTimeEdit:focus { border: 1px solid #8a8a68; background: white; }
            QDateTimeEdit::up-button, QDateTimeEdit::down-button { width: 0px; border: none; }
            QDateTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #c9c9b4;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QDateTimeEdit::down-arrow { image: none; }
            QCalendarWidget QWidget { background-color: white; color: #2d2d24; border-radius: 0px; }
            QCalendarWidget QAbstractItemView:enabled { background-color: white; color: #2d2d24; selection-background-color: #8a8a68; selection-color: white; border-radius: 0px; }
            QCalendarWidget QToolButton { color: #2d2d24; background-color: transparent; border: none; border-radius: 0px; }
            QCalendarWidget QToolButton:hover { color: #000000; }
            QCalendarWidget QToolButton#qt_calendar_monthbutton { margin-left: -6px; }
            QCalendarWidget QWidget#qt_calendar_navigationbar { background-color: #f0ede4; border-bottom: 1px solid #c9c9b4; border-radius: 0px; }
        """)

        lbl_style = "background: transparent; border: none; color: #4a4a3f; font-weight: 600; margin-top: 1px;"
        comp_lbl = QLabel("Компонент:")
        comp_lbl.setStyleSheet(lbl_style)
        vol_lbl = QLabel("Объем:")
        vol_lbl.setStyleSheet(lbl_style)
        date_lbl = QLabel("Дата/Время:")
        date_lbl.setStyleSheet(lbl_style)

        form_layout.addRow(comp_lbl, self.type_combo) # Стандартное размещение
        form_layout.addRow(vol_lbl, self.volume_spin)
        form_layout.addRow(date_lbl, self.datetime_edit)
        
        group_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.content_group)
        self.main_layout.addStretch()

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        self.cancel_btn = QPushButton("ОТМЕНИТЬ")
        self.save_btn = QPushButton("ДОБАВИТЬ")
        for b in [self.cancel_btn, self.save_btn]:
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(45)
            b.setMinimumWidth(160)

        self.cancel_btn.setStyleSheet("""
            QPushButton { background: #f5f3e9; border: 1px solid #dcdcc6; border-radius: 6px; color: #7e7e6d; font-weight: 700; font-size: 11px; }
            QPushButton:hover { background: #ebe8d5; color: #2d2d24; }
        """)
        self.save_btn.setStyleSheet("""
            QPushButton { background: #6b6b47; border: none; border-radius: 6px; color: white; font-weight: 800; font-size: 11px; }
            QPushButton:hover { background: #5d5d3d; }
            QPushButton:pressed { background: #4a4a31; }
        """)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        btns_layout.addStretch()
        btns_layout.addWidget(self.cancel_btn)
        btns_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(btns_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPosition().toPoint()

    def get_data(self):
        type_map = {"Кровь": "blood", "Плазма": "plasma", "Тромбоциты": "platelets"}
        return {
            "type": type_map[self.type_combo.currentText()],
            "volume": self.volume_spin.value(),
            "datetime": self.datetime_edit.dateTime().toPython()
        }

class TransfusionsTabWidget(QWidget):
    def __init__(self, patient_service: PatientService, parent=None):
        super().__init__(parent)
        self.patient_service = patient_service
        self.admission = None
        self.pending_transfusions = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        self.add_transfusion_button = QPushButton("Добавить трансфузию")
        self.add_transfusion_button.setCursor(Qt.PointingHandCursor)
        self.add_transfusion_button.setStyleSheet("""
            QPushButton {
                background-color: #7a7a5a;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #6a6a4a;
            }
        """)

        self.add_transfusion_button.clicked.connect(self._add_transfusion)
        layout.addWidget(self.add_transfusion_button)
        
        self.transfusion_list_layout = QVBoxLayout()
        self.transfusion_list_layout.setSpacing(25)
        self.transfusion_list_layout.setContentsMargins(0, 10, 0, 10)
        layout.addLayout(self.transfusion_list_layout)
        
        layout.addStretch(1)

        self.totals_group = QGroupBox("Итоговые объемы")
        self.totals_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #c9c9b4;
                border-radius: 6px;
                margin-top: 18px; 
                padding-top: 20px;
                font-weight: 800;
                color: #4a4a3a;
                background-color: #f0ede4;
                border-top-left-radius: 0px; 
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 8px 20px;
                background: #f0ede4;
                border: 1px solid #c9c9b4;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                left: 0px;
                top: 0px;
                font-size: 12px;
                color: #2d2d24;
            }
        """)
        totals_layout = QVBoxLayout(self.totals_group)
        totals_layout.setContentsMargins(20, 20, 20, 20)
        totals_layout.setSpacing(8)
        self.total_blood_label = QLabel("Общий объем крови: 0 мл")
        self.total_plasma_label = QLabel("Общий объем плазмы: 0 мл")
        self.total_platelets_label = QLabel("Общий объем тромбоцитов: 0 мл")
        
        for lbl in [self.total_blood_label, self.total_plasma_label, self.total_platelets_label]:
            lbl.setStyleSheet("font-weight: bold; color: #2c3e50; background: transparent;")
            
        totals_layout.addWidget(self.total_blood_label)
        totals_layout.addWidget(self.total_plasma_label)
        totals_layout.addWidget(self.total_platelets_label)
        layout.addWidget(self.totals_group)

    def set_admission(self, admission: Admission):
        self.admission = admission
        self.refresh()

    def refresh(self):
        while self.transfusion_list_layout.count():
            item = self.transfusion_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()

        transfusions = []
        if self.admission:
            transfusions.extend(self.patient_service.get_transfusions_by_admission(self.admission.id))
        transfusions.extend(self.pending_transfusions)

        groups = {"blood": [], "plasma": [], "platelets": []}
        type_names = {"blood": "Кровь", "plasma": "Плазма", "platelets": "Тромбоциты"}
        totals = {"blood": 0, "plasma": 0, "platelets": 0}
        
        for t in transfusions:
            groups[t.type].append(t)
            totals[t.type] += t.volume_ml
            
        for t_type in ["blood", "plasma", "platelets"]:
            if groups[t_type]:
                group_box = QGroupBox(type_names[t_type])
                group_box.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid #c9c9b4;
                        border-radius: 6px;
                        margin-top: 18px; 
                        padding-top: 20px; 
                        font-weight: 800;
                        color: #5d5d4a;
                        background-color: #f0ede4;
                        border-top-left-radius: 0px; 
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        padding: 8px 20px;
                        background: #f0ede4;
                        border: 1px solid #c9c9b4;
                        border-bottom: none;
                        border-top-left-radius: 8px;
                        border-top-right-radius: 8px;
                        left: 0px;
                        top: 0px; 
                        font-size: 12px;
                        color: #2d2d24;
                    }
                """)
                group_layout = QVBoxLayout(group_box)
                group_layout.setSpacing(5)
                group_layout.setContentsMargins(15, 20, 15, 15) 
                for t in groups[t_type]:
                    row = QHBoxLayout()
                    row.setContentsMargins(0, 0, 0, 0)
                    lbl = QLabel(f"{t.datetime.strftime('%d.%m.%Y %H:%M')} - {t.volume_ml} мл")
                    lbl.setStyleSheet("background: transparent; font-weight: 500; color: #2d2d24;")
                    row.addWidget(lbl)
                    row.addStretch(1)
                    del_btn = QPushButton("Удалить")
                    del_btn.setFixedWidth(80)
                    del_btn.setStyleSheet("""
                        QPushButton { background: #e8e4d5; border: 1px solid #c9c9b4; border-radius: 4px; padding: 4px; font-size: 11px; }
                        QPushButton:hover { background: #dad6c2; }
                    """)
                    if getattr(t, 'id', None) is not None and t.id != 0:
                        del_btn.clicked.connect(lambda checked=False, tid=t.id: self._delete_transfusion(tid))
                    else:
                        del_btn.clicked.connect(lambda checked=False, tr=t: self._delete_pending_transfusion(tr))
                    row.addWidget(del_btn)
                    group_layout.addLayout(row)
                self.transfusion_list_layout.addWidget(group_box)

        self.total_blood_label.setText(f"Общий объем крови: {totals['blood']} мл")
        self.total_plasma_label.setText(f"Общий объем плазмы: {totals['plasma']} мл")
        self.total_platelets_label.setText(f"Общий объем тромбоцитов: {totals['platelets']} мл")

    def _add_transfusion(self):
        dialog = TransfusionDialog(self.admission.id if self.admission else 0, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_transfusion = Transfusion(
                admission_id=self.admission.id if self.admission else 0,
                type=data["type"],
                volume_ml=data["volume"],
                datetime=data["datetime"]
            )
            self.pending_transfusions.append(new_transfusion)
            self.refresh()

    def _delete_transfusion(self, transfusion_id):
        if CustomMessageBox.show_question(self, "Удаление", "Удалить запись о трансфузии?"):
            self.patient_service.delete_transfusion(transfusion_id)
            self.refresh()

    def _delete_pending_transfusion(self, transfusion):
        if CustomMessageBox.show_question(self, "Удаление", "Удалить запись о трансфузии?"):
            if transfusion in self.pending_transfusions:
                self.pending_transfusions.remove(transfusion)
                self.refresh()
                
    def get_pending_transfusions(self):
        return self.pending_transfusions
        
    def clear_pending(self):
        self.pending_transfusions.clear()
