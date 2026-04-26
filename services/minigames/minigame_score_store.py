from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from rem_card.services.minigames.minigame_paths import PathLikeProvider
from rem_card.services.minigames.minigame_user_store import (
    MinigameUserStore,
    new_snake_progress,
)

ARCADE_GAME_LABELS = {
    "dodge": "Dodge",
    "tetris": "Тетрис",
    "minesweeper": "Сапёр",
    "game_2048": "2048",
}

DEFAULT_ARCADE_PROGRESS = {
    "games_played": 0,
    "last_score": 0,
    "last_result": "",
    "last_duration_sec": 0,
    "last_played_at": None,
    "last_extra": {},
    "best_score": 0,
    "best_result": "",
    "best_duration_sec": 0,
    "best_played_at": None,
    "best_extra": {},
}


class MinigameScoreStore:
    def __init__(
        self,
        data_root_provider: PathLikeProvider = None,
        user_store: Optional[MinigameUserStore] = None,
    ):
        self.user_store = user_store or MinigameUserStore(data_root_provider)

    def save_snake_result(
        self,
        user_id: str,
        *,
        score: int,
        length: int,
        duration_sec: int,
        won: bool = False,
    ) -> Dict[str, Any]:
        user = self.user_store.get_user(user_id)
        progress = user.setdefault("progress", {})
        snake = progress.setdefault("snake", new_snake_progress())

        clean_score = max(0, int(score or 0))
        clean_length = max(1, int(length or 1))
        clean_duration = max(0, int(duration_sec or 0))
        now = datetime.now().replace(microsecond=0).isoformat()

        previous_best_score = int(snake.get("best_score") or 0)
        previous_best_length = int(snake.get("best_length") or 1)
        previous_best_duration = int(snake.get("best_duration_sec") or 0)

        score_improved = clean_score > previous_best_score
        length_improved = clean_length > previous_best_length
        duration_improved = (
            clean_score == previous_best_score
            and clean_length == previous_best_length
            and clean_duration > 0
            and (previous_best_duration <= 0 or clean_duration < previous_best_duration)
        )

        snake["games_played"] = int(snake.get("games_played") or 0) + 1
        snake["last_score"] = clean_score
        snake["last_played_at"] = now
        snake["last_won"] = bool(won)

        if score_improved:
            snake["best_score"] = clean_score
        if length_improved:
            snake["best_length"] = clean_length
        if score_improved or length_improved or duration_improved:
            snake["best_duration_sec"] = clean_duration

        self.user_store.save_user(user)
        return user

    def save_arcade_result(
        self,
        user_id: str,
        game_key: str,
        *,
        score: int,
        result: str,
        duration_sec: float,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean_key = normalize_arcade_game_key(game_key)
        user = self.user_store.get_user(user_id)
        progress = user.setdefault("progress", {})
        game = progress.setdefault(clean_key, new_arcade_progress())
        for key, value in DEFAULT_ARCADE_PROGRESS.items():
            game.setdefault(key, deepcopy(value))

        clean_score = max(0, int(score or 0))
        clean_duration = max(0, int(float(duration_sec or 0)))
        clean_result = str(result or "").strip() or "game_over"
        clean_extra = dict(extra or {}) if isinstance(extra, dict) else {}
        now = datetime.now().replace(microsecond=0).isoformat()

        previous_best_score = int(game.get("best_score") or 0)
        previous_best_duration = int(game.get("best_duration_sec") or 0)
        previous_games_played = int(game.get("games_played") or 0)
        score_improved = clean_score > previous_best_score
        duration_improved = (
            clean_score == previous_best_score
            and clean_score > 0
            and clean_duration > 0
            and (previous_best_duration <= 0 or clean_duration < previous_best_duration)
        )

        game["games_played"] = previous_games_played + 1
        game["last_score"] = clean_score
        game["last_result"] = clean_result
        game["last_duration_sec"] = clean_duration
        game["last_played_at"] = now
        game["last_extra"] = clean_extra

        if previous_games_played <= 0 or score_improved or duration_improved:
            game["best_score"] = clean_score
            game["best_result"] = clean_result
            game["best_duration_sec"] = clean_duration
            game["best_played_at"] = now
            game["best_extra"] = clean_extra

        self.user_store.save_user(user)
        return user

    def get_snake_leaderboard(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for user in self.user_store.list_users(role=None):
            snake = (user.get("progress") or {}).get("snake") or {}
            entries.append(
                {
                    "user_id": user.get("user_id"),
                    "full_name": user.get("full_name") or "",
                    "role": user.get("role") or "",
                    "best_score": int(snake.get("best_score") or 0),
                    "best_length": int(snake.get("best_length") or 1),
                    "best_duration_sec": int(snake.get("best_duration_sec") or 0),
                    "games_played": int(snake.get("games_played") or 0),
                    "last_played_at": snake.get("last_played_at"),
                }
            )
        entries.sort(
            key=lambda item: (
                -item["best_score"],
                -item["best_length"],
                _duration_sort_value(item["best_duration_sec"]),
                str(item["full_name"]).casefold(),
            )
        )
        return entries

    def get_arcade_leaderboard(self, game_key: str) -> List[Dict[str, Any]]:
        clean_key = normalize_arcade_game_key(game_key)
        entries: List[Dict[str, Any]] = []
        for user in self.user_store.list_users(role=None):
            game = (user.get("progress") or {}).get(clean_key) or {}
            best_score = int(game.get("best_score") or 0)
            games_played = int(game.get("games_played") or 0)
            if games_played <= 0 and best_score <= 0:
                continue
            entries.append(
                {
                    "user_id": user.get("user_id"),
                    "full_name": user.get("full_name") or "",
                    "role": user.get("role") or "",
                    "best_score": best_score,
                    "best_result": game.get("best_result") or "",
                    "best_duration_sec": int(game.get("best_duration_sec") or 0),
                    "best_played_at": game.get("best_played_at"),
                    "best_extra": game.get("best_extra") if isinstance(game.get("best_extra"), dict) else {},
                    "games_played": games_played,
                    "last_score": int(game.get("last_score") or 0),
                    "last_played_at": game.get("last_played_at"),
                }
            )
        entries.sort(
            key=lambda item: (
                -item["best_score"],
                _duration_sort_value(item["best_duration_sec"]),
                str(item["full_name"]).casefold(),
            )
        )
        return entries


def _duration_sort_value(duration_sec: int) -> int:
    clean_duration = int(duration_sec or 0)
    return clean_duration if clean_duration > 0 else 10**9


def normalize_arcade_game_key(game_key: str) -> str:
    clean_key = str(game_key or "").strip().lower()
    if clean_key not in ARCADE_GAME_LABELS:
        raise ValueError("Неизвестная миниигра.")
    return clean_key


def new_arcade_progress() -> Dict[str, Any]:
    return deepcopy(DEFAULT_ARCADE_PROGRESS)
