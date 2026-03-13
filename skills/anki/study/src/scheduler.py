from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DEFAULT_EASE = 2500
MIN_EASE = 1300
HARD_MULT = 1.2
EASY_BONUS = 1.3
EASE_AGAIN_PENALTY = -200
EASE_HARD_PENALTY = -150
EASE_EASY_BONUS = 150
NEW_STEPS_MINUTES = [1, 10]
RELEARN_STEPS_MINUTES = [10]
GRADUATING_INTERVAL_DAYS = 1
EASY_GRADUATING_INTERVAL_DAYS = 4
MIN_REVIEW_INTERVAL = 1
LEECH_THRESHOLD = 8


@dataclass
class CardUpdate:
    state: str
    due: datetime
    interval: int
    ease_factor: int
    reps: int
    lapses: int
    step_index: int
    suspended: bool


def apply_fuzz(interval: int) -> int:
    if interval < 2:
        return interval
    if interval == 2:
        fuzz = 1
    elif interval <= 20:
        fuzz = max(1, round(interval * 0.1))
    elif interval <= 100:
        fuzz = max(2, round(interval * 0.05))
    else:
        fuzz = max(4, round(interval * 0.05))
    return interval + random.randint(-fuzz, fuzz)


def _day_due(now: datetime, days: int) -> datetime:
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return day + timedelta(days=days)


def _minute_due(now: datetime, minutes: int) -> datetime:
    return now + timedelta(minutes=minutes)


def schedule(card: dict, rating: int, now: datetime | None = None) -> CardUpdate:
    if now is None:
        now = datetime.now(tz=timezone.utc)

    state = card["state"]
    if state in ("new", "learning"):
        return _schedule_learning(state, card, rating, now)
    elif state == "review":
        return _schedule_review(card, rating, now)
    elif state == "relearning":
        return _schedule_relearning(card, rating, now)
    else:
        raise ValueError(f"Unknown card state: {state!r}")


def _schedule_learning(state: str, card: dict, rating: int, now: datetime) -> CardUpdate:
    steps = NEW_STEPS_MINUTES
    step_index = card["step_index"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1 or (rating == 2 and state == "new"):
        # Again (any) or Hard on new → step 0
        return CardUpdate(
            state="learning", due=_minute_due(now, steps[0]),
            interval=steps[0], ease_factor=ease,
            reps=reps, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 2:
        # Hard on learning → same step (do not advance)
        current_ivl = steps[step_index]
        return CardUpdate(
            state="learning", due=_minute_due(now, current_ivl),
            interval=current_ivl, ease_factor=ease,
            reps=reps, lapses=lapses, step_index=step_index, suspended=False,
        )
    elif rating == 3:
        next_step = step_index + 1
        if next_step >= len(steps):
            ivl = GRADUATING_INTERVAL_DAYS
            return CardUpdate(
                state="review", due=_day_due(now, ivl),
                interval=ivl, ease_factor=ease,
                reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
            )
        else:
            new_ivl = steps[next_step]
            return CardUpdate(
                state="learning", due=_minute_due(now, new_ivl),
                interval=new_ivl, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=next_step, suspended=False,
            )
    else:  # Easy
        ivl = EASY_GRADUATING_INTERVAL_DAYS
        return CardUpdate(
            state="review", due=_day_due(now, ivl),
            interval=ivl, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )


def _schedule_review(card: dict, rating: int, now: datetime) -> CardUpdate:
    interval = card["interval"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1:
        new_ease = max(MIN_EASE, ease + EASE_AGAIN_PENALTY)
        new_lapses = lapses + 1
        suspended = new_lapses >= LEECH_THRESHOLD
        relearn_ivl = RELEARN_STEPS_MINUTES[0]
        return CardUpdate(
            state="relearning", due=_minute_due(now, relearn_ivl),
            interval=relearn_ivl, ease_factor=new_ease,
            reps=reps, lapses=new_lapses, step_index=0, suspended=suspended,
        )
    elif rating == 2:
        new_ease = max(MIN_EASE, ease + EASE_HARD_PENALTY)
        raw = max(interval + 1, round(interval * HARD_MULT))
        new_ivl = max(interval + 1, apply_fuzz(raw))
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=new_ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 3:
        raw = max(interval + 1, round(interval * (ease / 1000)))
        new_ivl = max(interval + 1, apply_fuzz(raw))
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
    else:  # Easy
        new_ease = ease + EASE_EASY_BONUS
        raw = max(interval + 1, round(interval * (ease / 1000) * EASY_BONUS))
        new_ivl = max(interval + 1, apply_fuzz(raw))
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=new_ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )


def _schedule_relearning(card: dict, rating: int, now: datetime) -> CardUpdate:
    steps = RELEARN_STEPS_MINUTES
    step_index = card["step_index"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1:
        return CardUpdate(
            state="relearning", due=_minute_due(now, steps[0]),
            interval=steps[0], ease_factor=ease,
            reps=reps, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 2:
        current_ivl = steps[step_index]
        return CardUpdate(
            state="relearning", due=_minute_due(now, current_ivl),
            interval=current_ivl, ease_factor=ease,
            reps=reps, lapses=lapses, step_index=step_index, suspended=False,
        )
    elif rating == 3:
        next_step = step_index + 1
        if next_step >= len(steps):
            return CardUpdate(
                state="review", due=_day_due(now, MIN_REVIEW_INTERVAL),
                interval=MIN_REVIEW_INTERVAL, ease_factor=ease,
                reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
            )
        else:
            new_ivl = steps[next_step]
            return CardUpdate(
                state="relearning", due=_minute_due(now, new_ivl),
                interval=new_ivl, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=next_step, suspended=False,
            )
    else:  # Easy
        return CardUpdate(
            state="review", due=_day_due(now, MIN_REVIEW_INTERVAL),
            interval=MIN_REVIEW_INTERVAL, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
