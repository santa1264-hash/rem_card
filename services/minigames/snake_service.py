from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


Point = Tuple[int, int]


@dataclass(frozen=True)
class SnakeStepResult:
    finished: bool
    won: bool


class SnakeGame:
    def __init__(self, width: int = 40, height: int = 40):
        self.width = int(width)
        self.height = int(height)
        self._rng = random.Random()
        self.reset()

    def reset(self) -> None:
        center = (self.width // 2, self.height // 2)
        self.snake: List[Point] = [center]
        self.direction: Point = (1, 0)
        self.pending_direction: Point = self.direction
        self.food: Optional[Point] = None
        self.score = 0
        self.alive = True
        self.won = False
        self.started_at = time.monotonic()
        self._place_food()

    @property
    def length(self) -> int:
        return len(self.snake)

    def elapsed_sec(self) -> int:
        return max(0, int(time.monotonic() - self.started_at))

    def set_direction(self, dx: int, dy: int) -> None:
        requested = (int(dx), int(dy))
        if requested == (0, 0):
            return
        current = self.direction
        if self.length > 1 and requested == (-current[0], -current[1]):
            return
        self.pending_direction = requested

    def step(self) -> SnakeStepResult:
        if not self.alive or self.won:
            return SnakeStepResult(finished=True, won=self.won)

        self.direction = self.pending_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if not self._inside(new_head):
            self.alive = False
            return SnakeStepResult(finished=True, won=False)

        eating = new_head == self.food
        collision_body = self.snake if eating else self.snake[:-1]
        if new_head in collision_body:
            self.alive = False
            return SnakeStepResult(finished=True, won=False)

        self.snake.insert(0, new_head)
        if eating:
            self.score += 1
            if self.length >= self.width * self.height:
                self.won = True
                self.food = None
                return SnakeStepResult(finished=True, won=True)
            self._place_food()
        else:
            self.snake.pop()

        return SnakeStepResult(finished=False, won=False)

    def result(self) -> dict:
        return {
            "score": self.score,
            "length": self.length,
            "duration_sec": self.elapsed_sec(),
            "won": self.won,
        }

    def _inside(self, point: Point) -> bool:
        x, y = point
        return 0 <= x < self.width and 0 <= y < self.height

    def _place_food(self) -> None:
        occupied = set(self.snake)
        free = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in occupied
        ]
        self.food = self._rng.choice(free) if free else None
