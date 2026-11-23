"""End-to-end workflows: the real app, driven like a user, against an in-memory Supabase.

Covers: sign-up + onboarding, login errors, completing quests (XP, replacement, adaptivity),
the weekly recap, squads (create, join, wrong code, shared confirmation), Settings
(quests per pillar, pillars and the free limit, city search, Pro) and logging out.
"""
from contextlib import nullcontext
import io
import json
from pathlib import Path
import urllib.request

import sys

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import places
from fake_supabase import ANON_KEY, URL, FakeSupabase
from onboarding import PILLARS

APP = str(Path(__file__).resolve().parents[1] / "app.py")
DONE_ONBOARDING = {"completed": True, "levels": {"Fitness": 2, "Languages": 1},
                   "quests_shown": {"Fitness": 5, "Languages": 5}}


@pytest.fixture
def backend(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setattr(urllib.request, "urlopen", fake.urlopen)   # app.py imports urlopen on every run
    monkeypatch.delenv("REQUESTY_API_KEY", raising=False)           # no AI: quests come from the habit library
    photon = {"features": [{"properties": {"name": "Lisbon", "country": "Portugal", "countrycode": "PT"}}]}
    monkeypatch.setattr(places, "urlopen", lambda *a, **k: nullcontext(io.BytesIO(json.dumps(photon).encode())))
    places._fetch_places.clear()
    return fake


def new_app(signup=False):
    at = AppTest.from_file(APP, default_timeout=60)
    at.secrets["supabase"] = {"url": URL, "anon_key": ANON_KEY}
    if signup:
        at.query_params["auth"] = "signup"
    return at.run()


def button(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f"No button {label!r}; buttons: {[b.label for b in at.button]}"
    return matches[0]


def field(at, label):
    return next(t for t in at.text_input if t.label == label)


def log_in(email, password="password123"):
    at = new_app()
    field(at, "Email").input(email)
    field(at, "Password").input(password)
    button(at, "Log in").click().run()
    assert not at.exception, at.exception
    return at


def ready_user(backend, email, name="Ana", categories=("Fitness", "Languages"), metadata=None):
    meta = {"lifequest_onboarding": DONE_ONBOARDING, **(metadata or {})}
    return backend.add_user(email, metadata=meta, profile={"display_name": name, "selected_categories": list(categories)})


def go(at, page):
    at.session_state.current_page=page
    at.run()
    assert not at.exception, at.exception
    return at


def quest_boxes(at):
    return [c for c in at.checkbox if c.key and c.key.startswith("quest_check_")]


def everything_text(at):
    return " ".join([m.value for m in at.markdown] + [c.value for c in at.caption] + [t.value for t in at.title])


# ---------- 1. sign up and onboarding ----------

def test_new_user_signs_up_and_finishes_onboarding(backend):
    at = new_app(signup=True)
    field(at, "Email").input("new@example.com")
    field(at, "Password").input("password123")
    field(at, "Confirm password").input("password123")
    button(at, "Create account").click().run()
    assert at.title[0].value == "First, what should we call you?"

    field(at, "Your nickname").input("Ana")
    button(at, "Let's begin →").click().run()
    button(at, "Make it mine →").click().run()

    at.checkbox(key="ob_pick_Fitness").check()
    at.checkbox(key="ob_pick_Languages").check().run()
    button(at, "Find my starting point →").click().run()
    for pillar in ("Fitness", "Languages"):
        at.radio(key="ob_level_" + pillar).set_value(PILLARS[pillar][3][1]).run()
        button(at, "Continue →").click().run()
    at.radio(key="ob_shown").set_value(3).run()
    button(at, "Continue →").click().run()
    assert at.title[0].value.startswith("Your next chapter is ready")
    at.selectbox(key="ob_preferences_target_language").set_value("ja").run()
    button(at, "Prepare my quests →").click().run()
    assert not at.exception, at.exception

    user = backend.users["new@example.com"]
    answers = user["user_metadata"]["lifequest_onboarding"]
    assert answers["levels"] == {"Fitness": 2, "Languages": 2}
    assert answers["quests_shown"] == {"Fitness": 3, "Languages": 3}
    assert backend.profiles[user["id"]]["selected_categories"] == ["Fitness", "Languages"]
    assert len([q for q in backend.quests if q["status"] == "active"]) == 10   # five ready per pillar
    assert len(quest_boxes(at)) == 6                                           # but only three shown each
    assert "Ana" in everything_text(at)


def test_every_account_can_pick_more_than_three_pillars(backend):
    at = new_app(signup=True)
    field(at, "Email").input("limit@example.com")
    field(at, "Password").input("password123")
    field(at, "Confirm password").input("password123")
    button(at, "Create account").click().run()
    field(at, "Your nickname").input("Bo")
    button(at, "Let's begin →").click().run()
    button(at, "Make it mine →").click().run()
    for pillar in ("Fitness", "Health", "Social"):
        at.checkbox(key="ob_pick_" + pillar).check().run()
    assert not at.checkbox(key="ob_pick_Finance").disabled
    assert not at.checkbox(key="ob_pick_Fitness").disabled
    assert not any("Pro unlocks" in c.value for c in at.caption)


def test_onboarding_requires_a_nickname(backend):
    at = new_app(signup=True)
    field(at, "Email").input("nameless@example.com")
    field(at, "Password").input("password123")
    field(at, "Confirm password").input("password123")
    button(at, "Create account").click().run()
    field(at, "Your nickname").input("   ")
    button(at, "Let's begin →").click().run()
    assert any("Add a nickname" in e.value for e in at.error)
    assert at.title[0].value == "First, what should we call you?"


# ---------- 2. login ----------

def test_wrong_password_is_rejected(backend):
    ready_user(backend, "ana@example.com")
    at = log_in("ana@example.com", "wrong-password")
    assert at.session_state.access_token is None
    assert at.error, "an error message should be shown"


def test_existing_user_lands_on_home_with_five_quests_per_pillar(backend):
    ready_user(backend, "ana@example.com")
    at = log_in("ana@example.com")
    assert at.session_state.access_token
    assert len(quest_boxes(at)) == 10
    assert "Ana" in everything_text(at)


# ---------- 3. completing quests ----------

def test_completing_a_quest_awards_xp_and_unlocks_the_next_one(backend):
    user = ready_user(backend, "ana@example.com", categories=("Fitness",))
    at = log_in("ana@example.com")
    steps = next(q for q in backend.quests if q["focus"] == "steps")
    at.checkbox(key="quest_check_" + steps["id"]).check().run()
    assert not at.exception, at.exception

    assert steps["status"] == "completed"
    assert backend.profiles[user["id"]]["points"] == 10 + 5 * steps["difficulty"]
    active = [q for q in backend.quests if q["status"] == "active"]
    assert len(active) == 5                                    # the slot was refilled
    nxt = next(q for q in active if q["slot"] == steps["slot"])
    assert nxt["target"] > steps["target"]                     # and the next one is harder
    assert any("up from" in m.value for m in at.markdown)      # which the user can see


def test_quests_shown_setting_limits_home(backend):
    ready_user(backend, "ana@example.com", metadata={"lifequest_onboarding": {**DONE_ONBOARDING,
                                                                                "quests_shown": {"Fitness": 1, "Languages": 2}}})
    at = log_in("ana@example.com")
    assert len(quest_boxes(at)) == 3
    assert len([q for q in backend.quests if q["status"] == "active"]) == 10


def test_weekly_recap_counts_completed_quests(backend):
    ready_user(backend, "ana@example.com", categories=("Fitness",))
    at = log_in("ana@example.com")
    first = quest_boxes(at)[0]
    first.check().run()
    go(at, "📊 Recap")
    assert at.title[0].value == "Your week"
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Quests completed"] == "1"
    assert metrics["Active days"] == "1/7"


def test_recap_with_no_activity_shows_an_empty_state(backend):
    ready_user(backend, "ana@example.com", categories=("Fitness",))
    at = go(log_in("ana@example.com"), "📊 Recap")
    assert any("No quests completed this week yet" in i.value for i in at.info)


# ---------- 4. squads ----------

def test_squad_create_join_and_confirm_together(backend):
    ana = ready_user(backend, "ana@example.com", "Ana")
    bo = ready_user(backend, "bo@example.com", "Bo")

    at_ana = go(log_in("ana@example.com"), "👥 Squad")
    field(at_ana, "Squad name").input("Sunday Hikers")
    button(at_ana, "Start a squad").click().run()
    assert not at_ana.exception, at_ana.exception
    squad = backend.squads[0]
    assert squad["name"] == "Sunday Hikers" and squad["members"] == [ana["id"]]

    at_bo = go(log_in("bo@example.com"), "👥 Squad")
    field(at_bo, "Squad invite code").input(squad["invite_code"].lower())   # codes are case-insensitive
    button(at_bo, "Join my friends").click().run()
    assert bo["id"] in squad["members"]

    quest = backend.squad_quests[0]
    at_bo.checkbox(key="team_check_" + quest["id"]).check().run()
    assert quest["confirmed"] == [bo["id"]]
    assert backend.profiles[bo["id"]]["points"] == 0                     # one confirmation is not enough

    at_ana = go(log_in("ana@example.com"), "👥 Squad")
    at_ana.checkbox(key="team_check_" + quest["id"]).check().run()
    assert backend.profiles[ana["id"]]["points"] == 30
    assert backend.profiles[bo["id"]]["points"] == 30
    assert "This week in your squad" in everything_text(at_ana)


def test_joining_with_a_wrong_code_shows_an_error(backend):
    ready_user(backend, "ana@example.com")
    at = go(log_in("ana@example.com"), "👥 Squad")
    field(at, "Squad invite code").input("NOPE99")
    button(at, "Join my friends").click().run()
    assert any("not valid" in e.value for e in at.error)
    assert backend.squads == []


def test_squad_name_must_be_long_enough(backend):
    ready_user(backend, "ana@example.com")
    at = go(log_in("ana@example.com"), "👥 Squad")
    field(at, "Squad name").input("A")
    button(at, "Start a squad").click().run()
    assert any("at least two characters" in e.value for e in at.error)
    assert backend.squads == []


# ---------- 5. settings ----------

def test_changing_quests_per_pillar_is_saved_and_applied(backend):
    user = ready_user(backend, "ana@example.com")
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    at.button_group(key="shown_Fitness").set_value(2).run()
    assert user["user_metadata"]["lifequest_onboarding"]["quests_shown"]["Fitness"] == 2
    at = go(at, "🏠 Home")
    assert len(quest_boxes(at)) == 2 + 5


def test_adding_a_pillar_creates_its_quests(backend):
    user = ready_user(backend, "ana@example.com", categories=("Fitness",))
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    at.multiselect(key="pillars_setting").select("Health").run()
    button(at, "Save pillars").click().run()
    assert backend.profiles[user["id"]]["selected_categories"] == ["Fitness", "Health"]
    go(at, "🏠 Home")
    assert len([q for q in backend.quests if q["category"] == "Health" and q["status"] == "active"]) == 5


def test_every_account_can_choose_all_seven_pillars(backend):
    ready_user(backend, "ana@example.com", categories=("Fitness", "Health", "Social"))
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    assert at.multiselect(key="pillars_setting").proto.max_selections == 7


def test_old_subscription_metadata_does_not_render_subscription_ui(backend):
    ready_user(backend, "ana@example.com", metadata={"lifequest_pro": {"active": True, "plan": "yearly", "since": "2026-11-18"}})
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    assert at.multiselect(key="pillars_setting").proto.max_selections == 7
    assert not any('Subscribe to Pro' in b.label for b in at.button)   # the "You're on Pro" card


def test_city_search_saves_the_chosen_city_once(backend):
    user = ready_user(backend, "ana@example.com")
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    field(at, "Your city").input("Lisb").run()
    at.radio(key="settings_city_choice").set_value("Lisbon, Portugal").run()
    assert backend.profiles[user["id"]]["location"] == "Lisbon, Portugal"
    patches = [c for c in backend.calls if c == ("PATCH", "/rest/v1/profiles")]
    at.run()
    at.run()
    assert [c for c in backend.calls if c == ("PATCH", "/rest/v1/profiles")] == patches   # no save loop


def test_log_out_returns_to_the_login_screen(backend):
    ready_user(backend, "ana@example.com")
    at = go(log_in("ana@example.com"), "⚙️ Settings")
    token = at.session_state.access_token
    button(at, "Log out").click().run()
    assert at.title[0].value == "Welcome back"
    assert token not in backend.tokens                  # the session was revoked on the server too


def test_markdown_in_a_squad_mates_name_is_shown_as_plain_text(backend):
    ready_user(backend, "ana@example.com", "Ana")
    ready_user(backend, "eve@example.com", "![x](https://evil.example/p.png)")
    at = go(log_in("eve@example.com"), "👥 Squad")
    field(at, "Squad name").input("[Click me](https://evil.example)")
    button(at, "Start a squad").click().run()
    at_ana = go(log_in("ana@example.com"), "👥 Squad")
    field(at_ana, "Squad invite code").input(backend.squads[0]["invite_code"])
    button(at_ana, "Join my friends").click().run()
    shown = [h.value for h in at_ana.subheader]
    assert "\\[Click me\\]\\(https://evil\\.example\\)" in shown        # escaped, so not a link
