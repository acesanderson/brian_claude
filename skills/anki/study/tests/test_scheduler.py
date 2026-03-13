# tests/test_scheduler.py
import random
from datetime import datetime, timezone
from src.scheduler import schedule, apply_fuzz, CardUpdate

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _card(state="review", interval=10, ease=2500, reps=3, lapses=0, step_index=0):
    return dict(state=state, interval=interval, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=step_index, suspended=False)


# --- New card ---
def test_new_again_goes_to_step_0():
    u = schedule(_card(state="new", interval=0, reps=0), rating=1, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 0
    assert u.interval == 1  # first step: 1 minute

def test_new_hard_same_as_again():
    u = schedule(_card(state="new", interval=0, reps=0), rating=2, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 0
    assert u.interval == 1

def test_new_good_first_step_advances():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=0), rating=3, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 1
    assert u.interval == 10  # second step

def test_new_good_on_last_step_graduates():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=1), rating=3, now=NOW)
    assert u.state == "review"
    assert u.interval == 1  # GRADUATING_INTERVAL

def test_new_easy_graduates_with_easy_interval():
    u = schedule(_card(state="new", interval=0, reps=0), rating=4, now=NOW)
    assert u.state == "review"
    assert u.interval == 4  # EASY_GRADUATING_INTERVAL

# --- Learning card ---
def test_learning_hard_stays_at_same_step():
    u = schedule(_card(state="learning", interval=10, reps=0, step_index=1), rating=2, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 1
    assert u.interval == 10  # same step, not advanced

def test_learning_hard_different_from_new_hard():
    # Hard on new → step 0; Hard on learning → same step
    u_new = schedule(_card(state="new", reps=0, step_index=1), rating=2, now=NOW)
    u_learning = schedule(_card(state="learning", interval=10, reps=0, step_index=1), rating=2, now=NOW)
    assert u_new.step_index == 0
    assert u_learning.step_index == 1

# --- Review card ---
def test_review_good_interval_uses_ease():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=3, now=NOW)
    assert u.state == "review"
    # 10 * 2.5 = 25; fuzz range for 25: max(2, round(25*0.05))=2 → 23-27
    assert 23 <= u.interval <= 27

def test_review_good_interval_at_least_ivl_plus_one():
    # interval * ease could round down to same as current; must be >= interval+1
    u = schedule(_card(state="review", interval=1, ease=1300), rating=3, now=NOW)
    assert u.interval >= 2  # 1 * 1.3 = 1.3 → rounds to 1; clamped to min ivl+1 = 2

def test_review_again_sends_to_relearn():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=1, now=NOW)
    assert u.state == "relearning"
    assert u.ease_factor == 2300  # 2500 - 200
    assert u.lapses == 1
    assert u.step_index == 0

def test_review_hard_ease_penalty():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=2, now=NOW)
    assert u.ease_factor == 2350  # 2500 - 150
    assert u.state == "review"

def test_review_easy_ease_bonus():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=4, now=NOW)
    assert u.ease_factor == 2650  # 2500 + 150
    assert u.state == "review"

def test_ease_floor_respected():
    u = schedule(_card(state="review", interval=10, ease=1400), rating=1, now=NOW)
    assert u.ease_factor == 1300  # floor: 1400-200=1200 clamped to 1300

# --- Leech ---
def test_leech_suspends_at_threshold():
    u = schedule(_card(state="review", interval=10, lapses=7), rating=1, now=NOW)
    assert u.lapses == 8
    assert u.suspended is True

def test_not_suspended_below_threshold():
    u = schedule(_card(state="review", interval=10, lapses=6), rating=1, now=NOW)
    assert u.lapses == 7
    assert u.suspended is False

# --- Relearning ---
def test_relearning_good_graduates():
    # RELEARN_STEPS_MINUTES = [10], so step_index=0 is last step
    u = schedule(_card(state="relearning", interval=10, step_index=0), rating=3, now=NOW)
    assert u.state == "review"
    assert u.interval == 1  # MIN_REVIEW_INTERVAL

def test_relearning_hard_stays_at_step():
    u = schedule(_card(state="relearning", interval=10, step_index=0), rating=2, now=NOW)
    assert u.state == "relearning"
    assert u.step_index == 0

# --- Fuzz ---
def test_fuzz_small_interval():
    # interval=2: fuzz=1, so result in [1, 3]
    random.seed(42)
    results = {apply_fuzz(2) for _ in range(50)}
    assert results.issubset({1, 2, 3})

def test_fuzz_medium_interval():
    # interval=10: fuzz=max(1, round(10*0.1))=1, so result in [9, 11]
    random.seed(42)
    results = {apply_fuzz(10) for _ in range(50)}
    assert results.issubset({9, 10, 11})

def test_fuzz_large_interval():
    # interval=30: fuzz=max(2, round(30*0.05))=2, so result in [28, 32]
    random.seed(42)
    results = {apply_fuzz(30) for _ in range(50)}
    assert results.issubset(set(range(28, 33)))

def test_fuzz_does_not_apply_to_interval_0():
    assert apply_fuzz(0) == 0

def test_fuzz_does_not_apply_to_interval_1():
    assert apply_fuzz(1) == 1

# --- Due date ---
def test_learning_due_is_minutes():
    u = schedule(_card(state="new", interval=0, reps=0), rating=1, now=NOW)
    expected = NOW + __import__("datetime").timedelta(minutes=1)
    assert u.due == expected

def test_review_due_is_midnight_utc():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=1), rating=3, now=NOW)
    # NOW = 2026-01-01 12:00 UTC; graduating: due = midnight UTC + 1 day = 2026-01-02 00:00
    assert u.due.hour == 0
    assert u.due.minute == 0
    assert u.due.second == 0
