"""City search, Pro rules, profile_datafile photo and safe HTML (places.py, profile_datafile_data.py, account.py, design.py)."""
import base64
from contextlib import nullcontext
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.error import URLError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import account
import design
import places
import profile_data


class State(dict):
    """Minimal stand-in for st.session_state (dict + attribute access)."""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def fake_state(monkeypatch, *modules, metadata=None, location=""):
    state = State(user={"id": "u1", "user_metadata": metadata or {}}, profile_datafile={"location": location},
                  access_token="token")
    for module in modules:
        monkeypatch.setattr(module, "st", SimpleNamespace(session_state=state))
    return state


# ---------- city search (external API) ----------

PHOTON = {"features": [
    {"properties": {"name": "Lisbon", "country": "Portugal", "countrycode": "PT"}},
    {"properties": {"name": "Lisbon", "country": "Portugal", "countrycode": "PT"}},           # duplicate
    {"properties": {"name": "Lisburn", "state": "Northern Ireland", "country": "United Kingdom"}},
    {"properties": {}},                                                                    # no name
    "not a feature",
]}


@pytest.fixture(autouse=True)
def clear_city_cache():
    places._fetch_places.clear()
    yield
    places._fetch_places.clear()


def test_place_label_skips_repeats_and_blanks():
    assert places.place_label({"name": "Lisbon", "country": "Portugal"}) == "Lisbon, Portugal"
    assert places.place_label({"name": "Monaco", "state": "Monaco", "country": "Monaco"}) == "Monaco"
    assert places.place_label({}) == ""


def test_photon_results_are_deduplicated_and_cleaned():
    labels = [p["label"] for p in places.parse_places(PHOTON)]
    assert labels == ["Lisbon, Portugal", "Lisburn, Northern Ireland, United Kingdom"]
    assert places.parse_places(PHOTON, limit=1)[0]["country_code"] == "PT"


def test_search_returns_cities(monkeypatch):
    sent = {}
    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        return nullcontext(io.BytesIO(json.dumps(PHOTON).encode()))
    monkeypatch.setattr(places, "urlopen", fake_urlopen)
    assert places.search_places("Lisb")[0]["label"] == "Lisbon, Portugal"
    assert "q=Lisb" in sent["url"] and "layer=city" in sent["url"]


def test_too_short_query_does_not_call_the_api(monkeypatch):
    monkeypatch.setattr(places, "urlopen", lambda *a, **k: pytest.fail("API should not be called"))
    assert places.search_places(" L ") == []
    assert places.search_places("") == []


def test_long_queries_are_truncated(monkeypatch):
    sent = {}
    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        return nullcontext(io.BytesIO(b'{"features": []}'))
    monkeypatch.setattr(places, "urlopen", fake_urlopen)
    places.search_places("a" * 500)
    assert "a" * places.MAX_QUERY in sent["url"] and "a" * (places.MAX_QUERY + 1) not in sent["url"]


@pytest.mark.parametrize("response", [URLError("offline"), TimeoutError(), b"<html>not json</html>", b'["wrong shape"]'])
def test_unavailable_city_search_returns_none_not_a_crash(monkeypatch, response):
    def fake_urlopen(request, timeout):
        if isinstance(response, Exception):
            raise response
        return nullcontext(io.BytesIO(response))
    monkeypatch.setattr(places, "urlopen", fake_urlopen)
    assert places.search_places("Lisbon") is None


def test_failed_search_is_not_cached(monkeypatch):
    monkeypatch.setattr(places, "urlopen", lambda *a, **k: (_ for _ in ()).throw(URLError("down")))
    assert places.search_places("Porto") is None
    monkeypatch.setattr(places, "urlopen", lambda *a, **k: nullcontext(io.BytesIO(json.dumps(PHOTON).encode())))
    assert places.search_places("Porto")  # service is back: works without waiting for the cache to expire


# All pillars are available without a subscription.
def test_all_accounts_have_seven_pillars():
    assert profile_data.pillar_limit()==7
    assert profile_data.pillar_limit(5)==7


@pytest.mark.parametrize("location,country", [("Lisbon, Portugal", "Portugal"),
                                              ("Lisburn, Northern Ireland, United Kingdom", "United Kingdom"),
                                              ("", ""), (None, "")])
def test_country_comes_from_the_saved_city(location, country):
    assert profile_data.country_of(location) == country


def test_saving_metadata_uses_the_server_answer(monkeypatch):
    state = fake_state(monkeypatch, profile_data)
    api = lambda method, path, payload, token: ({"id": "u1", "user_metadata": payload["data"]}, None)
    assert profile_data.save_user_data(api, {"lifequest_preferences": {"active": True}}) is None
    assert state.user["user_metadata"]["lifequest_preferences"]["active"] is True


def test_saving_metadata_reports_errors_and_changes_nothing(monkeypatch):
    state = fake_state(monkeypatch, profile_data)
    api = lambda *args: (None, "Network error")
    assert profile_data.save_user_data(api, {"lifequest_preferences": {"active": True}}) == "Network error"
    assert "lifequest_preferences" not in state.user["user_metadata"]


# ---------- profile photo ----------

def image_bytes(fmt="PNG", size=(300, 200)):
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", size, (255, 138, 76)).save(buffer, fmt)
    return buffer.getvalue()


def test_photo_is_cropped_to_a_small_square_jpeg():
    from PIL import Image
    url = account.shrink_photo(image_bytes())
    assert url.startswith("data:image/jpeg;base64,")
    assert len(url) <= account.MAX_PHOTO_CHARS
    decoded = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert decoded.size == (account.PHOTO_SIZE, account.PHOTO_SIZE)


@pytest.mark.parametrize("raw", [b"", b"definitely not an image", b"%PDF-1.7 fake pdf"])
def test_non_images_are_rejected(raw):
    assert account.shrink_photo(raw) is None


def test_oversized_uploads_are_rejected_before_decoding():
    assert account.shrink_photo(b"0" * (account.MAX_UPLOAD_BYTES + 1)) is None


def test_only_image_data_urls_count_as_a_photo(monkeypatch):
    fake_state(monkeypatch, account, metadata={"lifequest_profile": {"photo": "javascript:alert(1)"}})
    assert account.photo() is None


def test_avatar_ring_available_to_everyone(monkeypatch):
    fake_state(monkeypatch, account, metadata={"lifequest_profile": {"ring": "lilac"}})
    assert account.ring() == "lilac"


def test_unknown_ring_falls_back_to_default(monkeypatch):
    fake_state(monkeypatch, account, metadata={"lifequest_profile": {"ring": "<script>"}})
    assert account.ring() == "peach"


# ---------- user text is escaped before it reaches HTML ----------

def test_avatar_escapes_names_and_ignores_unsafe_photos():
    html_out = design.avatar_html("<script>alert(1)</script>", photo="javascript:alert(1)")
    assert "<script>" not in html_out and "javascript:" not in html_out
    assert "&lt;" in html_out


def test_avatar_escapes_quotes_in_photo_urls():
    html_out = design.avatar_html("Ana", photo='data:image/png;base64,AAA" onerror="alert(1)')
    assert 'onerror="alert' not in html_out


def test_initials():
    assert design.initials("Ana Luiza Costa") == "AL"
    assert design.initials("") == "?"


# ---------- friendly errors and Markdown escaping (auth_helpers.py) ----------

from auth_helpers import friendly_error, plain_markdown


@pytest.mark.parametrize("message", [
    'new row violates row-level security policy for table "squad_members"',
    "permission denied for table profiles",
    'duplicate key value violates unique constraint "ai_quests_pkey"',
    "JWT expired", "", None, "x" * 200,
])
def test_technical_database_errors_are_hidden(message):
    assert friendly_error(message, "Please try again.") == "Please try again."


def test_our_own_messages_are_shown():
    assert friendly_error("Squad not found") == "Squad not found"
    assert friendly_error("You can create at most 5 squads.") == "You can create at most 5 squads."


@pytest.mark.parametrize("name,shown", [
    ("Ana", "Ana"),
    ("![x](https://evil/p.png)", "\\!\\[x\\]\\(https://evil/p\\.png\\)"),
    ("**bold** _it_", "\\*\\*bold\\*\\* \\_it\\_"),
    (None, ""),
])
def test_plain_markdown_escapes_formatting(name, shown):
    assert plain_markdown(name) == shown
