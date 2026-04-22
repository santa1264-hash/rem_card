from rem_card.ui.shared.custom_message_box import CustomMessageBox
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox
from ....app.logger import logger

class BalanceController(QObject):
    """Контроллер для связи UI баланса выведения с бизнес-логикой и БД."""
    data_updated = Signal()

    def __init__(self, fluid_service, admission_id: int, shift_date: datetime):
        super().__init__()
        self.service = fluid_service
        self.admission_id = admission_id
        self.shift_date = shift_date
        
        self.grid = None
        self.panel_2d = None
        self.quick_input = None # Теперь это Sector2b_v
        
        # Стек для Undo (храним ID последних созданных/измененных записей)
        self._undo_stack = [] 
        
        # Кэш данных: hour (0-23) -> накопленные значения по показателям выведения.
        self.hourly_cache = self._build_empty_hourly_cache()
        self._effective_bounds_cache = None

    @staticmethod
    def _build_empty_hourly_cache():
        return {
            h: {
                "urine": 0,
                "drain_output": 0,
                "ng_output": 0,
                "stool": 0,
                "other_output": 0,
            }
            for h in range(24)
        }

    def set_widgets(self, grid, panel_2d, quick_inputs: list):
        self.grid = grid
        self.panel_2d = panel_2d
        
        # Подключаем сигналы сетки и панели управления
        self.grid.cell_selected.connect(self._on_cell_selected)
        self.panel_2d.save_requested.connect(self._on_panel_save)
        self.panel_2d.delete_requested.connect(self._on_panel_delete)
        self.panel_2d.undo_requested.connect(self.undo)
        
        # Находим сектор 2b_v среди быстрых вводов (он обычно в списке)
        from rem_card.ui.rem_card_sectors.balance.sector_2b_v import Sector2b_v
        from rem_card.ui.rem_card_sectors.sector_3b import Sector3b
        for qi in quick_inputs:
            if isinstance(qi, Sector2b_v):
                self.quick_input = qi
                # Подключаем сигналы только если это поле ввода (QLineEdit)
                # В Sector2b_v они остались полями ввода
                qi.diurez_val.returnPressed.connect(lambda f=qi.diurez_val: self.add_value("urine", f))
                qi.drenazh_val.returnPressed.connect(lambda f=qi.drenazh_val: self.add_value("drain_output", f))
                qi.zond_val.returnPressed.connect(lambda f=qi.zond_val: self.add_value("ng_output", f))
                qi.rvota_val.returnPressed.connect(lambda f=qi.rvota_val: self.add_value("stool", f))
                if hasattr(qi, 'other_val'):
                    qi.other_val.returnPressed.connect(lambda f=qi.other_val: self.add_value("other_output", f))
            
            # В Sector3b поля стали QLabel, сигналы returnPressed не нужны
            if isinstance(qi, Sector3b):
                continue

    def refresh(self):
        """Загрузка данных из БД и обновление сетки."""
        try:
            effective_bounds = self.service.vital_service.get_effective_bounds(self.admission_id, self.shift_date)
            fluids = self.service.get_fluids(self.admission_id, self.shift_date)
            self.apply_loaded_data(fluids, effective_bounds)
        except Exception as e:
            logger.error(f"[BalanceCtrl] Error refreshing data: {e}", exc_info=True)

    def apply_loaded_data(self, fluids, effective_bounds):
        # СБРАСЫВАЕМ КЭШ полностью при каждом рефреше (особенно важно при смене дат)
        self.hourly_cache = self._build_empty_hourly_cache()
        self._effective_bounds_cache = effective_bounds

        # Сразу применяем блокировку при загрузке карты
        if self.quick_input:
            self.quick_input.set_quick_input_enabled(self.is_current_shift())

        for f in fluids or []:
            hour = f.timestamp.hour
            if hour in self.hourly_cache:
                cache = self.hourly_cache[hour]
                cache["urine"] += int(f.urine)
                cache["drain_output"] += int(f.drain_output)
                cache["ng_output"] += int(f.ng_output)
                cache["stool"] += int(f.stool)
                cache["other_output"] += int(f.other_output)

        if self.grid:
            self.grid.update_data(self.hourly_cache)
            row_key, hour, val = self.grid.get_selected_info()
            if row_key and self.panel_2d:
                row_idx = self.grid.rows_map.index(row_key)
                label = f"{self.grid.row_labels[row_idx]} ({hour:02d}:00)"
                self.panel_2d.set_selection(label, val if val > 0 else None, keep_focus=False)

        if self.panel_2d:
            self.panel_2d.set_undo_active(len(self._undo_stack) > 0)

        if self.quick_input:
            cumulative_data = self.get_cumulative_data_to_now()
            self.quick_input.update_quick_values(cumulative_data)

        self.data_updated.emit()

    def _on_cell_selected(self, row_idx, hour):
        row_key = self.grid.rows_map[row_idx]
        val = self.hourly_cache[hour].get(row_key, 0)
        label = f"{self.grid.row_labels[row_idx]} ({hour:02d}:00)"
        # Здесь keep_focus=True, так как это ЯВНЫЙ клик пользователя по сетке
        self.panel_2d.set_selection(label, val if val > 0 else None, keep_focus=True)

    def _on_panel_save(self, new_val):
        # ПРОВЕРКА ИСХОДА + 1 ЧАС
        current_sel = self.grid.selectedItems()
        if current_sel:
            item = current_sel[0]
            col = item.column()
            hour = (col + 8) % 24
            
            # Определяем дату для выбранного часа
            dt = self.shift_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if hour < 8 and self.shift_date.hour >= 8:
                dt += timedelta(days=1)
            
            # Получаем статус (безопасный доступ через сервис)
            status_service = getattr(self.service.vital_service, 'status_service', None)
            status_event = status_service.get_current_status(self.admission_id) if status_service else None
            
            if status_event and status_event.status.is_outcome():
                # Лимит: время исхода + 1 час
                limit_time = status_event.start_time + timedelta(hours=1)
                if dt > limit_time:
                    outcome_name = "переведен" if status_event.status == status_event.status.TRANSFERRED else "умер"
                    CustomMessageBox.warning(
                        None, 
                        "Внимание", 
                        f"Пациент {outcome_name} в {status_event.start_time.strftime('%H:%M')}. Ввод выведенного позже {limit_time.strftime('%H:%M')} невозможен."
                    )
                    return

        # Получаем информацию напрямую из выделения сетки, если get_selected_info() подводит для пустых ячеек
        items = self.grid.selectedItems()
        if not items:
            logger.warning("[BalanceCtrl] No cell selected in grid")
            # Если ячейка не выделена визуально (QTableWidget::item:selected), попробуем взять текущую ячейку
            row = self.grid.currentRow()
            col = self.grid.currentColumn()
            if row < 0 or col < 0:
                logger.error("[BalanceCtrl] Really no cell selected")
                return
        else:
            item = items[0]
            row = item.row()
            col = item.column()
            
        hour = (col + 8) % 24
        row_key = self.grid.rows_map[row]
        
        # Получаем текущее значение из кэша (приводим к int)
        old_val = int(self.hourly_cache[hour].get(row_key, 0))
        
        logger.debug(f"[BalanceCtrl] Panel Save: {row_key} at {hour}:00. New: {new_val}, Old: {old_val}")
        
        if old_val == 0:
            # Для пустых ячеек сохраняем сразу (замена/сумма тут не важны, т.к. 0 + X = X)
            self._process_update(row_key, hour, new_val, is_sum=False)
            return

        # Для занятых ячеек - диалог подтверждения (кастомный)
        res = CustomMessageBox.balance_question(
            None, 
            "Подтверждение", 
            f"В этой ячейке уже есть значение {old_val} мл. Что вы хотите сделать?"
        )
        
        if res == CustomMessageBox.SUM:
            self._process_update(row_key, hour, new_val, is_sum=True)
        elif res == CustomMessageBox.REPLACE:
            self._process_update(row_key, hour, new_val, is_sum=False)
        else:
            return # Отмена

    def _on_panel_delete(self):
        row_key, hour, old_val = self.grid.get_selected_info()
        if row_key is None: return
        
        logger.debug(f"[BalanceCtrl] Panel Delete: {row_key} at {hour}:00")
        self._process_update(row_key, hour, 0, is_sum=False)
        self.panel_2d.clear_selection()

    def is_current_shift(self) -> bool:
        """Проверяет, являются ли установленные сутки текущими реанимационными сутками."""
        now = datetime.now()
        if self._effective_bounds_cache:
            start, end = self._effective_bounds_cache
        else:
            # Получаем границы текущих реальных суток через сервис
            start, end = self.service.vital_service.get_effective_bounds(self.admission_id, now)
        return start <= self.shift_date < end

    def add_value(self, row_key: str, input_field):
        """Быстрое добавление значения из Sector2b_v (всегда в текущий час)."""
        if not self.is_current_shift():
            return
            
        text = input_field.text()
        if not text or not text.isdigit(): return
        
        val = int(text)
        now = datetime.now()
        hour = now.hour

        # ПРОВЕРКА ИСХОДА + 1 ЧАС для быстрого ввода
        status_service = getattr(self.service.vital_service, 'status_service', None)
        status_event = status_service.get_current_status(self.admission_id) if status_service else None
        
        if status_event and status_event.status.is_outcome():
            limit_time = status_event.start_time + timedelta(hours=1)
            # Для простоты проверяем текущее время (now) против лимита
            if now > limit_time:
                outcome_name = "переведен" if status_event.status == status_event.status.TRANSFERRED else "умер"
                CustomMessageBox.warning(
                    None, 
                    "Внимание", 
                    f"Пациент {outcome_name} в {status_event.start_time.strftime('%H:%M')}. Ввод выведенного позже {limit_time.strftime('%H:%M')} невозможен."
                )
                return

        logger.debug(f"[BalanceCtrl] Quick Add: {row_key} = {val} ml (hour {hour})")
        
        # Проверяем, есть ли уже значение
        current_hour = self.hourly_cache.setdefault(hour, self._build_empty_hourly_cache()[hour])
        current_hour_val = current_hour.get(row_key, 0)
        
        if current_hour_val > 0:
            msg_text = f"В часе {hour:02d}:00 уже есть значение {int(current_hour_val)} мл. Добавить {val} мл и суммировать?"
            if self._confirm(msg_text):
                self._process_update(row_key, hour, val, is_sum=True)
                input_field.clear()
        else:
            self._process_update(row_key, hour, val, is_sum=True)
            input_field.clear()

    def _process_update(self, row_key, hour, val, is_sum=False):
        """Сохранение значения выведения по часу через сервисный слой."""
        try:
            result = self.service.upsert_hourly_output(
                admission_id=self.admission_id,
                shift_date=self.shift_date,
                hour=hour,
                row_key=row_key,
                value=val,
                is_sum=is_sum,
            )
            if result["action"] == "add":
                self._undo_stack.append(("add", result["fluid_id"]))
                logger.debug(f"[BalanceCtrl] Created new record {result['fluid_id']} for hour {hour}")
            else:
                self._undo_stack.append(("update", result["fluid_id"], row_key, result["old_value"]))
                logger.debug(
                    f"[BalanceCtrl] Updated record {result['fluid_id']} for hour {hour}. {row_key}: "
                    f"{result['old_value']}->{result['new_value']}"
                )

            self.refresh()
            if self.panel_2d:
                self.panel_2d.set_undo_active(len(self._undo_stack) > 0)
            
        except Exception as e:
            logger.error(f"[BalanceCtrl] Save failed: {e}", exc_info=True)
            CustomMessageBox.critical(None, "Ошибка", f"Не удалось сохранить данные: {e}")

    def undo(self):
        if not self._undo_stack:
            logger.warning("[BalanceCtrl] Undo stack is empty")
            return
            
        action = self._undo_stack.pop()
        try:
            if action[0] == 'add':
                fluid_id = action[1]
                self.service.delete_fluid_by_id(fluid_id)
                logger.debug(f"[BalanceCtrl] Undo ADD: deleted record {fluid_id}")
            elif action[0] == 'update':
                fluid_id, row_key, old_val = action[1], action[2], action[3]
                self.service.restore_hourly_output(fluid_id, row_key, old_val)
                logger.debug(f"[BalanceCtrl] Undo UPDATE: record {fluid_id}, {row_key} restored to {old_val}")

            self.refresh()
            if self.panel_2d:
                self.panel_2d.set_undo_active(len(self._undo_stack) > 0)
        except Exception as e:
            logger.error(f"[BalanceCtrl] Undo failed: {e}")

    def _confirm(self, text):
        return CustomMessageBox.question(None, "Подтверждение", text) == CustomMessageBox.Yes

    def get_total_out_to_now(self) -> int:
        """Рассчитывает сумму всего выведения по сетке (до сейчас или за 24ч для архива)."""
        data = self.get_cumulative_data_to_now()
        return sum(int(v) for v in data.values())

    def get_total_out_daily(self) -> int:
        """Рассчитывает сумму всего выведения за полные сутки (24 часа)."""
        data = self.get_cumulative_data_daily()
        return sum(int(v) for v in data.values())

    def get_cumulative_data_to_now(self) -> dict:
        """Возвращает словарь с накопленными суммами до текущего часа (или за 24ч для архива)."""
        if not self.is_current_shift():
            return self.get_cumulative_data_daily()

        totals = {
            "urine": 0, "drain_output": 0, "ng_output": 0, 
            "stool": 0, "other_output": 0
        }
        now_hour = datetime.now().hour
        
        for hour, data in self.hourly_cache.items():
            # Текущий час в координатах смены (0-23, где 0 это 08:00)
            rel_now = (now_hour - 8 + 24) % 24
            rel_hour = (hour - 8 + 24) % 24
            
            if rel_hour <= rel_now:
                for key in totals:
                    totals[key] += int(data.get(key, 0))
                    
        return totals

    def get_cumulative_data_daily(self) -> dict:
        """Возвращает словарь с накопленными суммами за все 24 часа смены."""
        totals = {
            "urine": 0, "drain_output": 0, "ng_output": 0, 
            "stool": 0, "other_output": 0
        }
        for hour, data in self.hourly_cache.items():
            for key in totals:
                totals[key] += int(data.get(key, 0))
        return totals

    def refresh_on_tick(self):
        """Метод вызывается по таймеру каждую минуту для обновления UI."""
        if not self.grid or not self.quick_input:
            return
            
        # Блокируем или разблокируем поля в зависимости от того, текущие ли это сутки
        is_today = self.is_current_shift()
        self.quick_input.set_quick_input_enabled(is_today)

        # ЖЕСТКАЯ ПРОВЕРКА ФОКУСА ДЛЯ БЫСТРОГО ВВОДА
        # Если хоть одно поле быстрого ввода имеет фокус или содержит текст - не обновляем X и не трогаем refresh()
        quick_fields = [self.quick_input.diurez_val, self.quick_input.drenazh_val, 
                        self.quick_input.zond_val, self.quick_input.rvota_val, self.quick_input.other_val]
        
        is_busy = any(f.hasFocus() or f.text().strip() for f in quick_fields)
        
        # Если пользователь вводит в ручной ввод (2д)
        if self.panel_2d and (self.panel_2d.edit_input.hasFocus() or self.panel_2d.edit_input.text().strip()):
            is_busy = True

        if is_busy:
            return

        # 1. Обновляем значения X в полях быстрого ввода (мог наступить новый час)
        # Теперь X показывает накопленный итог для каждого показателя до текущего часа
        cumulative_data = self.get_cumulative_data_to_now()
        self.quick_input.update_quick_values(cumulative_data)
        
        # Сигнал НЕ посылаем, чтобы избежать рекурсии. 
        # DoctorRemCardWidget сам вызовет расчет баланса следом за этим методом.
