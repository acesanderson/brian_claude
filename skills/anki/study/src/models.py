from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Deck:
    id: int
    name: str
    created_at: datetime


@dataclass
class Card:
    id: int
    deck_id: int
    front: str
    back: str
    tags: list[str]
    created_at: datetime
    state: str        # new | learning | review | relearning
    due: datetime
    interval: int     # MINUTES when state in (learning, relearning); DAYS otherwise
    ease_factor: int  # stored * 1000: 2500 = 2.5
    reps: int
    lapses: int
    step_index: int
    suspended: bool
    reference: str | None = None  # human-supplied citation; None for legacy cards


@dataclass(frozen=True)
class ReviewLog:
    id: int
    card_id: int
    reviewed_at: datetime
    rating: int
    prior_state: str
    prior_interval: int
    prior_ease_factor: int
    new_interval: int
    new_ease_factor: int


@dataclass
class SessionStats:
    reviewed: int = 0
    again: int = 0
    hard: int = 0
    good: int = 0
    easy: int = 0

    def record(self, rating: int) -> None:
        self.reviewed += 1
        if rating == 1:
            self.again += 1
        elif rating == 2:
            self.hard += 1
        elif rating == 3:
            self.good += 1
        elif rating == 4:
            self.easy += 1

    def unrecord(self, rating: int) -> None:
        """Reverse a record() call. Used by undo."""
        self.reviewed = max(0, self.reviewed - 1)
        if rating == 1:
            self.again = max(0, self.again - 1)
        elif rating == 2:
            self.hard = max(0, self.hard - 1)
        elif rating == 3:
            self.good = max(0, self.good - 1)
        elif rating == 4:
            self.easy = max(0, self.easy - 1)
