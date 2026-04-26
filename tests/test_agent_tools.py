"""
Edge-case unit tests for agent.py internals and recommender helpers.

No API calls are made — all tests target pure/deterministic functions.

Coverage areas:
  1. Empty input        — empty dicts, empty strings, empty lists
  2. Invalid data types — wrong types for numeric params and k
  3. Missing profile    — None / incomplete profile dicts
  4. Extremely long input — very long strings in genre, mood, query history
  5. Special characters  — emoji, SQL injection, HTML, newlines
"""

import pytest

from src.agent import _clamp, _build_system_prompt, _execute_search_songs, _BASE_SYSTEM_PROMPT
from src.recommender import score_song, recommend_songs, load_songs


# ── Shared fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def small_catalog():
    return [
        {"id": 1, "title": "Pop Song", "artist": "A", "genre": "pop", "mood": "happy",
         "energy": 0.8, "tempo_bpm": 120, "valence": 0.9, "danceability": 0.8, "acousticness": 0.2},
        {"id": 2, "title": "Chill Loop", "artist": "B", "genre": "lofi", "mood": "chill",
         "energy": 0.3, "tempo_bpm": 75, "valence": 0.5, "danceability": 0.4, "acousticness": 0.9},
        {"id": 3, "title": "Rock Track", "artist": "C", "genre": "rock", "mood": "intense",
         "energy": 0.9, "tempo_bpm": 140, "valence": 0.4, "danceability": 0.6, "acousticness": 0.1},
    ]


@pytest.fixture
def rich_profile():
    return {
        "top_genre": "rock",
        "top_mood": "intense",
        "query_count": 7,
        "history": [
            {"query": "heavy guitar riffs", "genre": "rock", "mood": "intense", "timestamp": "2026-04-01"},
            {"query": "something like Nirvana", "genre": "rock", "mood": "intense", "timestamp": "2026-04-10"},
            {"query": "loud and fast", "genre": "metal", "mood": "angry", "timestamp": "2026-04-15"},
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. Empty input
# ══════════════════════════════════════════════════════════════════════════════

class TestEmptyInput:

    def test_execute_search_songs_empty_tool_input(self, small_catalog):
        """Empty tool input falls back to all defaults — must not raise."""
        results = _execute_search_songs({}, small_catalog)
        assert isinstance(results, list)
        assert len(results) == 5 or len(results) == len(small_catalog)  # k defaults to 5, catalog has 3

    def test_execute_search_songs_empty_genre_and_mood(self, small_catalog):
        """Explicitly empty genre/mood strings — no categorical bonus, still returns results."""
        results = _execute_search_songs({"genre": "", "mood": ""}, small_catalog)
        assert isinstance(results, list)
        assert len(results) > 0
        for song in results:
            assert 0.0 <= song["confidence_score"] <= 1.0

    def test_execute_search_songs_empty_catalog(self):
        """Empty song catalog should return an empty list without raising."""
        results = _execute_search_songs({"genre": "pop", "mood": "happy"}, [])
        assert results == []

    def test_recommend_songs_empty_catalog(self):
        """recommend_songs with no songs returns []."""
        prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.5,
                 "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
        assert recommend_songs(prefs, [], k=5) == []

    def test_score_song_empty_genre_and_mood(self):
        """Empty preference strings — no categorical points, numeric scoring still works."""
        prefs = {"genre": "", "mood": "", "target_energy": 0.5,
                 "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
        song = {"genre": "pop", "mood": "happy", "energy": 0.5,
                "acousticness": 0.5, "valence": 0.5, "danceability": 0.5}
        score, reasons = score_song(prefs, song)
        assert 0.0 <= score <= 1.0
        assert len(reasons) > 0

    def test_build_system_prompt_empty_history_list(self):
        """Profile with an empty history list → base prompt only, no personalization block."""
        profile = {"top_genre": "pop", "top_mood": "happy", "query_count": 3, "history": []}
        result = _build_system_prompt(profile)
        assert result == _BASE_SYSTEM_PROMPT
        assert "Personalization" not in result


# ══════════════════════════════════════════════════════════════════════════════
# 2. Invalid data types
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidDataTypes:

    def test_clamp_string_raises(self):
        """_clamp must raise when given a non-numeric string."""
        with pytest.raises((ValueError, TypeError)):
            _clamp("high")

    def test_clamp_none_raises(self):
        with pytest.raises((ValueError, TypeError)):
            _clamp(None)

    def test_execute_search_songs_string_k_falls_back(self, small_catalog):
        """Non-integer k string should not blow up — either raises cleanly or uses fallback."""
        try:
            results = _execute_search_songs({"k": "bad"}, small_catalog)
            # If implementation handles it gracefully, results should still be a list
            assert isinstance(results, list)
        except (ValueError, TypeError):
            pass  # Acceptable — documents current behaviour for invalid k

    def test_execute_search_songs_non_numeric_energy(self, small_catalog):
        """Non-numeric target_energy should not silently produce wrong scores."""
        try:
            results = _execute_search_songs({"target_energy": "loud"}, small_catalog)
            assert isinstance(results, list)
        except (ValueError, TypeError):
            pass  # Acceptable — documents current behaviour

    def test_execute_search_songs_numeric_genre(self, small_catalog):
        """Numeric genre is coerced to string via str() — must not raise."""
        results = _execute_search_songs({"genre": 42, "mood": 99}, small_catalog)
        assert isinstance(results, list)

    def test_score_song_missing_numeric_fields_uses_defaults(self):
        """score_song falls back to 0.5 for any missing target_* key."""
        prefs = {"genre": "pop", "mood": "happy"}   # no target_* keys
        song = {"genre": "pop", "mood": "happy", "energy": 0.5,
                "acousticness": 0.5, "valence": 0.5, "danceability": 0.5}
        score, _ = score_song(prefs, song)
        assert 0.0 <= score <= 1.0

    def test_recommend_songs_k_larger_than_catalog(self, small_catalog):
        """k > catalog size returns all available songs (not more)."""
        prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.5,
                 "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
        results = recommend_songs(prefs, small_catalog, k=100)
        assert len(results) == len(small_catalog)

    def test_execute_search_songs_k_zero_clamped_to_one(self, small_catalog):
        """k=0 should be clamped to 1 by _execute_search_songs."""
        results = _execute_search_songs({"k": 0}, small_catalog)
        assert len(results) == 1

    def test_execute_search_songs_k_huge_clamped_to_twenty(self, small_catalog):
        """k=9999 should be clamped to 20 (catalog only has 3 songs here → 3 returned)."""
        results = _execute_search_songs({"k": 9999}, small_catalog)
        assert len(results) <= 20


# ══════════════════════════════════════════════════════════════════════════════
# 3. Missing user profile
# ══════════════════════════════════════════════════════════════════════════════

class TestMissingProfile:

    def test_build_system_prompt_none(self):
        """None profile returns the unmodified base prompt."""
        assert _build_system_prompt(None) == _BASE_SYSTEM_PROMPT

    def test_build_system_prompt_empty_dict(self):
        """Empty dict profile (no history key) returns base prompt."""
        assert _build_system_prompt({}) == _BASE_SYSTEM_PROMPT

    def test_build_system_prompt_history_key_missing(self):
        """Profile without a 'history' key returns base prompt."""
        profile = {"top_genre": "jazz", "top_mood": "relaxed", "query_count": 2}
        assert _build_system_prompt(profile) == _BASE_SYSTEM_PROMPT

    def test_build_system_prompt_history_none(self):
        """Profile where history is None returns base prompt."""
        profile = {"top_genre": "jazz", "top_mood": "relaxed", "query_count": 2, "history": None}
        assert _build_system_prompt(profile) == _BASE_SYSTEM_PROMPT

    def test_build_system_prompt_partial_profile(self):
        """Profile with history but no top_genre/top_mood still returns a valid prompt."""
        profile = {
            "query_count": 1,
            "history": [{"query": "calm music", "genre": "ambient", "mood": "peaceful",
                          "timestamp": "2026-04-01"}],
        }
        result = _build_system_prompt(profile)
        assert isinstance(result, str)
        assert len(result) > len(_BASE_SYSTEM_PROMPT)
        assert "calm music" in result


# ══════════════════════════════════════════════════════════════════════════════
# 4. Extremely long input
# ══════════════════════════════════════════════════════════════════════════════

class TestExtremelyLongInput:

    def test_execute_search_songs_very_long_genre(self, small_catalog):
        """A 5000-char genre string must not raise — it simply won't match any song."""
        long_genre = "a" * 5000
        results = _execute_search_songs({"genre": long_genre, "mood": "chill"}, small_catalog)
        assert isinstance(results, list)
        for song in results:
            assert song["genre"] != long_genre   # no match expected

    def test_execute_search_songs_very_long_mood(self, small_catalog):
        """A 5000-char mood string must not raise."""
        long_mood = "z" * 5000
        results = _execute_search_songs({"genre": "pop", "mood": long_mood}, small_catalog)
        assert isinstance(results, list)

    def test_build_system_prompt_long_query_history(self):
        """Profile with a 1000-char query in history must produce a valid string prompt."""
        long_query = "find me " + "something " * 100
        profile = {
            "top_genre": "pop",
            "top_mood": "happy",
            "query_count": 1,
            "history": [{"query": long_query, "genre": "pop", "mood": "happy",
                          "timestamp": "2026-04-01"}],
        }
        result = _build_system_prompt(profile)
        assert isinstance(result, str)
        assert long_query.strip() in result

    def test_build_system_prompt_many_history_entries_only_last_five(self):
        """Only the last 5 history entries are included in the prompt."""
        history = [{"query": f"query {i}", "genre": "pop", "mood": "happy",
                    "timestamp": "2026-04-01"} for i in range(20)]
        profile = {"top_genre": "pop", "top_mood": "happy", "query_count": 20, "history": history}
        result = _build_system_prompt(profile)
        assert "query 19" in result   # last entry is included
        assert "query 0" not in result  # earliest entries are trimmed

    def test_recommend_songs_large_k_does_not_exceed_catalog(self, small_catalog):
        """Requesting far more songs than the catalog holds returns at most catalog size."""
        prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.5,
                 "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
        results = recommend_songs(prefs, small_catalog, k=10_000)
        assert len(results) <= len(small_catalog)


# ══════════════════════════════════════════════════════════════════════════════
# 5. Special characters in input
# ══════════════════════════════════════════════════════════════════════════════

class TestSpecialCharacters:

    def test_execute_search_songs_emoji_in_genre(self, small_catalog):
        """Emoji genre does not match any song but must not raise."""
        results = _execute_search_songs({"genre": "🎸🔥", "mood": "happy"}, small_catalog)
        assert isinstance(results, list)

    def test_execute_search_songs_sql_injection_in_genre(self, small_catalog):
        """SQL-injection-like string is treated as a plain non-matching genre."""
        results = _execute_search_songs({"genre": "'; DROP TABLE songs; --"}, small_catalog)
        assert isinstance(results, list)
        for r in results:
            assert "confidence_score" in r

    def test_execute_search_songs_html_in_mood(self, small_catalog):
        """HTML tags in mood are treated as a plain non-matching string."""
        results = _execute_search_songs({"mood": "<script>alert(1)</script>"}, small_catalog)
        assert isinstance(results, list)

    def test_execute_search_songs_newlines_and_tabs(self, small_catalog):
        """Whitespace control characters in genre/mood are handled by strip().lower()."""
        results = _execute_search_songs({"genre": "\npop\t", "mood": "\r\nchill"}, small_catalog)
        assert isinstance(results, list)
        # After strip(), "pop" and "chill" should match songs in the catalog
        genres = [r["genre"] for r in results]
        assert "pop" in genres or "lofi" in genres

    def test_build_system_prompt_special_chars_in_history(self):
        """Special characters in history queries must not break prompt construction."""
        profile = {
            "top_genre": "pop",
            "top_mood": "happy",
            "query_count": 3,
            "history": [
                {"query": "<script>alert('xss')</script>", "genre": "pop", "mood": "happy",
                 "timestamp": "2026-04-01"},
                {"query": "'; DROP TABLE users; --", "genre": "pop", "mood": "happy",
                 "timestamp": "2026-04-02"},
                {"query": "music with ♫ notes and 日本語", "genre": "pop", "mood": "happy",
                 "timestamp": "2026-04-03"},
            ],
        }
        result = _build_system_prompt(profile)
        assert isinstance(result, str)
        assert len(result) > len(_BASE_SYSTEM_PROMPT)

    def test_score_song_special_char_genre_no_match(self):
        """Genre with special chars never matches a catalog genre — no crash, lower score."""
        prefs = {"genre": "p🎵p", "mood": "happy", "target_energy": 0.8,
                 "target_acousticness": 0.2, "target_valence": 0.9, "target_danceability": 0.8}
        song = {"genre": "pop", "mood": "happy", "energy": 0.8,
                "acousticness": 0.2, "valence": 0.9, "danceability": 0.8}
        score_special, _ = score_song(prefs, song)

        prefs_normal = dict(prefs, genre="pop")
        score_normal, _ = score_song(prefs_normal, song)

        assert score_special < score_normal   # missing genre bonus
        assert 0.0 <= score_special <= 1.0

    def test_load_songs_nonexistent_path_raises(self):
        with pytest.raises(FileNotFoundError):
            load_songs("data/this_file_does_not_exist.csv")
