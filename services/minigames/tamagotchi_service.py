from __future__ import annotations

import random
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from rem_card.services.minigames.minigame_paths import PathLikeProvider
from rem_card.services.minigames.minigame_user_store import MinigameUserStore


MAX_OFFLINE_MINUTES = 8 * 60
EGG_MINUTES = 30
TEEN_MINUTES = 240
ADULT_MINUTES = 960
ELDER_MINUTES = 2880
DEMENTIA_MINUTES = 4320
DEAD_MINUTES = 5760
POOP_INTERVAL_MINUTES = 90
PEE_INTERVAL_MINUTES = 65
VOMIT_INTERVAL_MINUTES = 45

DEFAULT_TAMAGOTCHI_STATE = {
    "schema_version": 1,
    "pet_id": None,
    "name": None,
    "created_at": None,
    "last_updated_at": None,
    "age_minutes": 0,
    "stage": "egg",
    "animal": None,
    "rarity": "normal",
    "hunger": 85,
    "happiness": 75,
    "cleanliness": 90,
    "energy": 85,
    "health": 100,
    "anger": 0,
    "stress": 8,
    "discipline": 55,
    "weight": 0.5,
    "poops": 0,
    "pees": 0,
    "vomits": 0,
    "poop_meter": 0,
    "pee_meter": 0,
    "vomit_meter": 0,
    "sick": False,
    "sleeping": False,
    "alive": True,
    "care_misses": 0,
    "hunger_neglect": 0,
    "dirty_neglect": 0,
    "play_neglect": 0,
    "sick_neglect": 0,
    "last_event": "Питомец ждёт заботы.",
}

STAGE_LABELS = {
    "egg": "Яйцо",
    "child": "Ребёнок",
    "teen": "Подросток",
    "adult": "Взрослый",
    "elder": "Пожилой",
    "dementia": "Дед с деменцией",
    "dead": "Умер",
}

ANIMAL_LABELS = {
    "tiger": "Тигр",
    "elephant": "Слон",
    "giraffe": "Жираф",
    "chipmunk": "Бурундук",
    "dog": "Собака",
    "cat": "Кот",
    "mammoth": "Мамонт",
    "unicorn": "Единорог",
}

ANIMAL_WEIGHTS = (
    ("dog", 20),
    ("cat", 20),
    ("tiger", 14),
    ("chipmunk", 14),
    ("giraffe", 10),
    ("elephant", 9),
    ("mammoth", 8),
    ("unicorn", 5),
)
TAMAGOTCHI_NAMES = (
    "Пухляш",
    "Жмых",
    "Бублик",
    "Пупсень",
    "Чупакабрёнок",
    "Кексик",
    "Пельмеш",
    "Жулик",
    "Шмяк",
    "Комочек",
    "Господин Хрю",
    "Доктор Писк",
    "Барон Жмяк",
    "Сэр Пупырка",
    "Граф Кусь",
    "Капитан Сопля",
    "Профессор Бульк",
    "Лорд Пыщ",
    "Генерал Хрум",
    "Месье Тыгыдык",
    "Лежебок",
    "Сонька",
    "Дрыхлик",
    "Тюлень",
    "Подушка",
    "Зевун",
    "Обломыч",
    "Полежайкин",
    "Храпун",
    "Сплюха",
    "Жорик",
    "Пельмень",
    "Сосисыч",
    "Батон",
    "Хомяк",
    "Майонезик",
    "Борщун",
    "Котлетыч",
    "Шаурмёнок",
    "Гречкин",
    "Кирпичик",
    "Унитазик",
    "Табурет",
    "Пупырчатый",
    "Боброфей",
    "Макаронтий",
    "Шлёпсон",
    "Кусь-Кусь",
    "Хрумзик",
    "Бубундрий",
)
STAGE_RANKS = {"egg": 0, "child": 1, "teen": 2, "adult": 3, "elder": 4, "dementia": 5, "dead": 6}
EGG_WEIGHT_LIMITS_KG = (0.25, 1.2)
ANIMAL_STAGE_WEIGHT_LIMITS_KG = {
    "tiger": {
        "child": (1.0, 35.0),
        "teen": (35.0, 95.0),
        "adult": (95.0, 260.0),
        "elder": (85.0, 235.0),
        "dementia": (70.0, 205.0),
    },
    "elephant": {
        "child": (110.0, 650.0),
        "teen": (650.0, 2200.0),
        "adult": (2300.0, 5200.0),
        "elder": (2100.0, 4800.0),
        "dementia": (1800.0, 4200.0),
    },
    "giraffe": {
        "child": (65.0, 300.0),
        "teen": (300.0, 750.0),
        "adult": (800.0, 1200.0),
        "elder": (700.0, 1100.0),
        "dementia": (600.0, 1000.0),
    },
    "chipmunk": {
        "child": (0.003, 0.03),
        "teen": (0.03, 0.08),
        "adult": (0.066, 0.15),
        "elder": (0.055, 0.13),
        "dementia": (0.045, 0.11),
    },
    "dog": {
        "child": (0.25, 5.0),
        "teen": (5.0, 18.0),
        "adult": (12.0, 35.0),
        "elder": (10.0, 32.0),
        "dementia": (8.0, 28.0),
    },
    "cat": {
        "child": (0.1, 0.9),
        "teen": (0.9, 3.0),
        "adult": (3.0, 6.0),
        "elder": (2.8, 5.5),
        "dementia": (2.3, 5.0),
    },
    "mammoth": {
        "child": (90.0, 800.0),
        "teen": (800.0, 3000.0),
        "adult": (4500.0, 7300.0),
        "elder": (4000.0, 6800.0),
        "dementia": (3500.0, 6000.0),
    },
    "unicorn": {
        "child": (50.0, 180.0),
        "teen": (180.0, 400.0),
        "adult": (380.0, 850.0),
        "elder": (330.0, 750.0),
        "dementia": (280.0, 650.0),
    },
}
_RNG = random.Random()


class TamagotchiService:
    def __init__(
        self,
        data_root_provider: PathLikeProvider = None,
        user_store: Optional[MinigameUserStore] = None,
    ):
        self.user_store = user_store or MinigameUserStore(data_root_provider)

    def load_state(self, user_id: str) -> Dict[str, Any]:
        user = self.user_store.get_user(user_id)
        progress = user.setdefault("progress", {})
        state = progress.get("tamagotchi")
        created = not isinstance(state, dict)
        if created:
            state = new_tamagotchi_state()
            progress["tamagotchi"] = state

        self.normalize_state(state)
        elapsed_minutes = _elapsed_minutes_since(state.get("last_updated_at"))
        if elapsed_minutes > 0:
            self.advance_state(state, min(elapsed_minutes, MAX_OFFLINE_MINUTES), offline=True)
            state["last_updated_at"] = _now_iso()
            created = True

        if created:
            _sync_best_alive_record(progress, state)
            self.user_store.save_user(user)
        return deepcopy(state)

    def save_state(self, user_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        clean_state = deepcopy(state)
        self.normalize_state(clean_state)
        clean_state["last_updated_at"] = _now_iso()
        user = self.user_store.get_user(user_id)
        progress = user.setdefault("progress", {})
        progress["tamagotchi"] = clean_state
        _sync_best_alive_record(progress, clean_state)
        self.user_store.save_user(user)
        return deepcopy(clean_state)

    def tick(
        self,
        user_id: str,
        state: Dict[str, Any],
        *,
        minutes: int = 1,
        save: bool = False,
    ) -> Dict[str, Any]:
        clean_state = deepcopy(state)
        self.normalize_state(clean_state)
        self.advance_state(clean_state, minutes)
        if save or not clean_state.get("alive", True):
            return self.save_state(user_id, clean_state)
        clean_state["last_updated_at"] = _now_iso()
        return clean_state

    def perform_action(self, user_id: str, state: Dict[str, Any], action: str) -> Tuple[Dict[str, Any], str]:
        clean_state = deepcopy(state)
        self.normalize_state(clean_state)
        action = str(action or "").strip().lower()

        if action == "reset":
            old_pet_id = str(clean_state.get("pet_id") or "")
            clean_state = new_tamagotchi_state()
            message = "Новый питомец появился."
            clean_state["last_event"] = message
            self._save_reset_state(user_id, old_pet_id, clean_state)
            return deepcopy(clean_state), message

        if not clean_state.get("alive", True):
            return clean_state, "Питомец больше не реагирует. Можно начать заново."

        if action == "feed":
            if clean_state["hunger"] >= 100:
                clean_state["anger"] = _clamp(clean_state["anger"] + 3)
                clean_state["stress"] = _clamp(clean_state["stress"] + 2)
                message = "Питомец уже сыт."
            else:
                clean_state["hunger"] = _clamp(clean_state["hunger"] + 24)
                clean_state["happiness"] = _clamp(clean_state["happiness"] + 3)
                clean_state["health"] = _clamp(clean_state["health"] + 2)
                clean_state["anger"] = _clamp(clean_state["anger"] - 8)
                clean_state["stress"] = _clamp(clean_state["stress"] - 3)
                clean_state["hunger_neglect"] = 0
                clean_state["weight"] = _adjust_weight(clean_state, _care_weight_delta(clean_state, 0.018))
                message = "Питомец поел."
        elif action == "snack":
            clean_state["hunger"] = _clamp(clean_state["hunger"] + 8)
            clean_state["happiness"] = _clamp(clean_state["happiness"] + 18)
            clean_state["anger"] = _clamp(clean_state["anger"] - 6)
            clean_state["stress"] = _clamp(clean_state["stress"] - 4)
            clean_state["weight"] = _adjust_weight(clean_state, _care_weight_delta(clean_state, 0.03))
            if float(clean_state["weight"]) > _target_weight_for_state(clean_state) * 1.25:
                clean_state["health"] = _clamp(clean_state["health"] - 4)
                clean_state["energy"] = _clamp(clean_state["energy"] - 3)
                message = "Сладость понравилась, но лучше не перекармливать."
            else:
                message = "Питомец рад сладости."
        elif action == "play":
            if clean_state["energy"] < 12:
                clean_state["happiness"] = _clamp(clean_state["happiness"] - 2)
                clean_state["anger"] = _clamp(clean_state["anger"] + 4)
                clean_state["stress"] = _clamp(clean_state["stress"] + 2)
                message = "Питомец слишком устал для игры."
            else:
                clean_state["happiness"] = _clamp(clean_state["happiness"] + 22)
                clean_state["hunger"] = _clamp(clean_state["hunger"] - 9)
                clean_state["energy"] = _clamp(clean_state["energy"] - 12)
                clean_state["cleanliness"] = _clamp(clean_state["cleanliness"] - 6)
                clean_state["anger"] = _clamp(clean_state["anger"] - 18)
                clean_state["stress"] = _clamp(clean_state["stress"] - 12)
                clean_state["discipline"] = _clamp(clean_state["discipline"] + 2)
                clean_state["play_neglect"] = 0
                clean_state["weight"] = _adjust_weight(clean_state, -_care_weight_delta(clean_state, 0.012))
                message = "Питомец поиграл и стал счастливее."
        elif action == "clean":
            clean_state["cleanliness"] = 100
            clean_state["poops"] = 0
            clean_state["pees"] = 0
            clean_state["vomits"] = 0
            clean_state["health"] = _clamp(clean_state["health"] + 5)
            clean_state["stress"] = _clamp(clean_state["stress"] - 10)
            clean_state["anger"] = _clamp(clean_state["anger"] - 4)
            clean_state["dirty_neglect"] = 0
            message = "Домик чистый."
        elif action == "medicine":
            if clean_state.get("sick"):
                clean_state["sick"] = False
                clean_state["health"] = _clamp(clean_state["health"] + 28)
                clean_state["energy"] = _clamp(clean_state["energy"] - 4)
                clean_state["stress"] = _clamp(clean_state["stress"] - 8)
                clean_state["sick_neglect"] = 0
                message = "Лекарство помогло."
            else:
                clean_state["health"] = _clamp(clean_state["health"] + 2)
                clean_state["anger"] = _clamp(clean_state["anger"] + 2)
                message = "Питомец здоров."
        elif action == "sleep":
            clean_state["sleeping"] = not bool(clean_state.get("sleeping"))
            if clean_state["sleeping"]:
                clean_state["stress"] = _clamp(clean_state["stress"] - 4)
            else:
                clean_state["energy"] = _clamp(clean_state["energy"] + 2)
            message = "Питомец уснул." if clean_state["sleeping"] else "Питомец проснулся."
        else:
            message = "Неизвестное действие."

        clean_state["last_event"] = message
        return self.save_state(user_id, clean_state), message

    def _save_reset_state(self, user_id: str, old_pet_id: str, new_state: Dict[str, Any]) -> None:
        self.normalize_state(new_state)
        new_state["last_updated_at"] = _now_iso()
        user = self.user_store.get_user(user_id)
        progress = user.setdefault("progress", {})
        progress["tamagotchi"] = new_state
        _invalidate_best_alive_record(progress, old_pet_id)
        _sync_best_alive_record(progress, new_state)
        self.user_store.save_user(user)

    def advance_state(self, state: Dict[str, Any], minutes: int, *, offline: bool = False) -> None:
        self.normalize_state(state)
        clean_minutes = max(0, int(minutes or 0))
        if clean_minutes <= 0:
            return

        event = ""
        for _ in range(clean_minutes):
            if not state.get("alive", True):
                break

            previous_stage = str(state.get("stage") or "egg")
            state["age_minutes"] = int(state["age_minutes"]) + 1
            state["stage"] = _stage_for_age(int(state["age_minutes"]))
            if state["stage"] == "dead":
                state["alive"] = False
                state["sleeping"] = False
                event = "Питомец прожил свой век."
                break
            if state["stage"] != previous_stage:
                event = _stage_event(state["stage"])
            if state["stage"] != "egg" and not state.get("animal"):
                _assign_animal(state)
                event = f"Из яйца вылупился {animal_label(state.get('animal')).lower()}."
            _grow_weight_for_minute(state)

            if state.get("sleeping"):
                state["energy"] = _clamp(state["energy"] + 1.8)
                state["happiness"] = _clamp(state["happiness"] - 0.06)
                state["stress"] = _clamp(state["stress"] - 0.22)
            else:
                mood_penalty = 1.0 + (int(state["anger"]) / 130.0) + (int(state["stress"]) / 220.0)
                state["energy"] = _clamp(state["energy"] - (0.22 * mood_penalty))
                state["happiness"] = _clamp(state["happiness"] - (0.18 * mood_penalty))

            decay_multiplier = 1.0 + (int(state["anger"]) / 150.0) + (int(state["stress"]) / 220.0)
            state["hunger"] = _clamp(state["hunger"] - (0.32 * decay_multiplier))
            mess_factor = (
                int(state["poops"]) * 0.06
                + int(state["pees"]) * 0.08
                + int(state["vomits"]) * 0.14
            )
            state["cleanliness"] = _clamp(state["cleanliness"] - ((0.18 + mess_factor) * decay_multiplier))

            if state["hunger"] <= 10:
                state["hunger_neglect"] = int(state.get("hunger_neglect") or 0) + 1
                state["anger"] = _clamp(state["anger"] + 0.8)
                state["stress"] = _clamp(state["stress"] + 0.6)
            else:
                state["hunger_neglect"] = max(0, int(state.get("hunger_neglect") or 0) - 1)

            if state["happiness"] <= 18:
                state["play_neglect"] = int(state.get("play_neglect") or 0) + 1
                state["anger"] = _clamp(state["anger"] + 0.9)
                state["stress"] = _clamp(state["stress"] + 0.35)
                state["discipline"] = _clamp(state["discipline"] - 0.3)
            else:
                state["play_neglect"] = max(0, int(state.get("play_neglect") or 0) - 1)

            if state["cleanliness"] <= 25 or int(state["poops"]) + int(state["pees"]) + int(state["vomits"]) >= 3:
                state["dirty_neglect"] = int(state.get("dirty_neglect") or 0) + 1
                state["stress"] = _clamp(state["stress"] + 0.55)
            else:
                state["dirty_neglect"] = max(0, int(state.get("dirty_neglect") or 0) - 1)

            state["poop_meter"] = int(state.get("poop_meter") or 0) + 1
            if state["poop_meter"] >= POOP_INTERVAL_MINUTES:
                state["poop_meter"] = 0
                state["poops"] = min(5, int(state["poops"]) + 1)
                state["cleanliness"] = _clamp(state["cleanliness"] - 14)
                event = "Питомцу нужна уборка."

            state["pee_meter"] = int(state.get("pee_meter") or 0) + 1
            if state["pee_meter"] >= PEE_INTERVAL_MINUTES:
                state["pee_meter"] = 0
                state["pees"] = min(5, int(state["pees"]) + 1)
                state["cleanliness"] = _clamp(state["cleanliness"] - 10)
                event = "Питомец сделал лужу."

            state["vomit_meter"] = int(state.get("vomit_meter") or 0) + 1
            if state.get("sick") and state["vomit_meter"] >= VOMIT_INTERVAL_MINUTES:
                state["vomit_meter"] = 0
                if _RNG.random() < 0.45:
                    state["vomits"] = min(4, int(state["vomits"]) + 1)
                    state["cleanliness"] = _clamp(state["cleanliness"] - 18)
                    state["hunger"] = _clamp(state["hunger"] - 7)
                    state["health"] = _clamp(state["health"] - 5)
                    event = "Питомца вырвало из-за болезни."

            danger = 0.0
            if state["hunger"] <= 0:
                danger += 1.8 + min(2.2, int(state.get("hunger_neglect") or 0) / 22.0)
            if state["happiness"] <= 0:
                danger += 0.45 + min(1.0, int(state.get("play_neglect") or 0) / 60.0)
            if state["cleanliness"] < 20:
                danger += 0.55 + min(1.2, int(state.get("dirty_neglect") or 0) / 42.0)
            if int(state["poops"]) >= 3:
                danger += 0.4
            if int(state["pees"]) >= 3:
                danger += 0.35
            if int(state["vomits"]) >= 1:
                danger += 0.7
            if state.get("sick"):
                danger += 0.9 + min(1.8, int(state.get("sick_neglect") or 0) / 24.0)
                state["sick_neglect"] = int(state.get("sick_neglect") or 0) + 1
            else:
                state["sick_neglect"] = max(0, int(state.get("sick_neglect") or 0) - 1)

            if int(state["anger"]) >= 70:
                danger += 0.25
                if not state.get("sleeping"):
                    state["cleanliness"] = _clamp(state["cleanliness"] - 0.35)
                    state["energy"] = _clamp(state["energy"] - 0.3)
                event = "Питомец злится и быстрее выматывается."
            if int(state["stress"]) >= 75:
                danger += 0.35
                state["happiness"] = _clamp(state["happiness"] - 0.25)
                event = "Питомец нервничает."

            if danger > 0:
                state["health"] = _clamp(state["health"] - danger)
                state["care_misses"] = int(state.get("care_misses") or 0) + 1
            else:
                state["health"] = _clamp(state["health"] + 0.08)

            if not state.get("sick") and (
                state["cleanliness"] < 12
                or int(state["poops"]) >= 5
                or int(state["pees"]) >= 5
                or int(state["vomits"]) >= 2
            ):
                state["sick"] = True
                event = "Питомец заболел."

            if state["energy"] <= 4 and not state.get("sleeping"):
                event = "Питомец хочет спать."
            elif state["hunger"] <= 15:
                event = "Питомец проголодался."
            elif state["anger"] >= 70:
                event = "Питомец злится. С ним нужно поиграть."
            elif state["happiness"] <= 20:
                event = "Питомцу скучно."

            if state["health"] <= 0:
                state["alive"] = False
                state["sleeping"] = False
                state["stage"] = "dead"
                event = "Питомец больше не реагирует."

        if offline and not event:
            event = "Пока окно было закрыто, время прошло."
        state["last_event"] = event or _mood_text(state)
        state["last_updated_at"] = _now_iso()

    def normalize_state(self, state: Dict[str, Any]) -> None:
        now = _now_iso()
        for key, value in DEFAULT_TAMAGOTCHI_STATE.items():
            state.setdefault(key, deepcopy(value))
        state["schema_version"] = int(state.get("schema_version") or 1)
        pet_id = str(state.get("pet_id") or "").strip()
        if not pet_id:
            pet_id = _new_pet_id()
        state["pet_id"] = pet_id[:32]
        raw_name = str(state.get("name") or "").strip()
        if not raw_name or raw_name == "Тама":
            raw_name = _random_name()
        state["name"] = raw_name[:32]
        state["created_at"] = state.get("created_at") or now
        state["last_updated_at"] = state.get("last_updated_at") or now
        state["age_minutes"] = max(0, int(state.get("age_minutes") or 0))
        state["stage"] = "dead" if not bool(state.get("alive", True)) else _stage_for_age(state["age_minutes"])
        if state["stage"] == "dead":
            state["alive"] = False
            state["sleeping"] = False
        state["animal"] = _normalize_animal(state.get("animal"))
        if state["stage"] == "egg":
            state["animal"] = None
        elif not state["animal"]:
            _assign_animal(state)
        state["rarity"] = "rare" if state.get("animal") == "unicorn" else "normal"
        for key in ("hunger", "happiness", "cleanliness", "energy", "health", "anger", "stress", "discipline"):
            state[key] = _clamp(state.get(key, DEFAULT_TAMAGOTCHI_STATE[key]))
        state["weight"] = _normalize_weight_for_state(state, state.get("weight") or DEFAULT_TAMAGOTCHI_STATE["weight"])
        state["poops"] = max(0, min(5, int(state.get("poops") or 0)))
        state["pees"] = max(0, min(5, int(state.get("pees") or 0)))
        state["vomits"] = max(0, min(4, int(state.get("vomits") or 0)))
        state["poop_meter"] = max(0, min(POOP_INTERVAL_MINUTES - 1, int(state.get("poop_meter") or 0)))
        state["pee_meter"] = max(0, min(PEE_INTERVAL_MINUTES - 1, int(state.get("pee_meter") or 0)))
        state["vomit_meter"] = max(0, min(VOMIT_INTERVAL_MINUTES - 1, int(state.get("vomit_meter") or 0)))
        state["sick"] = bool(state.get("sick"))
        state["sleeping"] = bool(state.get("sleeping"))
        state["alive"] = bool(state.get("alive", True))
        state["care_misses"] = max(0, int(state.get("care_misses") or 0))
        state["hunger_neglect"] = max(0, int(state.get("hunger_neglect") or 0))
        state["dirty_neglect"] = max(0, int(state.get("dirty_neglect") or 0))
        state["play_neglect"] = max(0, int(state.get("play_neglect") or 0))
        state["sick_neglect"] = max(0, int(state.get("sick_neglect") or 0))
        state.pop("coins", None)
        state["last_event"] = str(state.get("last_event") or _mood_text(state))

    def get_tamagotchi_leaderboard(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for user in self.user_store.list_users(role=None):
            progress = user.get("progress") or {}
            state = progress.get("tamagotchi")
            if not isinstance(state, dict):
                continue
            clean_state = deepcopy(state)
            self.normalize_state(clean_state)
            elapsed_minutes = _elapsed_minutes_since(clean_state.get("last_updated_at"))
            if elapsed_minutes > 0:
                self.advance_state(clean_state, min(elapsed_minutes, MAX_OFFLINE_MINUTES), offline=True)
            record = _leaderboard_record_for_state(progress.get("tamagotchi_best_alive"), clean_state)
            if not record:
                continue
            entries.append(
                {
                    "user_id": user.get("user_id"),
                    "full_name": user.get("full_name") or "",
                    "role": user.get("role") or "",
                    "pet_name": record.get("name") or "",
                    "animal": record.get("animal"),
                    "stage": record.get("stage"),
                    "age_minutes": int(record.get("age_minutes") or 0),
                    "weight": float(record.get("weight") or 0),
                    "health": int(record.get("health") or 0),
                    "alive": True,
                    "rarity": record.get("rarity") or "normal",
                    "last_updated_at": record.get("last_updated_at"),
                }
            )
        entries.sort(
            key=lambda item: (
                -int(item["age_minutes"]),
                -float(item["weight"]),
                -STAGE_RANKS.get(str(item.get("stage") or ""), 0),
                str(item.get("full_name") or "").casefold(),
            )
        )
        return entries


def _sync_best_alive_record(progress: Dict[str, Any], state: Dict[str, Any]) -> None:
    if not isinstance(progress, dict):
        return
    pet_id = str(state.get("pet_id") or "")
    current_record = _record_from_alive_state(state)
    saved_record = _normalize_best_alive_record(progress.get("tamagotchi_best_alive"))

    if saved_record and str(saved_record.get("pet_id") or "") != pet_id:
        saved_record = None
        progress.pop("tamagotchi_best_alive", None)

    if not current_record:
        _invalidate_best_alive_record(progress, pet_id)
        return

    if not saved_record or _record_sort_key(current_record) > _record_sort_key(saved_record):
        progress["tamagotchi_best_alive"] = current_record


def _invalidate_best_alive_record(progress: Dict[str, Any], pet_id: str) -> None:
    if not isinstance(progress, dict):
        return
    saved_record = _normalize_best_alive_record(progress.get("tamagotchi_best_alive"))
    if not saved_record:
        progress.pop("tamagotchi_best_alive", None)
        return
    if not pet_id or str(saved_record.get("pet_id") or "") == str(pet_id):
        progress.pop("tamagotchi_best_alive", None)


def _leaderboard_record_for_state(record: Any, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not state.get("alive", True) or str(state.get("stage") or "") == "dead":
        return None
    pet_id = str(state.get("pet_id") or "")
    candidates: List[Dict[str, Any]] = []
    saved_record = _normalize_best_alive_record(record)
    if saved_record and str(saved_record.get("pet_id") or "") == pet_id:
        candidates.append(saved_record)
    current_record = _record_from_alive_state(state)
    if current_record:
        candidates.append(current_record)
    if not candidates:
        return None
    return deepcopy(max(candidates, key=_record_sort_key))


def _record_from_alive_state(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not state.get("alive", True) or str(state.get("stage") or "") == "dead":
        return None
    age_minutes = int(state.get("age_minutes") or 0)
    if age_minutes <= 0:
        return None
    return {
        "schema_version": 1,
        "pet_id": str(state.get("pet_id") or ""),
        "name": str(state.get("name") or ""),
        "animal": state.get("animal"),
        "stage": state.get("stage"),
        "age_minutes": age_minutes,
        "weight": float(state.get("weight") or 0),
        "health": int(state.get("health") or 0),
        "rarity": state.get("rarity") or "normal",
        "last_updated_at": state.get("last_updated_at") or _now_iso(),
    }


def _normalize_best_alive_record(record: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(record, dict):
        return None
    if record.get("alive") is False:
        return None
    pet_id = str(record.get("pet_id") or "").strip()
    if not pet_id:
        return None
    age_minutes = max(0, int(record.get("age_minutes") or 0))
    if age_minutes <= 0:
        return None
    animal = _normalize_animal(record.get("animal"))
    stage = str(record.get("stage") or "egg")
    if stage not in STAGE_RANKS or stage == "dead":
        return None
    try:
        weight = float(record.get("weight") or 0)
    except (TypeError, ValueError):
        weight = 0.0
    weight = _normalize_weight_for_state({"stage": stage, "animal": animal, "alive": True}, weight)
    try:
        health = int(record.get("health") or 0)
    except (TypeError, ValueError):
        health = 0
    return {
        "schema_version": 1,
        "pet_id": pet_id[:32],
        "name": str(record.get("name") or "")[:32],
        "animal": animal,
        "stage": stage,
        "age_minutes": age_minutes,
        "weight": weight,
        "health": max(0, min(100, health)),
        "rarity": "rare" if animal == "unicorn" else "normal",
        "last_updated_at": record.get("last_updated_at"),
    }


def _record_sort_key(record: Dict[str, Any]) -> Tuple[int, float, int]:
    return (
        int(record.get("age_minutes") or 0),
        float(record.get("weight") or 0),
        STAGE_RANKS.get(str(record.get("stage") or ""), 0),
    )


def new_tamagotchi_state() -> Dict[str, Any]:
    state = deepcopy(DEFAULT_TAMAGOTCHI_STATE)
    now = _now_iso()
    state["pet_id"] = _new_pet_id()
    state["name"] = _random_name()
    state["created_at"] = now
    state["last_updated_at"] = now
    return state


def stage_label(stage: str) -> str:
    return STAGE_LABELS.get(str(stage or ""), str(stage or ""))


def animal_label(animal: Optional[str]) -> str:
    if not animal:
        return "Не вылупился"
    return ANIMAL_LABELS.get(str(animal or ""), str(animal or ""))


def format_weight(weight: Any) -> str:
    try:
        kg = max(0.0, float(weight or 0))
    except (TypeError, ValueError):
        kg = 0.0
    if kg < 1:
        return f"{max(1, int(round(kg * 1000)))} г"
    if kg >= 1000:
        tonnes = kg / 1000
        text = f"{tonnes:.1f}" if tonnes < 10 else f"{tonnes:.0f}"
        return f"{text.rstrip('0').rstrip('.')} т"
    if kg < 10:
        text = f"{kg:.1f}".rstrip("0").rstrip(".")
        return f"{text} кг"
    return f"{int(round(kg))} кг"


def _random_name() -> str:
    return _RNG.choice(TAMAGOTCHI_NAMES)


def _new_pet_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _elapsed_minutes_since(value: Any) -> int:
    if not value:
        return 0
    try:
        previous = datetime.fromisoformat(str(value))
    except ValueError:
        return 0
    delta = datetime.now() - previous
    return max(0, int(delta.total_seconds() // 60))


def _stage_for_age(age_minutes: int) -> str:
    if age_minutes >= DEAD_MINUTES:
        return "dead"
    if age_minutes >= DEMENTIA_MINUTES:
        return "dementia"
    if age_minutes >= ELDER_MINUTES:
        return "elder"
    if age_minutes >= ADULT_MINUTES:
        return "adult"
    if age_minutes >= TEEN_MINUTES:
        return "teen"
    if age_minutes >= EGG_MINUTES:
        return "child"
    return "egg"


def _stage_age_bounds(stage: str) -> Tuple[int, int]:
    stage = str(stage or "egg")
    if stage == "child":
        return EGG_MINUTES, TEEN_MINUTES
    if stage == "teen":
        return TEEN_MINUTES, ADULT_MINUTES
    if stage == "adult":
        return ADULT_MINUTES, ELDER_MINUTES
    if stage == "elder":
        return ELDER_MINUTES, DEMENTIA_MINUTES
    if stage == "dementia":
        return DEMENTIA_MINUTES, DEAD_MINUTES
    if stage == "dead":
        return DEAD_MINUTES, DEAD_MINUTES
    return 0, EGG_MINUTES


def _weight_limits_for_state(state: Dict[str, Any]) -> Tuple[float, float]:
    stage = str(state.get("stage") or "egg")
    if stage == "egg":
        return EGG_WEIGHT_LIMITS_KG
    animal = _normalize_animal(state.get("animal")) or "dog"
    limits = ANIMAL_STAGE_WEIGHT_LIMITS_KG.get(animal, ANIMAL_STAGE_WEIGHT_LIMITS_KG["dog"])
    if stage == "dead":
        return 0.0, limits["adult"][1]
    return limits.get(stage, limits["child"])


def _target_weight_for_state(state: Dict[str, Any]) -> float:
    stage = str(state.get("stage") or "egg")
    low, high = _weight_limits_for_state(state)
    if stage == "dead":
        return max(low, min(high, float(state.get("weight") or 0)))

    start, end = _stage_age_bounds(stage)
    span = max(1, end - start)
    progress = max(0.0, min(1.0, (int(state.get("age_minutes") or 0) - start) / span))
    return round(low + ((high - low) * progress), 3)


def _normalize_weight_for_state(state: Dict[str, Any], value: Any) -> float:
    try:
        weight = float(value)
    except (TypeError, ValueError):
        weight = DEFAULT_TAMAGOTCHI_STATE["weight"]
    low, high = _weight_limits_for_state(state)
    return round(max(low, min(high, weight)), 3)


def _adjust_weight(state: Dict[str, Any], delta: float) -> float:
    return _normalize_weight_for_state(state, float(state.get("weight") or 0) + float(delta or 0))


def _care_weight_delta(state: Dict[str, Any], ratio: float) -> float:
    low, high = _weight_limits_for_state(state)
    span = max(0.001, high - low)
    return max(0.002, min(20.0, span * float(ratio or 0)))


def _growth_step_for_minute(state: Dict[str, Any]) -> float:
    low, high = _weight_limits_for_state(state)
    start, end = _stage_age_bounds(str(state.get("stage") or "egg"))
    span_minutes = max(1, end - start)
    return max(0.001, (high - low) / span_minutes * 1.25)


def _grow_weight_for_minute(state: Dict[str, Any]) -> None:
    if not state.get("alive", True) or str(state.get("stage") or "") == "dead":
        return
    current = _normalize_weight_for_state(state, state.get("weight") or DEFAULT_TAMAGOTCHI_STATE["weight"])
    target = _target_weight_for_state(state)
    stage = str(state.get("stage") or "egg")
    if current < target and float(state.get("hunger") or 0) > 20:
        current = min(target, current + max(_growth_step_for_minute(state), (target - current) * 0.2))
    elif current > target + 2 and (stage in {"elder", "dementia"} or float(state.get("hunger") or 0) < 35):
        current = max(target + 2, current - max(_growth_step_for_minute(state) * 0.5, 0.002))
    state["weight"] = _normalize_weight_for_state(state, current)


def _stage_event(stage: str) -> str:
    if stage == "teen":
        return "Питомец вырос в подростка."
    if stage == "adult":
        return "Питомец стал взрослым."
    if stage == "elder":
        return "Питомец стал пожилым."
    if stage == "dementia":
        return "Питомец стал совсем стареньким и забывчивым."
    if stage == "dead":
        return "Питомец прожил свой век."
    if stage == "child":
        return "Питомец вылупился."
    return "Питомец растёт."


def _assign_animal(state: Dict[str, Any]) -> None:
    animals = [item[0] for item in ANIMAL_WEIGHTS]
    weights = [item[1] for item in ANIMAL_WEIGHTS]
    state["animal"] = _RNG.choices(animals, weights=weights, k=1)[0]
    if state["animal"] == "unicorn":
        state["rarity"] = "rare"
        return
    state["rarity"] = "normal"


def _normalize_animal(value: Any) -> Optional[str]:
    animal = str(value or "").strip().lower()
    if animal in ANIMAL_LABELS:
        return animal
    return None


def _clamp(value: Any, minimum: int = 0, maximum: int = 100) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(minimum)
    return round(max(minimum, min(maximum, number)), 2)


def _mood_text(state: Dict[str, Any]) -> str:
    if not state.get("alive", True):
        return "Питомец больше не реагирует."
    if state.get("sick"):
        return "Питомцу нужно лекарство."
    if state.get("sleeping"):
        return "Питомец спит."
    if int(state.get("hunger") or 0) < 25:
        return "Питомец хочет есть."
    if int(state.get("happiness") or 0) < 25:
        return "Питомцу скучно."
    if int(state.get("cleanliness") or 0) < 30:
        return "Нужно прибраться."
    if int(state.get("energy") or 0) < 20:
        return "Питомец устал."
    return "Питомец в хорошем настроении."
