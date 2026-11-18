"""City search with the free Photon geocoder (OpenStreetMap data, no API key).

Only the text the user types is sent to Photon. The chosen city is stored as a
plain label (e.g. "Lisbon, Portugal"); quests are not changed by it.
"""
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st

PHOTON_URL = "https://photon.komoot.io/api/"
MAX_QUERY = 80


def place_label(props: dict) -> str:
    """'Lisbon, Portugal' or 'Lisburn, Northern Ireland, United Kingdom'."""
    parts = [props.get("name"), props.get("state"), props.get("country")]
    seen, out = set(), []
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            out.append(part)
    return ", ".join(out)


class PlaceSearchUnavailable(Exception):
    """Photon could not be reached or answered with something unreadable."""


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_places(query: str, limit: int) -> list[dict]:
    # Raising (instead of returning) keeps failures out of the cache, so a later retry can succeed.
    url = PHOTON_URL + "?" + urlencode({"q": query, "limit": limit, "layer": "city", "lang": "en"})
    try:
        with urlopen(Request(url, headers={"User-Agent": "LifeQuest-student-project/1.0"}), timeout=6) as response:
            data = json.load(response)
    except (URLError, TimeoutError, ValueError, OSError) as error:
        raise PlaceSearchUnavailable() from error
    if not isinstance(data, dict) or not isinstance(data.get("features"), list):
        raise PlaceSearchUnavailable()
    return parse_places(data, limit)


def parse_places(data: dict, limit: int = 6) -> list[dict]:
    """Turn a Photon response into unique, labelled cities."""
    results, labels = [], set()
    for feature in data.get("features", []):
        props = feature.get("properties", {}) if isinstance(feature, dict) else {}
        label = place_label(props)
        if not label or label in labels:
            continue
        labels.add(label)
        results.append({"label": label, "city": props.get("name"), "country": props.get("country"),
                        "country_code": props.get("countrycode")})
    return results[:limit]


def search_places(query: str, limit: int = 6) -> list[dict] | None:
    """Cities matching `query`; [] when nothing matches; None when the search service is unavailable."""
    query = (query or "").strip()[:MAX_QUERY]
    if len(query) < 2:
        return []
    try:
        return _fetch_places(query, limit)
    except PlaceSearchUnavailable:
        return None


def city_picker(key: str, current: str = "", label: str = "Your city (optional)",
                placeholder: str = "Start typing your city, for example Lisbon", none_found: str = "No matching city found. Check the spelling.",
                pick_label: str = "Choose your city",
                unavailable: str = "City search is unavailable right now. You can skip this and add your city later in Settings.") -> dict | None:
    """Type-ahead city search. Returns the chosen place dict, or None if nothing is chosen yet."""
    query = st.text_input(label, value=current, key=key + "_query", placeholder=placeholder, max_chars=MAX_QUERY)
    if not query.strip() or query.strip() == current:
        return None
    matches = search_places(query)
    if matches is None:
        st.warning(unavailable)
        return None
    if not matches:
        st.caption(none_found)
        return None
    labels = [m["label"] for m in matches]
    choice = st.radio(pick_label, labels, index=None, key=key + "_choice", label_visibility="collapsed")
    return next((m for m in matches if m["label"] == choice), None)


def clear_city_picker(key: str) -> None:
    """Forget the typed text and the picked city, so a saved choice is not saved again on the next run."""
    for suffix in ("_query", "_choice"):
        st.session_state.pop(key + suffix, None)
