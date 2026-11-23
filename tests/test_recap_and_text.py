"""Weekly recap, CSV export, adaptivity hint and translation completeness."""
import csv
from datetime import date
import io
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import account
import onboarding_text
from onboarding import PILLARS, QUESTS_SHOWN
from quest_plan import completed_csv, progress_hint, quest_xp, weekly_recap

TODAY = date(2026, 11, 18)  # a Wednesday; the week started on Monday 16 November


def quest(day, category="Fitness", status="completed", difficulty=1, **extra):
    return {"status": status, "category": category, "difficulty": difficulty, "title": "Walk",
            "completed_at": f"{day}T09:00:00+00:00" if day else None, **extra}


# ---------- adaptivity hint ----------

def test_hint_shows_when_the_target_went_up():
    rows = [quest("2026-11-17", slot=1, target=4000, id="old")]
    assert progress_hint({"id": "new", "category": "Fitness", "slot": 1, "target": 6000, "focus": "steps"}, rows) == ("up", 4000)


def test_hint_shows_when_the_target_was_eased():
    rows = [quest("2026-11-17", slot=1, target=6000, id="old")]
    assert progress_hint({"id": "new", "category": "Fitness", "slot": 1, "target": 5000, "focus": "steps"}, rows) == ("down", 6000)


def test_hint_uses_the_most_recent_completion():
    rows = [quest("2026-11-10", slot=1, target=2000, id="a"), quest("2026-11-17", slot=1, target=4000, id="b")]
    assert progress_hint({"id": "c", "category": "Fitness", "slot": 1, "target": 6000}, rows) == ("up", 4000)


@pytest.mark.parametrize("current,rows", [
    ({"id": "n", "category": "Fitness", "slot": 1, "target": 4000}, []),                                       # first time
    ({"id": "n", "category": "Fitness", "slot": 1, "target": 4000}, [quest("2026-11-17", slot=1, target=4000)]),  # unchanged
    ({"id": "n", "category": "Fitness", "slot": 1, "target": 4000}, [quest("2026-11-17", slot=2, target=10)]),    # other slot
    ({"id": "n", "category": "Fitness", "slot": 1, "target": 4000}, [quest("2026-11-17", "Health", slot=1, target=5)]),  # other pillar
    ({"id": "n", "category": "Fitness", "slot": 1, "target": 4000}, [quest(None, status="active", slot=1, target=1)]),   # not completed
    ({"id": "n", "category": "Fitness", "slot": 2, "target": 1, "focus": "new_sport"}, [quest("2026-11-17", slot=2, target=5)]),  # experience
    ({"id": "n", "category": "Fitness", "slot": 1, "target": None}, [quest("2026-11-17", slot=1, target=4000)]),  # no target
])
def test_no_hint_when_nothing_meaningful_changed(current, rows):
    assert progress_hint(current, rows) is None


# ---------- weekly recap ----------

def test_recap_counts_only_this_week_from_monday():
    rows = [quest("2026-11-16"), quest("2026-11-18", "Health"), quest("2026-11-18", "Health"),
            quest("2026-11-15"),                       # Sunday: last week
            quest("2026-11-09"), quest("2026-11-10"),  # last week
            quest("2026-11-18", status="active")]      # not completed
    recap = weekly_recap(rows, TODAY)
    assert recap["week_start"] == date(2026, 11, 16)
    assert recap["completed"] == 3
    assert recap["previous_completed"] == 3
    assert recap["delta"] == 0
    assert recap["active_days"] == 2
    assert recap["per_pillar"] == {"Health": 2, "Fitness": 1}
    assert recap["best_day"] == (date(2026, 11, 18), 2)


def test_recap_xp_uses_points_or_difficulty():
    rows = [quest("2026-11-17", difficulty=3), {"status": "completed", "category": "Social", "points": 30,
                                                  "completed_at": "2026-11-17T12:00:00Z"}]
    assert weekly_recap(rows, TODAY)["xp"] == (10 + 5 * 3) + 30
    assert quest_xp({"difficulty": None}) == 15


def test_empty_recap():
    recap = weekly_recap([], TODAY)
    assert (recap["completed"], recap["xp"], recap["active_days"], recap["best_day"]) == (0, 0, 0, None)


# ---------- CSV export ----------

def read_csv(text):
    return list(csv.reader(io.StringIO(text)))


def test_csv_has_a_header_and_newest_first():
    rows = [quest("2026-11-10", title="Old one"), quest("2026-11-17", "Health", title="New one", feedback="too_hard"),
            quest(None, status="active", title="Not done")]
    table = read_csv(completed_csv(rows))
    assert table[0] == ["completed_on", "pillar", "quest", "xp", "feedback"]
    assert [r[2] for r in table[1:]] == ["New one", "Old one"]
    assert table[1] == ["2026-11-17", "Health", "New one", "15", "too_hard"]


def test_csv_cleans_titles():
    table = read_csv(completed_csv([quest("2026-11-17", title="Invite 1 friend(s)", target=1)]))
    assert table[1][2] == "Invite 1 friend"


@pytest.mark.parametrize("title", ["=HYPERLINK(\"http://evil\")", "+1+2", "-2+3", "@SUM(A1)"])
def test_csv_neutralises_spreadsheet_formulas(title):
    cell = read_csv(completed_csv([quest("2026-11-17", title=title)]))[1][2]
    assert cell.startswith("'") and cell[1:] == title


def test_csv_with_no_quests_is_just_the_header():
    assert read_csv(completed_csv([])) == [["completed_on", "pillar", "quest", "xp", "feedback"]]


# ---------- translations are complete ----------

LANGS = ["pt", "fr", "de"]


@pytest.mark.parametrize("lang", LANGS)
def test_onboarding_ui_is_fully_translated(lang):
    assert set(onboarding_text.UI[lang]) == set(onboarding_text.UI["en"])
    for n in QUESTS_SHOWN:
        assert f"shown_{n}" in onboarding_text.UI[lang]


@pytest.mark.parametrize("lang", LANGS)
def test_every_pillar_is_translated_with_five_levels(lang):
    assert set(onboarding_text.PILLAR_TEXT[lang]) == set(PILLARS)
    for pillar, (name, tagline, description, levels) in onboarding_text.PILLAR_TEXT[lang].items():
        assert name and tagline and description
        assert len(levels) == len(PILLARS[pillar][3]) == 5


@pytest.mark.parametrize("module", [account])
def test_settings_texts_have_the_same_keys_in_every_language(module):
    english = set(module.TEXT["en"])
    for lang in LANGS:
        assert set(module.TEXT[lang]) == english


@pytest.mark.parametrize("key", ["step", "hi_title", "pillars_limit", "final_level", "final_per"])
def test_placeholders_match_across_languages(key):
    import string
    def fields(text):
        return {f for _, f, _, _ in string.Formatter().parse(text) if f}
    for lang in LANGS:
        assert fields(onboarding_text.UI[lang][key]) == fields(onboarding_text.UI["en"][key])
