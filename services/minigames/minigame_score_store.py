from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from rem_card.services.minigames.minigame_paths import PathLikeProvider
from rem_card.services.minigames.minigame_user_store import (
    MinigameUserStore,
    new_snake_progress,
)


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


def _duration_sort_value(duration_sec: int) -> int:
    clean_duration = int(duration_sec or 0)
    return clean_duration if clean_duration > 0 else 10**9
