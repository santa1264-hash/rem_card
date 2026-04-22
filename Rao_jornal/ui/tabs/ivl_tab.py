from PySide6.QtWidgets import QWidget, QFormLayout, QCheckBox, QDateTimeEdit, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QMessageBox
from PySide6.QtCore import QDateTime, Qt
from datetime import datetime

class IVLTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ivl_episodes_widgets = []
        self.get_admission_dt_func = None
        self.get_transfer_dt_func = None
        self.get_death_dt_func = None
        
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("QWidget { background-color: #f2f3ee; }")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(15)

        self.episodes_layout = QVBoxLayout()
        self.episodes_layout.setSpacing(12)
        self.main_layout.addLayout(self.episodes_layout)

        self._add_ivl_episode("Доставлен на ИВЛ", "delivery")
        self._add_ivl_episode("Переведен на ИВЛ", "transfer")
        for i in range(2, 5):
            self._add_ivl_episode(f"Повторная ИВЛ {i}", f"repeat_{i}")

        self.main_layout.addStretch()

        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame { background-color: #e6e8de; border: 2px solid #8a8a68; border-radius: 12px; }
            QLabel { border: none; background: transparent; }
        """)
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        self.ivl_duration_label = QLabel("Общее время ИВЛ: 0 часов")
        self.ivl_duration_label.setStyleSheet("font-weight: bold; font-size: 17px; color: #4a4a3f;")
        summary_layout.addStretch()
        summary_layout.addWidget(self.ivl_duration_label)
        summary_layout.addStretch()
        self.main_layout.addWidget(self.summary_frame)
        self.summary_frame.hide()

        self._update_ivl_visibility()

    def _add_ivl_episode(self, label_text, ep_type):
        frame = QFrame()
        frame.setObjectName(f"frame_{ep_type}")
        frame.setStyleSheet("""
            QFrame { background-color: #fdfdfa; border: 1px solid #c9c9b4; border-radius: 8px; }
            QLabel { border: none; color: #4a4a3f; font-size: 13px; background: transparent; }
            QCheckBox { border: none; font-weight: bold; font-size: 14px; color: #2d2d24; background: transparent; }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        start_cb = QCheckBox(label_text)
        start_cb.setCursor(Qt.PointingHandCursor)
        start_cb.clicked.connect(self._update_ivl_visibility)
        header_layout.addWidget(start_cb)
        
        end_cb = QCheckBox("Завершено (экстубация)")
        end_cb.setCursor(Qt.PointingHandCursor)
        end_cb.setStyleSheet("margin-left: 20px; font-weight: normal; color: #707054;")
        end_cb.clicked.connect(self._update_ivl_visibility)
        header_layout.addStretch()
        header_layout.addWidget(end_cb)
        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #c9c9b4; height: 1px; border: none;")
        layout.addWidget(line)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(15)
        
        start_dt = self._create_dt_edit()
        start_dt.dateTimeChanged.connect(self._validate_datetimes)
        start_lbl = QLabel("Дата начала:")
        
        end_dt = self._create_dt_edit()
        end_dt.dateTimeChanged.connect(self._validate_datetimes)
        end_lbl = QLabel("Дата окончания:")
        
        inputs_layout.addWidget(start_lbl)
        inputs_layout.addWidget(start_dt)
        inputs_layout.addSpacing(30)
        inputs_layout.addWidget(end_lbl)
        inputs_layout.addWidget(end_dt)
        inputs_layout.addStretch()
        layout.addLayout(inputs_layout)
        
        self.episodes_layout.addWidget(frame)
        
        self.ivl_episodes_widgets.append({
            "type": ep_type,
            "frame": frame,
            "line": line,
            "start_cb": start_cb,
            "start_lbl": start_lbl,
            "start_dt": start_dt,
            "end_cb": end_cb,
            "end_lbl": end_lbl,
            "end_dt": end_dt
        })

    def _create_dt_edit(self):
        dt = QDateTimeEdit()
        dt.setDisplayFormat("dd.MM.yyyy  HH:mm")
        dt.setCalendarPopup(True)
        dt.setDateTime(QDateTime.currentDateTime())
        dt.setFixedWidth(190)
        dt.setStyleSheet("""
            QDateTimeEdit { background-color: #fdfdfa; color: #2d2d24; border: 1px solid #c9c9b4; border-radius: 5px; padding: 5px; }
            QDateTimeEdit:focus { border: 1px solid #8a8a68; background-color: white; }
            QDateTimeEdit::up-button, QDateTimeEdit::down-button { width: 0px; }
            QDateTimeEdit::drop-down { width: 0px; }
        """)
        return dt

    def set_datetime_getters(self, get_adm, get_transfer, get_death):
        self.get_admission_dt_func = get_adm
        self.get_transfer_dt_func = get_transfer
        self.get_death_dt_func = get_death

    def sync_admission_datetime(self):
        if self.get_admission_dt_func and self.ivl_episodes_widgets:
            delivery_ep = self.ivl_episodes_widgets[0]
            if delivery_ep["start_cb"].isChecked():
                delivery_ep["start_dt"].setDateTime(self.get_admission_dt_func())
                self._validate_datetimes()

    def _update_ivl_visibility(self):
        adm_dt = self.get_admission_dt_func() if self.get_admission_dt_func else QDateTime.currentDateTime()
        delivery_ep = self.ivl_episodes_widgets[0]
        
        if delivery_ep["start_cb"].isChecked():
            delivery_ep["start_dt"].setDateTime(adm_dt)
            delivery_ep["start_dt"].setEnabled(False)
        
        for i, ep in enumerate(self.ivl_episodes_widgets):
            is_start = ep["start_cb"].isChecked()
            is_end = ep["end_cb"].isChecked()
            
            ep["line"].setVisible(is_start)
            ep["start_lbl"].setVisible(is_start)
            ep["start_dt"].setVisible(is_start)
            ep["end_cb"].setVisible(is_start)
            ep["end_lbl"].setVisible(is_start and is_end)
            ep["end_dt"].setVisible(is_start and is_end)
            
            if is_start:
                ep["frame"].setStyleSheet("QFrame { background-color: #fdfdfa; border: 2px solid #8a8a68; border-radius: 8px; } QLabel { border: none; } QCheckBox { border: none; font-weight: bold; }")
            else:
                ep["frame"].setStyleSheet("QFrame { background-color: #f6f7f2; border: 1px solid #dcdccb; border-radius: 8px; } QLabel { border: none; } QCheckBox { border: none; font-weight: normal; color: #b0b0a0; }")
                ep["end_cb"].setChecked(False)

            if i > 0:
                prev_ep = self.ivl_episodes_widgets[i-1]
                if ep["type"] == "transfer":
                    del_active = delivery_ep["start_cb"].isChecked()
                    del_ended = delivery_ep["end_cb"].isChecked()
                    show_it = not del_active or (del_active and del_ended)
                    ep["frame"].setVisible(show_it)
                else:
                    show_it = prev_ep["start_cb"].isChecked() and prev_ep["end_cb"].isChecked()
                    ep["frame"].setVisible(show_it)
            else:
                ep["frame"].setVisible(True)

        self._validate_datetimes()

    def _validate_datetimes(self, *args):
        adm_dt = self.get_admission_dt_func() if self.get_admission_dt_func else None
        if not adm_dt: return

        last_end_dt = adm_dt
        
        for i, ep in enumerate(self.ivl_episodes_widgets):
            if not ep["start_cb"].isChecked(): continue
            
            if ep["start_dt"].dateTime() < last_end_dt:
                ep["start_dt"].blockSignals(True)
                ep["start_dt"].setDateTime(last_end_dt)
                ep["start_dt"].blockSignals(False)
            
            if ep["end_cb"].isChecked():
                if ep["end_dt"].dateTime() < ep["start_dt"].dateTime():
                    ep["end_dt"].blockSignals(True)
                    ep["end_dt"].setDateTime(ep["start_dt"].dateTime())
                    ep["end_dt"].blockSignals(False)
                last_end_dt = ep["end_dt"].dateTime()
            else:
                last_end_dt = ep["start_dt"].dateTime()

        self.update_ivl_duration()

    def update_ivl_duration(self):
        total_seconds = 0
        has_ivl = False
        for ep in self.ivl_episodes_widgets:
            if ep["start_cb"].isChecked():
                has_ivl = True
                start_time = ep["start_dt"].dateTime().toPython()
                if ep["end_cb"].isChecked():
                    end_time = ep["end_dt"].dateTime().toPython()
                else:
                    transfer_dt = self.get_transfer_dt_func() if self.get_transfer_dt_func else None
                    death_dt = self.get_death_dt_func() if self.get_death_dt_func else None
                    if transfer_dt: end_time = transfer_dt.toPython()
                    elif death_dt: end_time = death_dt.toPython()
                    else: end_time = datetime.now()
                if end_time > start_time:
                    total_seconds += (end_time - start_time).total_seconds()
        if has_ivl:
            hours = int(total_seconds / 3600)
            self.ivl_duration_label.setText(f"Общее время ИВЛ: {hours} часов")
            self.summary_frame.show()
        else:
            self.summary_frame.hide()
            
    def get_data(self):
        ivl_episodes = []
        for i, ep in enumerate(self.ivl_episodes_widgets):
            if ep["start_cb"].isChecked():
                ivl_episodes.append({
                    "episode_number": i + 1,
                    "type": ep["type"],
                    "start_time": ep["start_dt"].dateTime().toPython(),
                    "end_time": ep["end_dt"].dateTime().toPython() if ep["end_cb"].isChecked() else None
                })
        return ivl_episodes
        
    def set_data(self, episodes):
        for widget in self.ivl_episodes_widgets:
            widget["start_cb"].setChecked(False)
            widget["end_cb"].setChecked(False)
        for ep in episodes:
            for widget in self.ivl_episodes_widgets:
                if widget["type"] == ep.type:
                    widget["start_cb"].setChecked(True)
                    widget["start_dt"].setDateTime(ep.start_time)
                    if ep.end_time:
                        widget["end_cb"].setChecked(True)
                        widget["end_dt"].setDateTime(ep.end_time)
                    break
        self._update_ivl_visibility()
        
    def close_active_ivl_if_dead(self, death_datetime):
        """Закрывает активные эпизоды ИВЛ. Если экстубация уже стоит ПОЗЖЕ смерти, корректирует на время смерти."""
        for ep in self.ivl_episodes_widgets:
            if ep["start_cb"].isChecked():
                if not ep["end_cb"].isChecked():
                    ep["end_cb"].setChecked(True)
                    ep["end_dt"].setDateTime(death_datetime)
                else:
                    if ep["end_dt"].dateTime() > death_datetime:
                        ep["end_dt"].setDateTime(death_datetime)
        self._update_ivl_visibility()

    def is_currently_on_ivl(self):
        for ep in self.ivl_episodes_widgets:
            if ep["start_cb"].isChecked() and not ep["end_cb"].isChecked():
                return True
        return False

    def get_last_extubation_dt(self):
        """Возвращает время самой поздней экстубации среди всех активных/завершенных блоков."""
        last_dt = None
        for ep in self.ivl_episodes_widgets:
            if ep["start_cb"].isChecked():
                dt = ep["end_dt"].dateTime() if ep["end_cb"].isChecked() else ep["start_dt"].dateTime()
                if last_dt is None or dt > last_dt:
                    last_dt = dt
        return last_dt
