import os
import re
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
from datetime import datetime, timedelta
from ...data.dto.remcard_dto import OrderType, OrderStatus
from ...services.order_domain_service import (
    NURSE_MARK_EXECUTED,
    NURSE_MARK_NOT_EXECUTED,
)
from ..styles.theme import BG_ALT_ROW

class OrdersDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.now_line_color = QColor(231, 76, 60, 150) # Прозрачный красный
        self._icon_cache = {}
        from rem_card.app.paths import get_icon_dir
        self._mark_icon_paths = {
            NURSE_MARK_EXECUTED: os.path.join(get_icon_dir(), "done.png"),
            NURSE_MARK_NOT_EXECUTED: os.path.join(get_icon_dir(), "notdone.png"),
        }

    def _get_mark_pixmap(self, mark: str):
        path = self._mark_icon_paths.get(mark)
        if not path:
            return None
        if path in self._icon_cache:
            return self._icon_cache[path]

        if not os.path.exists(path):
            self._icon_cache[path] = None
            return None

        pm = QPixmap(path)
        if pm.isNull():
            self._icon_cache[path] = None
            return None

        self._icon_cache[path] = pm
        return pm

    def _format_duration(self, minutes: int) -> str:
        if not minutes or minutes <= 0:
            return ""
        if minutes < 60:
            return f"{minutes} мин."
        else:
            hours = round(minutes / 60.0, 1)
            hours_str = str(hours).replace('.', ',')
            return f"{hours_str} ч."

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        # Проверка валидности модели
        model = index.model()
        if not model:
            return

        # РИСУЕМ СЕТКУ ДЛЯ ВСЕХ ЯЧЕЕК (даже если нет данных)
        painter.save()
        
        # Рисуем ячейку
        r = option.rect
        
        # 1. Сначала рисуем все серые линии сетки
        # (Используем drawLine вместо drawRect для лучшего контроля, если нужно)
        painter.setPen(QPen(QColor(220, 221, 225), 0.5))
        painter.drawLine(r.left(), r.top(), r.right(), r.top())       # Верх
        painter.drawLine(r.left(), r.bottom(), r.right(), r.bottom()) # Низ
        painter.drawLine(r.left(), r.top(), r.left(), r.bottom())     # Лево
        painter.drawLine(r.right(), r.top(), r.right(), r.bottom())    # Право
        
        painter.restore()

        # Получаем данные заказа из UserRole для обеих колонок
        order_or_admin = model.data(index, Qt.UserRole)

        if index.column() == 0:
            order = order_or_admin # В первой колонке это OrderDTO
            if not order:
                return
                
            painter.save()
            # Очищаем фон
            if option.features & QStyleOptionViewItem.Alternate:
                painter.fillRect(option.rect, QColor(BG_ALT_ROW))
            else:
                painter.fillRect(option.rect, Qt.white)
                
            # Рисуем границу
            painter.setPen(QPen(QColor(220, 221, 225), 0.5))
            painter.drawRect(option.rect)

            # Безопасное получение данных
            latin = order.latin if hasattr(order, 'latin') and order.latin else "Без названия"
            dose_val = order.dose_value if hasattr(order, 'dose_value') and order.dose_value is not None else 0
            dose_unit = order.dose_unit if hasattr(order, 'dose_unit') and order.dose_unit else ""
            order_type = order.type if hasattr(order, 'type') else OrderType.PROCEDURE
            drug_key = str(getattr(order, 'drug_key', '') or '').strip().lower()

            # Формируем 1 строку: Форма Препарат Доза
            # Для ручного ввода, компонентов крови или если префикс уже есть в названии, не добавляем S.
            # Префикс определяем как любое слово, заканчивающееся на точку, в начале строки (например, S. Tab. Supp.)
            if drug_key in ('ruchnoivvod', 'plasma', 'blood') or re.match(r'^[A-Za-z]+\. ', latin.strip()):
                prefix = ""
            else:
                prefix = "S. " if order_type != OrderType.PROCEDURE else ""
                
            dose_str = f"{dose_val:g} {dose_unit}".strip()
            if dose_str == "0":
                dose_str = ""
            
            # Безопасное получение веса
            model_ctx = getattr(model, 'patient_context', None)
            if getattr(order, 'is_per_kg', False) and model_ctx and hasattr(model_ctx, 'weight') and model_ctx.weight and dose_val > 0:
                # Используем кэширование или пре-расчитанное значение было бы лучше, 
                # но пока просто берем из контекста. Метод calculate_dose делает округление.
                calc_dose = model_ctx.calculate_dose(dose_val)
                if calc_dose is not None:
                    dose_str = f"{dose_val:g} {dose_unit}/kg ({calc_dose:g} {dose_unit})"
                
            line1_text = f"{prefix}{latin} {dose_str}".strip()
            
            # Формируем 2 строку: Растворитель, способ введения, длительность
            line2_text = ""
            line2_parts = []
            
            # Извлекаем данные из комментария
            comment_text = getattr(order, 'comment', "") or ""
            
            # Ищем растворитель (все, что до тегов)
            diluent = comment_text
            diluent = re.sub(r'\[ROUTE:.*?\]', '', diluent)
            diluent = re.sub(r'\[DUR:.*?\]', '', diluent)
            diluent = diluent.replace("[RU]", "").strip()
            
            if diluent and not diluent.isspace():
                # Убираем ведущий "+" и возможный префикс "S." если есть
                if diluent.startswith("+"):
                    diluent = diluent[1:].strip()
                
                if diluent:
                    # Убираем старый S. если он был, чтобы не дублировать
                    if diluent.startswith("S. "):
                        diluent = diluent[3:].strip()
                    
                    # Добавляем тире перед объемом, если его еще нет
                    if " - " not in diluent:
                        diluent = re.sub(r'\s+(\d+)\s*(мл|ml)', r' - \1 \2', diluent)
                    
                    line2_parts.append(f"S. {diluent}")
                
            route_dur_parts = []
            
            # Ищем путь введения
            route_match = re.search(r'\[ROUTE:(.*?)\]', comment_text)
            if route_match:
                route_dur_parts.append(route_match.group(1))
                
            # Ищем длительность
            dur_match = re.search(r'\[DUR:(.*?)\]', comment_text)
            duration_val = 0
            if dur_match:
                try:
                    duration_val = int(dur_match.group(1))
                except:
                    pass
            else:
                duration_val = getattr(order, 'duration_min', 0)
                
            try:
                duration_val = int(duration_val)
            except:
                duration_val = 0
                
            if duration_val == -1:
                route_dur_parts.append("до конца суток")
            elif duration_val > 0:
                route_dur_parts.append(self._format_duration(duration_val))
                
            if route_dur_parts:
                line2_parts.append(" - ".join(route_dur_parts))
                
            # Если нет тегов, но есть старый текстовый коммент (обратная совместимость)
            if comment_text and not route_match and not dur_match and not "[RU]" in comment_text:
                old_text = comment_text.strip()
                # Пытаемся отформатировать минуты, если есть
                match = re.search(r"(\d+)\s*мин", old_text)
                if match:
                    mins = int(match.group(1))
                    formatted = self._format_duration(mins)
                    old_text = old_text.replace(match.group(0), formatted)
                if old_text and old_text not in line2_parts:
                     # Если это просто название растворителя, оно уже в diluent
                     if not diluent or old_text != diluent:
                        line2_parts = [old_text]
            
            line2_text = ", ".join(line2_parts)
            
            # Отрисовка текста
            painter.setPen(Qt.black)
            
            # Рисуем первую строку (сверху)
            rect1 = QRect(option.rect.left() + 5, option.rect.top() + 5, option.rect.width() - 10, 20)
            
            # Убираем перенос слов, добавляем многоточие если текст слишком длинный
            font_metrics = painter.fontMetrics()
            elided_line1 = font_metrics.elidedText(line1_text, Qt.ElideRight, rect1.width())
            painter.drawText(rect1, Qt.AlignLeft | Qt.AlignVCenter, elided_line1)
            
            # Рисуем вторую строку (снизу) серым цветом, если она есть
            if line2_text:
                painter.setPen(QColor(120, 120, 120))
                rect2 = QRect(option.rect.left() + 5, option.rect.top() + 25, option.rect.width() - 10, 15)
                elided_line2 = font_metrics.elidedText(line2_text, Qt.ElideRight, rect2.width())
                painter.drawText(rect2, Qt.AlignLeft | Qt.AlignVCenter, elided_line2)
            
            # Рисуем значок savecard.png в верхнем правом углу, если карта сохранена
            if getattr(order, 'is_finalized', False):
                # Берем готовый флаг из модели (кеш), чтобы не делать O(N) обходы в paint.
                has_any_draft = getattr(model, 'has_any_draft', False)
                
                # Показываем только если нет черновиков во всей карте
                if not has_any_draft:
                    import os
                    from PySide6.QtGui import QPixmap
                    from rem_card.app.paths import get_icon_dir
                    icon_path = os.path.join(get_icon_dir(), "savecard.png")
                    if os.path.exists(icon_path):
                        pixmap = QPixmap(icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        icon_x = option.rect.right() - 20
                        icon_y = option.rect.top() + 5
                        painter.drawPixmap(icon_x, icon_y, pixmap)

            painter.restore()
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        rect = option.rect
        
        # Извлекаем данные о ячейке из модели (UserRole возвращает AdministrationDTO)
        admin = order_or_admin # В колонках времени это AdministrationDTO
        time_slots = getattr(model, 'time_slots', [])
        col_idx = index.column() - 1
        if col_idx < 0 or col_idx >= len(time_slots):
            painter.restore()
            return
        hour_dt = time_slots[col_idx]

        if admin:
            if admin.status == "cancelled":
                painter.setPen(Qt.black)
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(rect, Qt.AlignCenter, "Отм")
            elif admin.status == "planned":
                painter.save()
                painter.setPen(Qt.black)
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                
                # Рисуем "X" или иконку выполнения (по отметке из БД) для START/SINGLE/END.
                mark = getattr(admin, "comment", "") or ""
                mark_pixmap = None
                if admin.cell_role != "body":
                    if admin.cell_role in ("start", "single", "end"):
                        mark_pixmap = self._get_mark_pixmap(mark)

                    if mark_pixmap:
                        # Размер иконки делаем сопоставимым с сектором 5.
                        icon_size = min(28, max(14, min(rect.width(), rect.height()) - 6))
                        scaled = mark_pixmap.scaled(
                            icon_size, icon_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        x = rect.left() + (rect.width() - scaled.width()) // 2
                        y = rect.top() + (rect.height() - scaled.height()) // 2
                        painter.drawPixmap(x, y, scaled)
                    else:
                        painter.drawText(rect, Qt.AlignCenter, "X")
                
                # Рисуем линии для цепей
                if admin.cell_role in ("start", "body", "end"):
                    line_y = int(rect.center().y())
                    cx = int(rect.center().x())
                    line_pen = QPen(Qt.black, 1.5)
                    painter.setPen(line_pen)

                    if admin.cell_role == "start":
                        painter.drawLine(cx + 10, line_y, rect.right(), line_y)
                    elif admin.cell_role == "body":
                        painter.drawLine(rect.left(), line_y, rect.right(), line_y)
                    elif admin.cell_role == "end":
                        painter.drawLine(rect.left(), line_y, cx - 10, line_y)
                        
                        # Рисуем наконечник стрелки
                        painter.setBrush(Qt.black)
                        arrow_size = 5
                        from PySide6.QtGui import QPolygon
                        arrow = QPolygon([
                            QPoint(cx - 10, line_y),
                            QPoint(cx - 10 - arrow_size, line_y - arrow_size),
                            QPoint(cx - 10 - arrow_size, line_y + arrow_size),
                        ])
                        painter.drawPolygon(arrow)

                    if admin.cell_role in ("body", "end"):
                        body_mark_pixmap = self._get_mark_pixmap(mark)
                        if body_mark_pixmap:
                            base_icon_size = min(24, max(14, min(rect.width(), rect.height()) - 8))
                            icon_size = (
                                max(10, int(round(base_icon_size * 0.7)))
                                if admin.cell_role == "body"
                                else base_icon_size
                            )
                            scaled = body_mark_pixmap.scaled(
                                icon_size, icon_size,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            x = rect.left() + (rect.width() - scaled.width()) // 2
                            y = rect.top() + (rect.height() - scaled.height()) // 2
                            painter.drawPixmap(x, y, scaled)
                
                painter.restore()
            elif admin.status == "deleted":
                pass

        # Отрисовка NOW-маркера
        self._draw_now_marker(painter, rect, hour_dt)

        # 2. Если нужна черная линия, рисуем её В САМОМ КОНЦЕ метода paint, 
        # чтобы она была поверх всего содержимого ячейки
        if index.column() > 0:
            time_slots = getattr(model, 'time_slots', [])
            col_idx = index.column() - 1
            if col_idx < len(time_slots):
                if time_slots[col_idx].hour in [13, 19, 1]:
                    # ВАЖНО: Рисуем черную линию ПОВЕРХ ВСЕГО
                    painter.setPen(QPen(Qt.black, 1.5)) # Сделаем 1.5 для уверенности
                    # Смещаем на 1.0 пиксель правее (суммарно 0.5 + 0.5 = 1.0)
                    x = rect.right() + 1.0
                    painter.drawLine(x, rect.top(), x, rect.bottom())

        painter.restore()

    def _draw_now_marker(self, painter, rect, hour_dt):
        now = datetime.now()
        # Проверяем попадание в час. Учитываем, что hour_dt - это начало часа.
        if now >= hour_dt and now < (hour_dt + timedelta(hours=1)):
            # Рассчитываем положение линии внутри часа
            minute_ratio = now.minute / 60.0
            pos_x = rect.left() + int(rect.width() * minute_ratio)
            
            painter.setPen(QPen(self.now_line_color, 2))
            painter.drawLine(pos_x, rect.top(), pos_x, rect.bottom())
