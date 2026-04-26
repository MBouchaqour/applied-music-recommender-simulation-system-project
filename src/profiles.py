"""
User profile management.

Persists each user's name, preferences, and interaction history to
data/user_profiles.csv. Supports upsert semantics — submitting a new
query updates the existing row rather than appending a duplicate.

CSV columns:
    username     — unique identifier (the name the user typed)
    first_seen   — UTC timestamp of first query
    last_seen    — UTC timestamp of most recent query
    query_count  — total number of queries made
    last_query   — most recent query text
    top_genre    — genre appearing most often across all interactions
    top_mood     — mood appearing most often across all interactions
    history      — JSON array of the last MAX_HISTORY interactions
                   each entry: {query, genre, mood, timestamp}
"""

import csv
import json
import os
from datetime import datetime, timezone

PROFILE_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "user_profiles.csv",
)

FIELDNAMES = [
    "username",
    "first_seen",
    "last_seen",
    "query_count",
    "last_query",
    "top_genre",
    "top_mood",
    "history",
]

MAX_HISTORY = 20


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _read_all() -> dict:
    """Return all profiles as a dict keyed by username."""
    if not os.path.exists(PROFILE_CSV):
        return {}
    profiles = {}
    with open(PROFILE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profiles[row["username"]] = row
    return profiles


def _write_all(profiles: dict) -> None:
    """Overwrite the CSV with the current profiles dict."""
    os.makedirs(os.path.dirname(PROFILE_CSV), exist_ok=True)
    with open(PROFILE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(profiles.values())


def _parse_history(raw: str) -> list:
    try:
        return json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        return []


def load_profile(username: str) -> dict | None:
    """
    Load a profile by username.
    Returns a dict with 'history' already parsed to a list, or None if
    the user doesn't exist yet.
    """
    profile = _read_all().get(username)
    if profile is None:
        return None
    profile = dict(profile)
    profile["history"] = _parse_history(profile.get("history", "[]"))
    profile["query_count"] = int(profile.get("query_count", 0))
    return profile


def upsert_profile(username: str, query: str, songs: list) -> dict:
    """
    Create or update a user profile after a successful query.

    Infers session_genre and session_mood from the top-scored returned
    song, appends the interaction to history, and recalculates top_genre
    and top_mood from the full history.

    Returns the updated profile dict (history as a list, not JSON).
    """
    profiles = _read_all()
    now = _now()

    session_genre = songs[0]["genre"] if songs else ""
    session_mood  = songs[0]["mood"]  if songs else ""

    new_entry = {
        "query":     query,
        "genre":     session_genre,
        "mood":      session_mood,
        "timestamp": now,
    }

    if username in profiles:
        profile = profiles[username]
        history = _parse_history(profile.get("history", "[]"))
        history.append(new_entry)
        history = history[-MAX_HISTORY:]

        all_genres = [h["genre"] for h in history if h.get("genre")]
        all_moods  = [h["mood"]  for h in history if h.get("mood")]
        top_genre  = max(set(all_genres), key=all_genres.count) if all_genres else ""
        top_mood   = max(set(all_moods),  key=all_moods.count)  if all_moods  else ""

        profile.update({
            "last_seen":   now,
            "query_count": int(profile.get("query_count", 0)) + 1,
            "last_query":  query,
            "top_genre":   top_genre,
            "top_mood":    top_mood,
            "history":     json.dumps(history),
        })
    else:
        history = [new_entry]
        profile = {
            "username":    username,
            "first_seen":  now,
            "last_seen":   now,
            "query_count": 1,
            "last_query":  query,
            "top_genre":   session_genre,
            "top_mood":    session_mood,
            "history":     json.dumps(history),
        }
        profiles[username] = profile

    _write_all(profiles)

    display = dict(profile)
    display["history"] = history
    display["query_count"] = int(display["query_count"])
    return display


def get_all_profiles() -> list:
    """Return all profiles as a list of dicts with history parsed."""
    result = []
    for p in _read_all().values():
        p = dict(p)
        p["history"] = _parse_history(p.get("history", "[]"))
        p["query_count"] = int(p.get("query_count", 0))
        result.append(p)
    return result
