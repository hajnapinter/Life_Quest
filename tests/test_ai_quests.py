"""AI answers are checked before use, and failures fall back safely (ai_quests.py)."""
from pathlib import Path
from urllib.error import HTTPError, URLError
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ai_quests
from ai_quests import QuestGenerationError, generate_slot_quests, validate_batch, zero_cost_model
from quest_plan import slot_plan

PLANS = [slot_plan("Fitness", 1, 1, []), slot_plan("Fitness", 2, 1, [])]  # steps (2,000) + new sport (experience)


def good():
    return {"quests": [
        {"slot": 1, "title": "Walk 2,000 steps today", "description": "Spread them through the day.", "minutes": 20},
        {"slot": 2, "title": "Try a beginner pilates class", "description": "Pick a free online class.", "minutes": 25},
    ]}


def with_change(index, **fields):
    data = good()
    data["quests"][index].update(fields)
    return data


# ---------- accepted ----------

def test_valid_batch_is_accepted_and_marked_as_ai():
    output = validate_batch(good(), PLANS)
    assert [q["slot"] for q in output] == [1, 2]
    assert all(q["source"] == "ai" and q["category"] == "Fitness" for q in output)


def test_fields_echoed_by_the_model_are_ignored():
    output = validate_batch(with_change(0, category="Hacked", target=999, difficulty=5), PLANS)
    assert output[0]["category"] == "Fitness"
    assert output[0]["target"] == 2000


# ---------- rejected ----------

@pytest.mark.parametrize("result", [
    None,
    {"quests": "not a list"},
    {"quests": good()["quests"][:1]},                                   # too few
    {"quests": good()["quests"] + good()["quests"][:1]},                # too many
])
def test_wrong_shape_or_count_is_rejected(result):
    with pytest.raises(ValueError):
        validate_batch(result, PLANS)


@pytest.mark.parametrize("index,fields", [
    (1, {"slot": 1}),                       # duplicate slot
    (1, {"slot": 9}),                       # unexpected slot
    (0, {"slot": "1"}),                     # slot must be an integer
    (0, {"title": "x" * 91}),               # title too long
    (0, {"title": "   "}),                  # empty title
    (0, {"description": ""}),               # empty description
    (0, {"description": "y" * 241}),        # description too long
    (0, {"minutes": 0}),                    # below 1 minute
    (0, {"minutes": 121}),                  # above 2 hours
    (0, {"minutes": True}),                 # booleans are not numbers here
    (0, {"title": "Walk 3,000 steps today"}),               # model changed the server's target
    (1, {"title": "Try a new sport for 15 minutes"}),       # experience quests must not add timers
    (1, {"title": "walk 2,000 steps TODAY"}),               # duplicate title (case-insensitive)
])
def test_invalid_quests_are_rejected(index, fields):
    with pytest.raises(ValueError):
        validate_batch(with_change(index, **fields), PLANS)


def test_missing_field_is_rejected():
    data = good()
    del data["quests"][0]["minutes"]
    with pytest.raises(ValueError):
        validate_batch(data, PLANS)


# ---------- only free models are used ----------

@pytest.mark.parametrize("metadata,free", [
    ({"input_price": 0, "output_price": "0"}, True),
    ({"pricing": [{"input_price": 0, "output_price": 0}, {"input_price": "0.0", "output_price": 0}]}, True),
    ({"input_price": 0}, False),                                           # missing price is not "free"
    ({"input_price": 0, "output_price": 0.000001}, False),
    ({"input_price": 0, "output_price": 0, "cache_write_price": 0.1}, False),  # any extra billable item
    ({"input_price": False, "output_price": 0}, False),                    # booleans are not prices
    ({"input_price": "free", "output_price": 0}, False),
    ({"pricing": "free"}, False),
    ({"pricing": [{"input_price": 0, "output_price": 0}, {"input_price": 1, "output_price": 0}]}, False),
])
def test_zero_cost_model(metadata, free):
    assert zero_cost_model(metadata) is free


# ---------- when the AI service is unavailable ----------

def test_no_api_key_means_no_ai_call():
    with pytest.raises(QuestGenerationError):
        generate_slot_quests("", PLANS, [])


def test_rate_limit_gives_a_friendly_fallback_message(monkeypatch):
    def limited(*args, **kwargs):
        raise HTTPError("url", 429, "Too Many Requests", {}, None)
    monkeypatch.setattr(ai_quests, "urlopen", limited)
    with pytest.raises(QuestGenerationError, match="limit"):
        generate_slot_quests("key", PLANS, [])


@pytest.mark.parametrize("error", [URLError("offline"), TimeoutError(), HTTPError("url", 500, "boom", {}, None)])
def test_network_failures_never_crash(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(ai_quests, "urlopen", fail)
    with pytest.raises(QuestGenerationError):
        generate_slot_quests("key", PLANS, [])
