from PySide6.QtWidgets import QWidget, QFormLayout, QHBoxLayout, QCheckBox, QDateTimeEdit, QComboBox, QLineEdit, QLabel, QVBoxLayout, QFrame
from rem_card.Rao_jornal.ui.custom_dialogs import CustomMessageBox
from PySide6.QtCore import QDateTime, Qt

class TransferTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.get_admission_dt_func = None
        self.get_main_profile_func = None
        self.on_death_checked_callback = None
        self.on_duration_changed_callback = None
        self.is_ivl_active_func = None 
        self.get_last_extubation_dt_func = None
        
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("QWidget { background-color: #f2f3ee; }")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)

        # Карточка исхода
        self.outcome_frame = QFrame()
        self.outcome_frame.setStyleSheet("""
            QFrame { background-color: #fdfdfa; border: 1px solid #c9c9b4; border-radius: 8px; }
            QLabel { border: none; font-weight: bold; font-size: 15px; color: #4a4a3f; background: transparent; }
        """)
        outcome_layout = QHBoxLayout(self.outcome_frame)
        outcome_layout.setContentsMargins(25, 20, 25, 20)
        
        outcome_label = QLabel("Укажите исход госпитализации:")
        self.outcome_combo = QComboBox()
        self.outcome_combo.addItems(["В отделении", "Переведен", "Умер"])
        self.outcome_combo.setFixedWidth(200)
        self.outcome_combo.currentTextChanged.connect(self._on_outcome_changed)
        
        self.outcome_combo.setStyleSheet("""
            QComboBox { 
                background-color: #fdfdfa; 
                border: 1px solid #c9c9b4; 
                border-radius: 5px; 
                padding: 5px 10px; 
                color: #2d2d24;
            }
            QComboBox:focus { border: 2px solid #8a8a68; }
        """)
        
        outcome_layout.addWidget(outcome_label)
        outcome_layout.addWidget(self.outcome_combo)
        outcome_layout.addStretch()
        self.main_layout.addWidget(self.outcome_frame)

        # Контейнер для деталей
        self.details_frame = QFrame()
        self.details_frame.setStyleSheet("""
            QFrame { background-color: #fdfdfa; border: 2px solid #8a8a68; border-radius: 8px; }
            QLabel { border: none; font-weight: normal; color: #4a4a3f; background: transparent; }
        """)
        self.details_layout = QFormLayout(self.details_frame)
        self.details_layout.setContentsMargins(30, 25, 30, 25)
        self.details_layout.setSpacing(15)
        self.main_layout.addWidget(self.details_frame)

        # Создаем все возможные виджеты заранее
        self.transfer_dt_lbl = QLabel("Дата и время перевода:")
        self.transfer_datetime_input = self._create_dt_edit()
        self.transfer_datetime_input.dateTimeChanged.connect(self._validate_datetimes)
        
        self.transfer_dept_lbl = QLabel("Куда переведен:")
        self.transfer_department_input = QComboBox()
        self.transfer_department_input.addItems([
            "Терапия", "Хирургия", "Травматология", "Гинекология", "Неврология", "Кардиология", "Инфекционно-педиатрическое", "Другое ЛПУ"
        ])
        self.transfer_department_input.currentTextChanged.connect(self._on_department_changed)
        self.transfer_department_input.setFixedWidth(380)

        self.transfer_lpu_lbl = QLabel("Название ЛПУ:")
        self.transfer_lpu_input = QComboBox()
        self.transfer_lpu_input.addItems(["ГКБ №2 г. Комсомольск-на-Амуре", "ГКБ №7 г. Комсомольск-на-Амуре", "Другое ЛПУ"])
        self.transfer_lpu_input.currentTextChanged.connect(self._update_visibility)
        self.transfer_lpu_input.setFixedWidth(380)

        self.transfer_lpu_other_lbl = QLabel("Уточнение ЛПУ:")
        self.transfer_lpu_other_input = QLineEdit()
        self.transfer_lpu_other_input.setPlaceholderText("Введите название другого ЛПУ")
        self.transfer_lpu_other_input.setFixedWidth(380)

        self.death_dt_lbl = QLabel("Дата и время смерти:")
        self.death_datetime_input = self._create_dt_edit()
        self.death_datetime_input.dateTimeChanged.connect(self._validate_datetimes)
        
        self.final_profile_lbl = QLabel("Окончательный профиль:")
        self.final_profile_input = QComboBox()
        self.final_profile_input.addItems([
            "Терапия", "Хирургия", "Травматология", "Гинекология", "Неврология", "Кардиология", "Инфекционно-педиатрическое"
        ])
        self.final_profile_input.setFixedWidth(380)

        # Добавляем ВСЕ в лейаут один раз
        self.details_layout.addRow(self.transfer_dt_lbl, self.transfer_datetime_input)
        self.details_layout.addRow(self.transfer_dept_lbl, self.transfer_department_input)
        self.details_layout.addRow(self.transfer_lpu_lbl, self.transfer_lpu_input)
        self.details_layout.addRow(self.transfer_lpu_other_lbl, self.transfer_lpu_other_input)
        self.details_layout.addRow(self.death_dt_lbl, self.death_datetime_input)
        self.details_layout.addRow(self.final_profile_lbl, self.final_profile_input)

        self.main_layout.addStretch()

        # Сводка по времени
        self.duration_frame = QFrame()
        self.duration_frame.setStyleSheet("""
            QFrame { background-color: #e6e8de; border: 2px solid #8a8a68; border-radius: 12px; }
            QLabel { border: none; background: transparent; }
        """)
        duration_layout = QHBoxLayout(self.duration_frame)
        duration_layout.setContentsMargins(20, 15, 20, 15)
        self.duration_label = QLabel("Время пребывания: 0 дн. 0 час.")
        self.duration_label.setStyleSheet("font-weight: bold; font-size: 17px; color: #4a4a3f;")
        duration_layout.addStretch()
        duration_layout.addWidget(self.duration_label)
        duration_layout.addStretch()
        self.main_layout.addWidget(self.duration_frame)

        self._update_visibility()

    def _create_dt_edit(self):
        dt = QDateTimeEdit()
        dt.setDisplayFormat("dd.MM.yyyy  HH:mm")
        dt.setCalendarPopup(True)
        dt.setDateTime(QDateTime.currentDateTime())
        dt.setFixedWidth(200)
        dt.setStyleSheet("""
            QDateTimeEdit { background-color: #fdfdfa; color: #2d2d24; border: 1px solid #c9c9b4; border-radius: 5px; padding: 5px; }
            QDateTimeEdit:focus { border: 1px solid #8a8a68; background-color: white; }
            QDateTimeEdit::up-button, QDateTimeEdit::down-button { width: 0px; }
            QDateTimeEdit::drop-down { width: 0px; }
        """)
        return dt

    def set_callbacks(self, get_adm, get_main_prof, on_death_cb, on_dur_cb, is_ivl_active=None, get_last_extubation=None):
        self.get_admission_dt_func = get_adm
        self.get_main_profile_func = get_main_prof
        self.on_death_checked_callback = on_death_cb
        self.on_duration_changed_callback = on_dur_cb
        self.is_ivl_active_func = is_ivl_active
        self.get_last_extubation_dt_func = get_last_extubation

    def _check_ivl_block(self, silent=False):
        """Проверяет, заблокирован ли исход из-за активной ИВЛ."""
        outcome = self.outcome_combo.currentText()
        if outcome != "Переведен": return False
        
        is_ivl = self.is_ivl_active_func and self.is_ivl_active_func()
        if not is_ivl: return False
        
        # Перевод невозможен ВООБЩЕ если ИВЛ активна
        if not silent:
            CustomMessageBox.show_info(self, "Внимание", "Нельзя перевести пациента (даже в другое ЛПУ),\nпока есть незавершенные эпизоды ИВЛ.\n\nСначала отметьте экстубацию.")
        return True

    def _on_department_changed(self, text: str):
        if self._check_ivl_block():
            self.outcome_combo.blockSignals(True)
            self.outcome_combo.setCurrentText("В отделении")
            self.outcome_combo.blockSignals(False)
        self._update_visibility()

    def _on_outcome_changed(self, text: str):
        if text == "Переведен" and self._check_ivl_block():
            self.outcome_combo.blockSignals(True)
            self.outcome_combo.setCurrentText("В отделении")
            self.outcome_combo.blockSignals(False)
            self._update_visibility()
            return
            
        if text == "Переведен":
            if self.get_main_profile_func:
                main_profile = self.get_main_profile_func()
                idx = self.transfer_department_input.findText(main_profile)
                if idx >= 0: self.transfer_department_input.setCurrentIndex(idx)
        elif text == "Умер":
            if self.get_main_profile_func:
                main_profile = self.get_main_profile_func()
                idx = self.final_profile_input.findText(main_profile)
                if idx >= 0: self.final_profile_input.setCurrentIndex(idx)
            current_time = QDateTime.currentDateTime()
            self.death_datetime_input.setDateTime(current_time)
            
            # Автоматически закрываем ИВЛ временем смерти при выборе исхода "Умер"
            if self.on_death_checked_callback:
                self.on_death_checked_callback(current_time)
        
        self._update_visibility()

    def _update_visibility(self, *args):
        outcome = self.outcome_combo.currentText()
        is_transfer = (outcome == "Переведен")
        is_death = (outcome == "Умер")
        is_in_dept = (outcome == "В отделении")
        
        self.details_frame.setVisible(not is_in_dept)
        self.duration_frame.setVisible(not is_in_dept)
        
        if not is_in_dept:
            self.transfer_dt_lbl.setVisible(is_transfer)
            self.transfer_datetime_input.setVisible(is_transfer)
            self.transfer_dept_lbl.setVisible(is_transfer)
            self.transfer_department_input.setVisible(is_transfer)
            
            show_lpu = is_transfer and (self.transfer_department_input.currentText() == "Другое ЛПУ")
            self.transfer_lpu_lbl.setVisible(show_lpu)
            self.transfer_lpu_input.setVisible(show_lpu)
            
            show_other_lpu = show_lpu and (self.transfer_lpu_input.currentText() == "Другое ЛПУ")
            self.transfer_lpu_other_lbl.setVisible(show_other_lpu)
            self.transfer_lpu_other_input.setVisible(show_other_lpu)
            
            self.death_dt_lbl.setVisible(is_death)
            self.death_datetime_input.setVisible(is_death)
            self.final_profile_lbl.setVisible(is_death)
            self.final_profile_input.setVisible(is_death)
            
            self._validate_datetimes()

    def _validate_datetimes(self, *args):
        if not self.get_admission_dt_func: return
        adm_dt = self.get_admission_dt_func()
        
        outcome = self.outcome_combo.currentText()
        
        if outcome == "Переведен":
            min_dt = adm_dt
            if self.get_last_extubation_dt_func:
                ext_dt = self.get_last_extubation_dt_func()
                if ext_dt and ext_dt > min_dt: min_dt = ext_dt
                
            if self.transfer_datetime_input.dateTime() < min_dt:
                self.transfer_datetime_input.blockSignals(True)
                self.transfer_datetime_input.setDateTime(min_dt)
                self.transfer_datetime_input.blockSignals(False)
                
        elif outcome == "Умер":
            # Для "Умер" мы позволяем времени смерти быть любым после поступления, 
            # но вызываем коллбэк закрытия ИВЛ, который сам подкорректирует экстубацию под смерть.
            if self.death_datetime_input.dateTime() < adm_dt:
                self.death_datetime_input.blockSignals(True)
                self.death_datetime_input.setDateTime(adm_dt)
                self.death_datetime_input.blockSignals(False)
            
            # Синхронизируем закрытие ИВЛ
            if self.on_death_checked_callback:
                self.on_death_checked_callback(self.death_datetime_input.dateTime())
        
        self.update_duration_label()

    def update_duration_label(self):
        if not self.get_admission_dt_func: return
        outcome = self.outcome_combo.currentText()
        if outcome == "В отделении": return

        start = self.get_admission_dt_func().toPython()
        end = None
        if outcome == "Переведен":
            end = self.transfer_datetime_input.dateTime().toPython()
        elif outcome == "Умер":
            end = self.death_datetime_input.dateTime().toPython()

        if end:
            diff = end - start
            if diff.total_seconds() >= 0:
                days = diff.days
                hours = diff.seconds // 3600
                self.duration_label.setText(f"Общее время пребывания: {days} дн. {hours} час.")
            else:
                self.duration_label.setText("Ошибка: дата убытия раньше поступления!")
            if self.on_duration_changed_callback: self.on_duration_changed_callback()

    def get_data(self):
        outcome_text = self.outcome_combo.currentText()
        if outcome_text == "В отделении":
            return {
                "transfer_datetime": None,
                "transfer_department": None,
                "transfer_lpu": None,
                "transfer_lpu_other": None,
                "death_datetime": None,
                "outcome": None
            }
        
        return {
            "transfer_datetime": self.transfer_datetime_input.dateTime().toPython() if outcome_text == "Переведен" else None,
            "transfer_department": self.transfer_department_input.currentText() if outcome_text == "Переведен" else self.final_profile_input.currentText(),
            "transfer_lpu": self.transfer_lpu_input.currentText() if (outcome_text == "Переведен" and self.transfer_department_input.currentText() == "Другое ЛПУ") else None,
            "transfer_lpu_other": self.transfer_lpu_other_input.text().strip() if (outcome_text == "Переведен" and self.transfer_department_input.currentText() == "Другое ЛПУ" and self.transfer_lpu_input.currentText() == "Другое ЛПУ") else None,
            "death_datetime": self.death_datetime_input.dateTime().toPython() if outcome_text == "Умер" else None,
            "outcome": "переведен" if outcome_text == "Переведен" else "умер"
        }
        
    def set_data(self, admission):
        if not admission or (not admission.transfer_datetime and not admission.death_datetime):
            self.outcome_combo.setCurrentText("В отделении")
            self._update_visibility()
            return
        if admission.outcome == "умер" or admission.death_datetime:
            self.outcome_combo.setCurrentText("Умер")
            if admission.death_datetime:
                self.death_datetime_input.setDateTime(admission.death_datetime)
            elif admission.transfer_datetime:
                self.death_datetime_input.setDateTime(admission.transfer_datetime)
            if admission.transfer_department: self.final_profile_input.setCurrentText(admission.transfer_department)
        else:
            self.outcome_combo.setCurrentText("Переведен")
            if admission.transfer_datetime:
                self.transfer_datetime_input.setDateTime(admission.transfer_datetime)
            if admission.transfer_department: self.transfer_department_input.setCurrentText(admission.transfer_department)
            if admission.transfer_department == "Другое ЛПУ" and admission.transfer_lpu:
                self.transfer_lpu_input.setCurrentText(admission.transfer_lpu)
                if admission.transfer_lpu == "Другое ЛПУ" and admission.transfer_lpu_other:
                    self.transfer_lpu_other_input.setText(admission.transfer_lpu_other)
        self._update_visibility()
