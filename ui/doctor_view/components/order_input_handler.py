import re
from datetime import datetime
from rem_card.data.dto.remcard_dto import OrderDTO, OrderType, ScheduleEngine
from rem_card.services.prescription_engine import engine

class OrderInputHandler:
    """Логика парсинга текстового ввода назначений в объекты OrderDTO."""
    
    @staticmethod
    def parse_input_to_dto(text: str, admission_id: int) -> OrderDTO:
        # --- ИЗОЛИРОВАННАЯ ВЕТКА ДЛЯ МНОГОКОМПОНЕНТНЫХ ПРЕПАРАТОВ ---
        explicit_key_match = re.search(r'\[KEY:(.*?)\]', text)
        if explicit_key_match:
            drug_key = explicit_key_match.group(1)
            drug_data = engine.drugs.get(drug_key, {})
            if drug_data.get("is_multicomp"):
                text = text.replace(explicit_key_match.group(0), "").strip()
                
                # Извлекаем теги
                diluent_tag_match = re.search(r'\[DIL:(.*?)\]', text)
                diluent_part = ""
                if diluent_tag_match:
                    diluent_part = diluent_tag_match.group(1).strip()
                    text = text.replace(diluent_tag_match.group(0), "").strip()

                route_match = re.search(r'\[ROUTE:(.*?)\]', text)
                route_from_tag = ""
                if route_match:
                    route_from_tag = route_match.group(1).strip()
                    text = text.replace(route_match.group(0), "").strip()

                dur_match = re.search(r'\[DUR:(.*?)\]', text)
                duration = 0
                if dur_match:
                    try:
                        duration = int(dur_match.group(1))
                    except ValueError:
                        pass
                    text = text.replace(dur_match.group(0), "").strip()

                text = text.replace("[RU]", "").strip()

                # Оставшаяся строка - это только компоненты
                drug_part = text
                latin_name = drug_part
                unit = ""
                dose = 0.0
                
                admin_type = drug_data.get("admin_type", "bolus")
                otype = OrderType.MEDICATION
                if admin_type in ["infusion", "continuous"] or "инф" in text.lower():
                    otype = OrderType.INFUSION_CONTINUOUS
                    
                freq_match = re.search(r"(\d+)р", text)
                freq = int(freq_match.group(1)) if freq_match else 1
                
                route_text = route_from_tag if route_from_tag else engine.admin_types.get(admin_type, {}).get("name_ru", "")
                dur_text = ""
                if duration == -1:
                    dur_text = "до конца суток"
                elif duration > 0:
                    dur_text = f"{duration} мин"

                diluent_info = diluent_part if diluent_part else ""
                if route_from_tag:
                    diluent_info += f" [ROUTE:{route_from_tag}]"
                if duration != 0:
                    diluent_info += f" [DUR:{duration}]"

                return OrderDTO(
                    admission_id=admission_id,
                    drug_key=drug_key,
                    latin=latin_name,
                    type=otype,
                    dose_value=dose,
                    dose_unit=unit,
                    is_per_kg=False,
                    frequency=freq,
                    specific_times=ScheduleEngine.generate_times(freq),
                    duration_min=duration,
                    is_committed=0,
                    created_at=datetime.now(),
                    comment=diluent_info.strip()
                )

        # --- СТАРАЯ ОРИГИНАЛЬНАЯ ВЕТКА ДЛЯ ОБЫЧНЫХ ПРЕПАРАТОВ ---
        # 1. Разделение на препарат и растворитель
        if text.count("+") > 1:
            last_plus_idx = text.rfind("+")
            drug_part = text[:last_plus_idx].strip()
            diluent_part = text[last_plus_idx+1:].strip()
        else:
            parts = text.split("+")
            drug_part = parts[0].strip()
            diluent_part = parts[1].strip() if len(parts) > 1 else ""

        clean_drug_part = drug_part
        found_prefix = ""
        prefix_match = re.match(r'^([A-Za-z]+\.)\s+', drug_part)
        if prefix_match:
            found_prefix = prefix_match.group(1)
            clean_drug_part = drug_part[prefix_match.end():]
            
        dose_match = re.search(r"(\d+\.?\d*)", clean_drug_part)
        if dose_match:
            search_term = clean_drug_part[:dose_match.start()].strip()
        else:
            search_term = clean_drug_part.strip()
        
        if not search_term:
            search_term = clean_drug_part.split()[0] if clean_drug_part else ""

        text_lower = text.lower()
        if "ruki" in text_lower or "ruchnoivvod" in text_lower or "[ru]" in text_lower:
            display_latin = text.replace("[RU]", "").replace("[ru]", "").strip()
            resolved_drug_key = None
            resolved_drug_data = {}

            if explicit_key_match:
                explicit_key = explicit_key_match.group(1).strip().lower()
                if explicit_key:
                    resolved_drug_key = explicit_key
                    resolved_drug_data = engine.drugs.get(explicit_key, {}) or {}
                display_latin = display_latin.replace(explicit_key_match.group(0), "").strip()
            
            comment_parts = []
            
            dose_val = 0.0
            dose_match = re.search(r'\[DOSE:(.*?)\]', display_latin)
            if dose_match:
                try:
                    dose_val = float(dose_match.group(1))
                except:
                    pass
                display_latin = display_latin.replace(dose_match.group(0), "").strip()
                
            dose_unit = ""
            unit_match = re.search(r'\[UNIT:(.*?)\]', display_latin)
            if unit_match:
                dose_unit = unit_match.group(1)
                display_latin = display_latin.replace(unit_match.group(0), "").strip()
            
            route_match = re.search(r'(\[ROUTE:.*?\])', display_latin)
            if route_match:
                comment_parts.append(route_match.group(1))
                display_latin = display_latin.replace(route_match.group(1), "").strip()
            
            dur_match = re.search(r'(\[DUR:(.*?)\])', display_latin)
            duration_min = 0
            if dur_match:
                comment_parts.append(dur_match.group(1))
                try:
                    duration_min = int(dur_match.group(2))
                except:
                    pass
                display_latin = display_latin.replace(dur_match.group(1), "").strip()
            elif resolved_drug_data:
                try:
                    duration_min = int(resolved_drug_data.get("duration_min", 0) or 0)
                except Exception:
                    duration_min = 0
                
            if "+" in display_latin:
                parts = display_latin.split("+", 1)
                display_latin = parts[0].strip()
                diluent = parts[1].strip()
                if diluent:
                    comment_parts.insert(0, diluent)
            
            if display_latin.lower() == "ruki" or display_latin.lower() == "ruchnoivvod":
                display_latin = "Ручной ввод"
                
            final_comment = " ".join(comment_parts)
            display_latin = " ".join(display_latin.split())

            if not resolved_drug_key and display_latin:
                normalized = re.sub(r"[^0-9a-zа-яё]+", "", display_latin.lower())
                if any(token in normalized for token in ("сзп", "плазм", "plasma", "ffp")):
                    resolved_drug_key = "plasma"
                elif any(token in normalized for token in ("эрмас", "эритро", "кров", "blood", "rbc")):
                    resolved_drug_key = "blood"

                cleaned_search = re.sub(r"[^0-9a-zа-яё]+", " ", display_latin.lower()).strip()
                if cleaned_search and not resolved_drug_key:
                    found_key, _ = engine.detect_drug(cleaned_search)
                    if found_key in ("blood", "plasma"):
                        resolved_drug_key = found_key
                
            freq_match = re.search(r"(\d+)р", text)
            freq = int(freq_match.group(1)) if freq_match else 1

            admin_type = str(resolved_drug_data.get("admin_type", "") or "").lower()
            route_hint = " ".join(comment_parts).lower()
            otype = OrderType.MEDICATION
            if duration_min != 0 or admin_type in ("infusion", "continuous") or "инф" in route_hint:
                otype = OrderType.INFUSION_CONTINUOUS
                
            return OrderDTO(
                admission_id=admission_id,
                drug_key=resolved_drug_key or "ruchnoivvod",
                latin=display_latin,
                type=otype,
                dose_value=dose_val,
                dose_unit=dose_unit,
                frequency=freq,
                specific_times=ScheduleEngine.generate_times(freq) if resolved_drug_key else [],
                duration_min=duration_min,
                is_committed=0,
                created_at=datetime.now(),
                comment=final_comment
            )

        drug_data = None
        
        if explicit_key_match:
            drug_key = explicit_key_match.group(1)
            drug_data = engine.drugs.get(drug_key)
            if diluent_part:
                diluent_part = diluent_part.replace(explicit_key_match.group(0), "").strip()
        else:
            drug_key = search_term.lower()
            for k, v in engine.drugs.items():
                if v.get("latin", "").lower() == search_term.lower():
                    drug_key = k
                    drug_data = v
                    break
                    
            if not drug_data:
                drug_key, drug_data = engine.detect_drug(search_term)
            
        dose = engine.parse_dose(drug_part)
        if dose is None:
            dose = drug_data.get("default_dose", 1.0) if drug_data else 1.0
            
        freq_match = re.search(r"(\d+)р", text)
        freq = int(freq_match.group(1)) if freq_match else 1

        duration = 0
        dur_match = re.search(r'\[DUR:(.*?)\]', text)
        if dur_match:
            try:
                duration = int(dur_match.group(1))
            except ValueError:
                pass
            if diluent_part:
                diluent_part = diluent_part.replace(dur_match.group(0), "").strip()
        elif "до конца суток" in text.lower():
            duration = -1
        else:
            duration_match = re.search(r"(\d+)\s*мин", text.lower())
            duration = int(duration_match.group(1)) if duration_match else (drug_data.get("duration_min", 0) if drug_data else 0)
        
        if diluent_part:
            diluent_part = re.sub(r'\[ROUTE:.*?\]', '', diluent_part).strip()
            diluent_part = re.sub(r'\[UNIT:.*?\]', '', diluent_part).strip()
            diluent_part = re.sub(r'\[DOSE:.*?\]', '', diluent_part).strip()
        
        if drug_data:
            latin_name = drug_data.get("latin", "").capitalize() or drug_key.capitalize()
            unit = drug_data.get("unit", "mg")
            admin_type = drug_data.get("admin_type", "bolus")
        else:
            latin_name = f"{found_prefix} {search_term.capitalize()}" if found_prefix else search_term.capitalize()
            unit = "g" if dose < 10 else "mg"
            admin_type = "bolus"
            
        otype = OrderType.MEDICATION
        if admin_type in ["infusion", "continuous"] or "инф" in text.lower():
            otype = OrderType.INFUSION_CONTINUOUS
            
        diluent_info = diluent_part
            
        return OrderDTO(
            admission_id=admission_id,
            drug_key=drug_key,
            latin=latin_name,
            type=otype,
            dose_value=dose,
            dose_unit=unit,
            is_per_kg=("/кг" in text or "мкг" in text.lower()),
            frequency=freq,
            specific_times=ScheduleEngine.generate_times(freq),
            duration_min=duration,
            is_committed=0,
            created_at=datetime.now(),
            comment=diluent_info
        )
