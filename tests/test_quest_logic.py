"""Quest progression, statistics and title cleanup (quest_plan.py)."""
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quest_plan import EXPERIENCE_FOCUSES, TRACKS, clean_title, pillar_statistics, slot_plan


def done(slot, target, day="2026-11-10", feedback=None, category="Fitness", status="completed"):
    return {"slot": slot, "category": category, "status": status, "target": target, "difficulty": 1,
            "completed_at": day + "T10:00:00+00:00", "feedback": feedback}


# ---------- slot_plan: starting point ----------

def test_first_quest_uses_the_starting_level():
    plan = slot_plan("Fitness", 1, 2, [])
    assert plan["focus"] == "steps"
    assert plan["target"] == 4000
    assert plan["metric"] is True
    assert plan["difficulty"] == 2
    assert plan["source"] == "curated"
    assert "4,000" in plan["title"] or "4000" in plan["title"]


def test_starting_level_is_clamped_to_1_5():
    assert slot_plan("Languages", 1, 9, [])["target"] == TRACKS["Languages"][0][1][4]
    assert slot_plan("Languages", 1, 0, [])["target"] == TRACKS["Languages"][0][1][0]


def test_experience_quests_always_target_one_experience():
    for category, tracks in TRACKS.items():
        for slot, track in enumerate(tracks, 1):
            if track[0] in EXPERIENCE_FOCUSES:
                plan = slot_plan(category, slot, 3, [])
                assert plan["target"] == 1 and plan["metric"] is False


def test_every_pillar_has_five_valid_slots():
    for category, tracks in TRACKS.items():
        assert len(tracks) == 5
        for slot in range(1, 6):
            plan = slot_plan(category, slot, 1, [])
            assert plan["title"].strip()
            assert 1 <= plan["minutes"] <= 120


# ---------- slot_plan: progression after success / "too hard" ----------

def test_steps_increase_after_a_success():
    assert slot_plan("Fitness", 1, 2, [done(1, 4000)])["target"] == 6000


def test_steps_decrease_when_marked_too_hard():
    assert slot_plan("Fitness", 1, 2, [done(1, 4000, feedback="too_hard")])["target"] == 3000


def test_steps_stay_within_1000_and_12000():
    assert slot_plan("Fitness", 1, 5, [done(1, 12000)])["target"] == 12000
    assert slot_plan("Fitness", 1, 1, [done(1, 1000, feedback="too_hard")])["target"] == 1000


def test_other_metric_quests_grow_up_to_the_track_ceiling():
    assert slot_plan("Languages", 1, 1, [done(1, 5, category="Languages")])["target"] == 10
    assert slot_plan("Languages", 1, 1, [done(1, 25, category="Languages")])["target"] == 25


def test_too_hard_lowers_but_never_below_the_easiest_target():
    assert slot_plan("Languages", 1, 1, [done(1, 10, category="Languages", feedback="too_hard")])["target"] == 8
    assert slot_plan("Languages", 1, 1, [done(1, 5, category="Languages", feedback="too_hard")])["target"] == 5


def test_history_from_other_slots_and_pillars_is_ignored():
    history = [done(2, 50), done(1, 99999, category="Health")]
    assert slot_plan("Fitness", 1, 2, history)["target"] == 4000


def test_difficulty_rises_with_completions_but_caps_at_5():
    history = [done(1, 4000, day=f"2026-11-0{d}") for d in range(1, 9)]
    assert slot_plan("Fitness", 1, 2, history)["difficulty"] == 5


# ---------- pillar_statistics ----------

def test_statistics_count_week_previous_week_and_streak():
    today = date(2026, 11, 18)
    rows = [done(1, 1, "2026-11-18"), done(1, 1, "2026-11-17"), done(1, 1, "2026-11-16"),
            done(1, 1, "2026-11-08"), done(1, 1, "2026-11-18", status="active")]
    stats = pillar_statistics(rows, today)
    assert stats["completed"] == 4
    assert stats["week"] == 3
    assert stats["week_delta"] == 2
    assert stats["streak"] == 3


def test_streak_survives_until_the_end_of_today():
    stats = pillar_statistics([done(1, 1, "2026-11-17"), done(1, 1, "2026-11-16")], date(2026, 11, 18))
    assert stats["streak"] == 2


def test_streak_breaks_after_a_missed_day():
    assert pillar_statistics([done(1, 1, "2026-11-15")], date(2026, 11, 18))["streak"] == 0


def test_activity_covers_the_last_14_days_oldest_first():
    stats = pillar_statistics([done(1, 1, "2026-11-18"), done(2, 1, "2026-11-18")], date(2026, 11, 18))
    assert len(stats["activity"]) == 14
    assert stats["activity"][0]["Date"] == date(2026, 11, 5)
    assert stats["activity"][-1] == {"Date": date(2026, 11, 18), "Quests": 2}


def test_statistics_with_no_history():
    stats = pillar_statistics([], date(2026, 11, 18))
    assert (stats["completed"], stats["week"], stats["week_delta"], stats["streak"]) == (0, 0, 0, 0)
    assert all(day["Quests"] == 0 for day in stats["activity"])


# ---------- clean_title ----------

def test_clean_title_singular_and_plural():
    assert clean_title("Invite {n} friend(s)".format(n=1), 1) == "Invite 1 friend"
    assert clean_title("Invite {n} friend(s)".format(n=2), 2) == "Invite 2 friends"
    assert clean_title("Join 1 activity/activities", 1) == "Join 1 activity"
    assert clean_title("Track 1 payments", 1) == "Track 1 payment"


def test_clean_title_without_target_is_unchanged():
    assert clean_title("Read (s)", None) == "Read (s)"
