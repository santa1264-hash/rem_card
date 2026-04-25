from __future__ import annotations

import json
import os
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from rem_card.services.minigames.minigame_paths import (
    PathLikeProvider,
    ensure_minigame_dirs,
)


VALID_ROLES = {"doctor", "nurse"}

DEFAULT_SNAKE_PROGRESS = {
    "best_score": 0,
    "best_length": 1,
    "best_duration_sec": 0,
    "games_played": 0,
    "last_score": 0,
    "last_played_at": None,
}


def normalize_role(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if normalized not in VALID_ROLES:
        raise ValueError("Должность должна быть doctor или nurse.")
    return normalized


def new_snake_progress() -> Dict[str, Any]:
    return deepcopy(DEFAULT_SNAKE_PROGRESS)


def new_progress() -> Dict[str, Any]:
    return {"snake": new_snake_progress()}


class MinigameUserStore:
    def __init__(self, data_root_provider: PathLikeProvider = None):
        self._data_root_provider = data_root_provider

    def users_dir(self) -> str:
        return ensure_minigame_dirs(self._data_root_provider)

    def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        expected_role = normalize_role(role) if role else None
        users: List[Dict[str, Any]] = []
        users_dir = self.users_dir()
        for path in self._iter_user_files(users_dir):
            payload = self._read_user_file(path)
            if not payload:
                continue
            if expected_role and payload.get("role") != expected_role:
                continue
            users.append(payload)
        users.sort(
            key=lambda item: (
                str(item.get("full_name") or "").casefold(),
                str(item.get("created_at") or ""),
                str(item.get("user_id") or ""),
            )
        )
        return users

    def create_user(self, full_name: str, role: str) -> Dict[str, Any]:
        name = " ".join(str(full_name or "").split())
        if not name:
            raise ValueError("Введите ФИО.")
        normalized_role = normalize_role(role)
        now = _now_iso()
        user_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        payload = {
            "schema_version": 1,
            "user_id": user_id,
            "full_name": name,
            "role": normalized_role,
            "created_at": now,
            "updated_at": now,
            "progress": new_progress(),
        }
        self.save_user(payload)
        return payload

    def get_user(self, user_id: str) -> Dict[str, Any]:
        path = self._user_path(user_id)
        payload = self._read_user_file(path)
        if not payload:
            raise FileNotFoundError(f"Пользователь миниигр не найден: {user_id}")
        return payload

    def save_user(self, payload: Dict[str, Any]) -> None:
        self._normalize_payload(payload)
        payload["updated_at"] = _now_iso()
        path = self._user_path(str(payload["user_id"]))
        self._atomic_write_json(path, payload)

    def _iter_user_files(self, users_dir: str) -> Iterable[str]:
        try:
            names = os.listdir(users_dir)
        except FileNotFoundError:
            return []
        paths = [
            os.path.join(users_dir, name)
            for name in names
            if name.lower().endswith(".json") and os.path.isfile(os.path.join(users_dir, name))
        ]
        return sorted(paths)

    def _user_path(self, user_id: str) -> str:
        safe_id = _safe_user_id(user_id)
        return os.path.join(self.users_dir(), f"user_{safe_id}.json")

    def _read_user_file(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if not isinstance(payload, dict):
            return None
        try:
            self._normalize_payload(payload, for_read=True)
        except ValueError:
            return None
        return payload

    def _normalize_payload(self, payload: Dict[str, Any], *, for_read: bool = False) -> None:
        if not isinstance(payload, dict):
            raise ValueError("Некорректный JSON пользователя.")
        user_id = str(payload.get("user_id") or "").strip()
        if not user_id:
            raise ValueError("Не задан user_id.")
        payload["user_id"] = _safe_user_id(user_id)
        payload["schema_version"] = int(payload.get("schema_version") or 1)
        payload["full_name"] = " ".join(str(payload.get("full_name") or "").split())
        if not payload["full_name"]:
            raise ValueError("Не задано ФИО.")
        payload["role"] = normalize_role(str(payload.get("role") or ""))
        payload.setdefault("created_at", _now_iso())
        payload.setdefault("updated_at", payload["created_at"])
        progress = payload.get("progress")
        if not isinstance(progress, dict):
            progress = {}
            payload["progress"] = progress
        snake = progress.get("snake")
        if not isinstance(snake, dict):
            snake = {}
            progress["snake"] = snake
        for key, default_value in DEFAULT_SNAKE_PROGRESS.items():
            snake.setdefault(key, deepcopy(default_value))
        if not for_read:
            _coerce_snake_numbers(snake)

    def _atomic_write_json(self, path: str, payload: Dict[str, Any]) -> None:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        base_name = os.path.basename(path)
        fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, path)
            tmp_path = ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _safe_user_id(user_id: str) -> str:
    safe = "".join(ch for ch in str(user_id or "").strip() if ch.isalnum() or ch in "_-")
    if not safe:
        raise ValueError("Некорректный user_id.")
    return safe


def _coerce_snake_numbers(snake: Dict[str, Any]) -> None:
    for key in ("best_score", "best_length", "best_duration_sec", "games_played", "last_score"):
        try:
            snake[key] = int(snake.get(key) or 0)
        except (TypeError, ValueError):
            snake[key] = int(DEFAULT_SNAKE_PROGRESS[key] or 0)
    if snake["best_length"] < 1:
        snake["best_length"] = 1
