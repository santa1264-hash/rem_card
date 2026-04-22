import os
from rem_card.ui.shared.custom_message_box import CustomMessageBox
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox, QDateTimeEdit, QApplication, QDialog)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QColor, QIcon
from rem_card.ui.shared.base_sector import BaseSectorWidget
from rem_card.data.dto.remcard_dto import PatientStatus
from rem_card.ui.rem_card_sectors.outcome_dialogs import DeathOutcomeDialog, TransferOutcomeDialog

class SectorEvents(BaseSectorWidget):
    status_changed = Signal()

    def __init__(self, parent=None):
        super().__init__("События", parent)
        self.status_service = None
        self.admission_id = None
        self.shift_date = None
        self.shift_start = None
        self.shift_end = None
        self.user_id = "USER" 
        self.role = "Врач" # По умолчанию
        self._is_editing_time = False # Флаг для блокировки автообновления при редактировании

        self.label.hide()
        self.setFrameStyle(BaseSectorWidget.NoFrame)
        self.setStyleSheet("background: transparent;")

        self.init_ui()

    def init_ui(self):
        # Общий контейнер
        self.main_container = QWidget()
        self.main_container.setObjectName("sector_events_main_container")
        self.main_layout_v = QVBoxLayout(self.main_container)
        # Отступ 3px сверху и снизу для унификации с другими секторами
        self.main_layout_v.setContentsMargins(0, 3, 0, 3)
        self.main_layout_v.setSpacing(0)
        
        # 1. Шапка
        self.header_lbl = QLabel("События / Перемещения пациента")
        self.header_lbl.setObjectName("sector_header")
        self.header_lbl.setAlignment(Qt.AlignCenter)
        self.header_lbl.setFixedHeight(30)
        self.main_layout_v.addWidget(self.header_lbl)

        # 2. Область контента
        self.content_area = QWidget()
        self.content_area.setObjectName("sector_content_area")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(15)
        
        # --- Верхняя панель: Кнопки выбора статуса ---
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        self.btn_active = self._create_status_btn("В отделении", "#2ecc71", PatientStatus.ACTIVE)
        self.btn_out = self._create_status_btn("Вне отд.", "#f1c40f", PatientStatus.OUT)
        self.btn_or = self._create_status_btn("Операционная", "#e74c3c", PatientStatus.OR)
        self.btn_trans = self._create_status_btn("Переведен", "#34495e", PatientStatus.TRANSFERRED)
        self.btn_dead = self._create_status_btn("Умер", "#2c3e50", PatientStatus.DEAD)
        
        buttons_layout.addWidget(self.btn_active)
        buttons_layout.addWidget(self.btn_out)
        buttons_layout.addWidget(self.btn_or)
        buttons_layout.addWidget(self.btn_trans)
        buttons_layout.addWidget(self.btn_dead)
        
        self.content_layout.addWidget(buttons_widget)
        
        # --- Панель ввода комментария и ОТМЕНА ---
        reason_widget = QWidget()
        reason_layout = QHBoxLayout(reason_widget)
        reason_layout.setContentsMargins(0, 0, 0, 0)
        reason_layout.setSpacing(10)
        
        self.edit_reason_text = QLineEdit()
        self.edit_reason_text.setPlaceholderText("Комментарий к перемещению...")
        self.edit_reason_text.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 13px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border: 1.5px solid #3498db;
            }
        """)
        reason_layout.addWidget(self.edit_reason_text)

        # Кнопка ОТМЕНЫ последнего действия
        self.btn_rollback = QPushButton(" Отменить последнее")
        self.btn_rollback.setFixedHeight(30)
        self.btn_rollback.setStyleSheet("""
            QPushButton {
                font-weight: bold; font-size: 12px; color: #e74c3c;
                background-color: #fdfdfd; border-radius: 4px; border: 1.5px solid #e74c3c;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #fff5f5; }
            QPushButton:pressed { background-color: #fceaea; }
            QPushButton:disabled { color: #bdc3c7; border-color: #dcdde1; }
        """)
        self.btn_rollback.clicked.connect(self.on_rollback_clicked)
        reason_layout.addWidget(self.btn_rollback)
        
        self.content_layout.addWidget(reason_widget)
        
        # --- Список истории событий ---
        self.history_area = QScrollArea()
        self.history_area.setWidgetResizable(True)
        self.history_area.setFrameShape(QFrame.NoFrame)
        self.history_area.setStyleSheet("background-color: #fdfdfd; border: 1px solid #dcdde1; border-radius: 4px;")
        
        self.history_list_container = QWidget()
        self.history_list_layout = QVBoxLayout(self.history_list_container)
        self.history_list_layout.setContentsMargins(5, 5, 5, 5)
        self.history_list_layout.setSpacing(5)
        self.history_list_layout.addStretch()
        
        self.history_area.setWidget(self.history_list_container)
        self.content_layout.addWidget(self.history_area, 1) 
        
        self.main_layout_v.addWidget(self.content_area)

        # 3. Футер
        self.bottom_footer = QWidget()
        self.bottom_footer.setObjectName("sector_footer")
        self.bottom_footer.setFixedHeight(15)
        self.main_layout_v.addWidget(self.bottom_footer)

        # Стили
        self.main_container.setStyleSheet("""
            QWidget#sector_events_main_container { background-color: transparent !important; }
            QWidget#sector_header {
                font-weight: bold; font-size: 14px; color: #2c3e50 !important; 
                background-color: #e9ecef !important;
                border-top: 1.5px solid #bdc3c7 !important;
                border-left: 1.5px solid #bdc3c7 !important;
                border-right: 1.5px solid #bdc3c7 !important;
                border-bottom: 0.5px solid #bdc3c7 !important;
                border-top-left-radius: 5px !important; border-top-right-radius: 5px !important;
            }
            QWidget#sector_content_area {
                background-color: white !important;
                border-left: 1.5px solid #bdc3c7 !important;
                border-right: 1.5px solid #bdc3c7 !important;
                border-top: none !important; border-bottom: none !important;
            }
            QWidget#sector_footer {
                background-color: white !important;
                border-left: 1.5px solid #bdc3c7 !important;
                border-right: 1.5px solid #bdc3c7 !important;
                border-bottom: 1.5px solid #bdc3c7 !important;
                border-bottom-left-radius: 5px !important; border-bottom-right-radius: 5px !important;
                border-top: none !important;
            }
        """)

        self.set_content(self.main_container)

    def _create_status_btn(self, text, color, status):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setFixedHeight(36)
        btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold; font-size: 13px; color: white;
                background-color: {color}; border-radius: 5px; border: 1px solid #bdc3c7;
                padding: 0 10px;
            }}
            QPushButton:hover {{ border: 2px solid #2c3e50; }}
            QPushButton:checked {{ background-color: {color}; border: 3px solid #2c3e50; }}
            QPushButton:disabled {{ background-color: #bdc3c7; color: #7f8c8d; }}
        """)
        btn.clicked.connect(lambda: self.on_status_btn_clicked(status))
        return btn

    def set_patient(self, admission_id, status_service):
        self.admission_id = admission_id
        self.status_service = status_service
        self.refresh()

    def set_shift_context(self, shift_date, shift_start, shift_end):
        """Устанавливает временные границы для фильтрации событий."""
        self.shift_date = shift_date
        self.shift_start = shift_start
        self.shift_end = shift_end
        self.refresh()

    def refresh(self, force=False):
        if not self.admission_id or not self.status_service:
            from rem_card.app.logger import logger
            logger.debug(f"[SectorEvents] Refresh skipped: id={self.admission_id}, service={bool(self.status_service)}")
            return
            
        # 1. Если мы сейчас редактируем время или комментарий (флаг взведен)
        if self._is_editing_time and not force:
            return
            
        # 2. ЖЕСТКАЯ ПРОВЕРКА ФОКУСА: если курсор в любом поле ввода этой вкладки - не обновляем!
        focused_widget = QApplication.focusWidget()
        if focused_widget and not force:
            # Проверяем, принадлежит ли виджет с фокусом нашему контейнеру списка
            if self.history_list_container.isAncestorOf(focused_widget):
                return
            # И также для верхнего поля комментария
            if focused_widget == self.edit_reason_text:
                return

        # Если границы смены установлены - фильтруем, иначе берем всё
        is_archive = False
        if self.shift_start and self.shift_end:
            events = self.status_service.get_events_in_range(self.admission_id, self.shift_start, self.shift_end)
            is_archive = self.shift_end < datetime.now()
            from rem_card.app.logger import logger
            logger.debug(f"[SectorEvents] Refreshing for {self.shift_start.strftime('%d.%m %H:%M')}. Found {len(events)} events. Archive: {is_archive}")
        else:
            events = self.status_service.get_events(self.admission_id)
        
        if not events and self.shift_start:
            # Если событий нет совсем (даже начального), это странно.
            # Но мы должны очистить список, чтобы не показывать старые данные другого пациента.
            pass

        while self.history_list_layout.count() > 1:
            item = self.history_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        current_ev = None
        for ev in reversed(events):
            if ev.end_time is None: current_ev = ev
            
            row = QFrame()
            row.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dcdde1; border-radius: 3px; margin: 2px;")
            l = QHBoxLayout(row)
            l.setContentsMargins(10, 5, 10, 5)
            
            # Поле комментария и флаг редактирования (общие для всех типов строк)
            reason_edit = QLineEdit(ev.reason_text or "")
            reason_edit.setPlaceholderText("Комментарий...")
            reason_edit.setStyleSheet("border: 1px solid #dcdde1; border-radius: 2px; padding: 1px 5px;")
            
            def create_change_handler(btn, style):
                def handler():
                    self._is_editing_time = True
                    btn.setStyleSheet(style)
                    btn.setToolTip("Нажмите, чтобы сохранить изменения")
                return handler

            # ТАБЛИЧНОЕ ВЫРАВНИВАНИЕ (Фиксированные колонки)
            # 1. Время начала (Увеличили логику отображения ...)
            is_start_outside = self.shift_start and ev.start_time < self.shift_start
            
            if is_start_outside:
                dt_start_view = QLabel("...")
                dt_start_view.setFixedWidth(60)
                dt_start_view.setAlignment(Qt.AlignCenter)
                dt_start_view.setStyleSheet("font-weight: bold; color: #7f8c8d;")
                dt_start_view.setToolTip(ev.start_time.strftime("%d.%m.%y %H:%M"))
                l.addWidget(dt_start_view)
                
                # Скрытый виджет для сохранения структуры данных, если нужно
                dt_start = QDateTimeEdit(ev.start_time)
                dt_start.hide()
            else:
                dt_start = QDateTimeEdit(ev.start_time)
                dt_start.setDisplayFormat("HH:mm")
                dt_start.setButtonSymbols(QDateTimeEdit.NoButtons)
                dt_start.setFixedWidth(60)
                dt_start.setStyleSheet("border: none; background: transparent; font-weight: bold;")
                l.addWidget(dt_start)
            
            sep = QLabel("-")
            sep.setFixedWidth(12)
            sep.setAlignment(Qt.AlignCenter)
            sep.setStyleSheet("border: none; background: transparent;")
            l.addWidget(sep)
            
            # 2. Время конца
            is_end_outside = False
            if ev.end_time:
                if self.shift_end and ev.end_time > self.shift_end:
                    is_end_outside = True
            else:
                # Если события еще нет, но смена УЖЕ ЗАКОНЧИЛАСЬ в прошлом
                if self.shift_end and self.shift_end < datetime.now():
                    is_end_outside = True

            if is_end_outside:
                dt_end_view = QLabel("...")
                dt_end_view.setFixedWidth(60)
                dt_end_view.setAlignment(Qt.AlignCenter)
                dt_end_view.setStyleSheet("font-weight: bold; color: #7f8c8d;")
                l.addWidget(dt_end_view)
                
                # Технические объекты для обработчиков
                dt_end = QDateTimeEdit(ev.end_time or self.shift_end)
                dt_end.hide()
            elif ev.end_time:
                dt_end = QDateTimeEdit(ev.end_time)
                dt_end.setDisplayFormat("HH:mm")
                dt_end.setButtonSymbols(QDateTimeEdit.NoButtons)
                dt_end.setFixedWidth(60)
                dt_end.setStyleSheet("border: none; background: transparent; font-weight: bold;")
                l.addWidget(dt_end)
                
                # Блокируем автообновление при начале взаимодействия с полем
                dt_start.dateTimeChanged.connect(lambda: setattr(self, '_is_editing_time', True))
                dt_end.dateTimeChanged.connect(lambda: setattr(self, '_is_editing_time', True))

                # 3. Кнопка сохранения (Колонка фикс. ширины)
                btn_container = QWidget()
                btn_container.setFixedWidth(30)
                btn_lay = QHBoxLayout(btn_container)
                btn_lay.setContentsMargins(0, 0, 0, 0)
                
                # Привязываем изменение комментария к флагу редактирования
                reason_edit.textChanged.connect(lambda: setattr(self, '_is_editing_time', True))

                btn_save_time = QPushButton("✓")
                btn_save_time.setFixedSize(20, 20)
                btn_save_time.setToolTip("Данные сохранены")
                
                style_saved = "QPushButton { border-radius: 10px; background-color: #2ecc71; color: white; font-weight: bold; border: 1px solid #2ecc71; }"
                style_changed = "QPushButton { border-radius: 10px; background-color: #f1f2f6; color: #7f8c8d; font-weight: bold; border: 1px solid #bdc3c7; } QPushButton:hover { background-color: #2ecc71; color: white; }"
                
                btn_save_time.setStyleSheet(style_saved)
                
                change_handler = create_change_handler(btn_save_time, style_changed)
                dt_start.dateTimeChanged.connect(change_handler)
                dt_end.dateTimeChanged.connect(change_handler)
                reason_edit.textChanged.connect(change_handler)

                # Управление доступностью полей ввода времени
                if is_start_outside or is_archive:
                    dt_start.setEnabled(False)
                
                if is_end_outside:
                    dt_end.setEnabled(False)
                
                # Логика блокировки кнопки сохранения (одна на всю строку)
                should_block_save = False
                
                # 1. Если и старт, и конец вне границ смены (строка выглядит как ... - ...)
                if is_start_outside and is_end_outside:
                    should_block_save = True
                
                # 2. Если мы в архиве, и время окончания тоже вне этой смены
                if is_archive and is_end_outside:
                    should_block_save = True
                
                if should_block_save:
                    btn_save_time.setEnabled(False)
                    btn_save_time.setStyleSheet("QPushButton { border-radius: 10px; background-color: #bdc3c7; color: white; border: 1px solid #bdc3c7; }")
                    btn_save_time.setToolTip("Редактирование этого события запрещено")
                
                btn_save_time.clicked.connect(lambda checked=False, e=ev, s=dt_start, ed=dt_end, r=reason_edit: self.on_save_time_clicked(e, s, ed, r))
                btn_lay.addWidget(btn_save_time)
                l.addWidget(btn_container)
            elif not is_end_outside:
                l_end = QLabel("...")
                l_end.setFixedWidth(60)
                l_end.setStyleSheet("border: none; background: transparent; font-weight: bold;")
                l.addWidget(l_end)
                
                # Заполнитель для кнопки
                btn_container = QWidget()
                btn_container.setFixedWidth(30)
                btn_lay = QHBoxLayout(btn_container)
                btn_lay.setContentsMargins(0, 0, 0, 0)
                
                btn_save_comm = QPushButton("✓")
                btn_save_comm.setFixedSize(20, 20)
                
                style_saved_comm = "QPushButton { border-radius: 10px; background-color: #3498db; color: white; font-weight: bold; border: 1px solid #3498db; }"
                style_changed_comm = "QPushButton { border-radius: 10px; background-color: #f1f2f6; color: #7f8c8d; font-weight: bold; border: 1px solid #bdc3c7; } QPushButton:hover { background-color: #3498db; color: white; }"
                
                btn_save_comm.setStyleSheet(style_saved_comm)
                btn_save_comm.setToolTip("Данные сохранены")

                change_handler_comm = create_change_handler(btn_save_comm, style_changed_comm)
                reason_edit.textChanged.connect(change_handler_comm)

                if is_archive:
                    btn_save_comm.setEnabled(False)
                    btn_save_comm.setStyleSheet("QPushButton { border-radius: 10px; background-color: #bdc3c7; color: white; border: 1px solid #bdc3c7; }")
                    btn_save_comm.setToolTip("Редактирование архива запрещено")

                btn_save_comm.clicked.connect(lambda checked=False, e=ev, s=dt_start, r=reason_edit: self.on_save_time_clicked(e, s, None, r))
                btn_lay.addWidget(btn_save_comm)
                l.addWidget(btn_container)
            else:
                # Если событие выходит за правую границу, добавляем пустой заполнитель для выравнивания
                btn_spacer = QWidget()
                btn_spacer.setFixedWidth(30)
                l.addWidget(btn_spacer)
            
            # 4. Статус (Колонка фикс. ширины)
            status_map = {
                PatientStatus.ACTIVE: ("В отделении", "#2ecc71"),
                PatientStatus.OUT: ("Вне отд.", "#f39c12"),
                PatientStatus.OR: ("Операционная", "#e74c3c"),
                PatientStatus.TRANSFERRED: ("Переведен", "#968c8c"),
                PatientStatus.DEAD: ("Умер", "#968c8c")
            }
            s_name, s_color = status_map.get(ev.status, (ev.status.value, "grey"))
            
            s_lbl = QLabel(s_name)
            s_lbl.setFixedWidth(155) # Увеличено на 40% (110 -> 155)
            s_lbl.setAlignment(Qt.AlignCenter)
            # Бейдж статуса с цветной рамкой и легким фоном
            s_lbl.setStyleSheet(f"""
                QLabel {{
                    color: {s_color}; 
                    font-weight: bold; 
                    border: 1.5px solid {s_color}; 
                    border-radius: 4px; 
                    background-color: rgba({QColor(s_color).red()}, {QColor(s_color).green()}, {QColor(s_color).blue()}, 25);
                    padding: 2px;
                }}
            """)
            l.addWidget(s_lbl)
            
            # 5. Комментарий (Тянется)
            if is_archive:
                reason_edit.setReadOnly(True)
                reason_edit.setStyleSheet("border: none; background: transparent; color: #444;")
            l.addWidget(reason_edit, 1)
            
            # 6. Автор (Колонка фикс. ширины)
            creator_raw = str(ev.created_by or "SYSTEM").upper()
            creator_map = {
                "SYSTEM": "Система",
                "USER": self.role,
                "ADMIN": "Админ"
            }
            creator_display = creator_map.get(creator_raw, creator_raw)
            
            creator = QLabel(f"[{creator_display}]")
            creator.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            l.addWidget(creator)
            
            self.history_list_layout.insertWidget(0, row)

        if current_ev:
            self._update_buttons_state(current_ev.status, is_archive)
            self.btn_rollback.setEnabled(len(events) > 1 and not is_archive)
        else:
            self._update_buttons_state(None, is_archive)
            self.btn_rollback.setEnabled(False)

    def _update_buttons_state(self, current_status, is_archive=False):
        self.btn_active.setChecked(current_status == PatientStatus.ACTIVE)
        self.btn_out.setChecked(current_status == PatientStatus.OUT)
        self.btn_or.setChecked(current_status == PatientStatus.OR)
        self.btn_trans.setChecked(current_status == PatientStatus.TRANSFERRED)
        self.btn_dead.setChecked(current_status == PatientStatus.DEAD)
        
        is_final = current_status in (PatientStatus.TRANSFERRED, PatientStatus.DEAD)
        can_edit = not is_final and not is_archive
        
        for btn in [self.btn_active, self.btn_out, self.btn_or, self.btn_trans, self.btn_dead]:
            btn.setEnabled(can_edit)

    def on_status_btn_clicked(self, status):
        if not self.admission_id or not self.status_service: return
        
        r_text = self.edit_reason_text.text()

        if status in (PatientStatus.TRANSFERRED, PatientStatus.DEAD):
            self._handle_structured_outcome(status, r_text)
            return

        if hasattr(self.status_service, "enqueue_change_status"):
            self.content_area.setEnabled(False)

            def on_success(result):
                self.content_area.setEnabled(True)
                if result:
                    self.edit_reason_text.clear()
                    self.refresh(force=True)
                    self.status_changed.emit()
                else:
                    CustomMessageBox.warning(self, "Ошибка", "Не удалось изменить статус пациента.")

            def on_error(exc):
                self.content_area.setEnabled(True)
                CustomMessageBox.warning(self, "Ошибка", f"Ошибка смены статуса: {exc}")

            self.status_service.enqueue_change_status(
                self.admission_id,
                status,
                reason_type=None,
                reason_text=r_text,
                user_id=self.user_id,
                on_success=on_success,
                on_error=on_error,
            )
            return

        if self.status_service.change_status(self.admission_id, status, None, r_text, self.user_id):
            self.edit_reason_text.clear()
            self.refresh()
            self.status_changed.emit()

    def _handle_structured_outcome(self, status, base_comment: str):
        context = {}
        if hasattr(self.status_service, "get_admission_outcome_context"):
            try:
                context = self.status_service.get_admission_outcome_context(self.admission_id)
            except Exception as exc:
                CustomMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные госпитализации: {exc}")
                self.refresh(force=True)
                return

        dialog_parent = self.window() if self.window() else self
        if status == PatientStatus.TRANSFERRED:
            dialog = TransferOutcomeDialog(context, self.shift_date or datetime.now(), base_comment, dialog_parent)
        else:
            dialog = DeathOutcomeDialog(context, self.shift_date or datetime.now(), base_comment, dialog_parent)

        if dialog.exec() != QDialog.Accepted:
            self.refresh(force=True)
            return

        payload = dict(dialog.result_data or {})
        event_time = payload.get("event_time")
        reason_text = payload.get("reason_text") or base_comment
        admission_details = payload.get("admission_details") or {}

        def on_success(result):
            self.content_area.setEnabled(True)
            if result:
                self.edit_reason_text.clear()
                self.refresh(force=True)
                self.status_changed.emit()
            else:
                self.refresh(force=True)
                CustomMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось зафиксировать исход. Проверьте время: оно не должно быть раньше начала текущего статуса.",
                )

        def on_error(exc):
            self.content_area.setEnabled(True)
            self.refresh(force=True)
            CustomMessageBox.warning(self, "Ошибка", f"Ошибка фиксации исхода: {exc}")

        self.content_area.setEnabled(False)
        if hasattr(self.status_service, "enqueue_change_status_with_outcome_details"):
            self.status_service.enqueue_change_status_with_outcome_details(
                self.admission_id,
                status,
                event_time,
                reason_type=None,
                reason_text=reason_text,
                user_id=self.user_id,
                admission_details=admission_details,
                on_success=on_success,
                on_error=on_error,
            )
            return

        try:
            if hasattr(self.status_service, "change_status_with_outcome_details"):
                result = self.status_service.change_status_with_outcome_details(
                    self.admission_id,
                    status,
                    event_time,
                    None,
                    reason_text,
                    self.user_id,
                    admission_details,
                )
            else:
                result = self.status_service.change_status(self.admission_id, status, None, reason_text, self.user_id)
            on_success(result)
        except Exception as exc:
            on_error(exc)

    def on_save_time_clicked(self, event_dto, start_edit, end_edit, reason_edit):
        """Обработка сохранения измененного времени и комментария."""
        from datetime import timedelta
        
        new_start = start_edit.dateTime().toPython()
        new_end = end_edit.dateTime().toPython() if end_edit else None
        new_reason = reason_edit.text()

        # Исправление перехода через полночь:
        # Если время конца "меньше" времени начала, значит наступили следующие сутки
        if new_end and new_end < new_start:
            # Проверяем, не является ли разница слишком большой (например, более 12 часов)
            # чтобы отличить реальный переход через 00:00 от случайной ошибки ввода
            if (new_start - new_end).total_seconds() > 0:
                new_end += timedelta(days=1)
        
        # Минимальная валидация (только если есть время конца)
        if new_end and (new_end - new_start).total_seconds() < 60:
            CustomMessageBox.warning(self, "Внимание", "Длительность события должна быть не менее 60 секунд. Проверьте время начала и окончания.")
            return

        if hasattr(self.status_service, "enqueue_update_event_bounds"):
            self.content_area.setEnabled(False)

            def on_success(result):
                self.content_area.setEnabled(True)
                self._is_editing_time = False
                self.refresh(force=True)
                if result:
                    self.status_changed.emit()
                else:
                    CustomMessageBox.warning(self, "Ошибка линейности времени", "Невозможно изменить время: это приведет к наложению событий.\n\nВремя начала события не может быть раньше начала предыдущего.\nСначала сдвиньте соседние события.")

            def on_error(exc):
                self.content_area.setEnabled(True)
                self._is_editing_time = False
                self.refresh(force=True)
                CustomMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения события: {exc}")

            self.status_service.enqueue_update_event_bounds(
                event_dto.id,
                new_start,
                new_end,
                new_reason,
                on_success=on_success,
                on_error=on_error,
            )
            return

        if self.status_service.update_event_bounds(event_dto.id, new_start, new_end, new_reason):
            self._is_editing_time = False # Снимаем блокировку
            self.refresh(force=True)
            self.status_changed.emit()
        else:
            # Снимаем блокировку, чтобы UI не завис, и обновляем данные обратно из БД
            self._is_editing_time = False 
            self.refresh(force=True)
            
            CustomMessageBox.warning(self, "Ошибка линейности времени", "Невозможно изменить время: это приведет к наложению событий.\n\nВремя начала события не может быть раньше начала предыдущего.\nСначала сдвиньте соседние события.")

    def on_rollback_clicked(self):
        if not self.admission_id or not self.status_service: return
        
        reply = self._show_question(
            "Вы уверены, что хотите отменить последнее изменение статуса и вернуться к предыдущему?"
        )
        
        if reply == CustomMessageBox.Yes:
            if hasattr(self.status_service, "enqueue_rollback_last_status"):
                self.content_area.setEnabled(False)

                def on_success(result):
                    self.content_area.setEnabled(True)
                    if result:
                        self.refresh(force=True)
                        self.status_changed.emit()
                    else:
                        CustomMessageBox.warning(self, "Ошибка", "Не удалось отменить перемещение (возможно, это начальный статус).")

                def on_error(exc):
                    self.content_area.setEnabled(True)
                    CustomMessageBox.warning(self, "Ошибка", f"Ошибка отката статуса: {exc}")

                self.status_service.enqueue_rollback_last_status(
                    self.admission_id,
                    on_success=on_success,
                    on_error=on_error,
                )
                return

            if self.status_service.rollback_last_status(self.admission_id):
                self.refresh()
                self.status_changed.emit()
            else:
                CustomMessageBox.warning(self, "Ошибка", "Не удалось отменить перемещение (возможно, это начальный статус).")

    def _show_question(self, text):
        return CustomMessageBox.question(self, "Подтверждение", text)

    def set_content(self, widget):
        """Установка виджета в BaseSectorWidget"""
        super().set_content(widget)
