"""
Test suite for the Music Recommender.

Run from the project root:
  pytest tests/ -v

Testing summary (Step 4):
  6 tests covering: OOP Recommender class, score_song scoring logic,
  recommend_songs output, and load_songs data loading.
"""

import os
import pytest
from recommender import Song, UserProfile, Recommender, load_songs, score_song, recommend_songs


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_small_recommender() -> Recommender:
    songs = [
        Song(id=1, title="Test Pop Track", artist="Test Artist", genre="pop", mood="happy",
             energy=0.8, tempo_bpm=120, valence=0.9, danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Test Artist", genre="lofi", mood="chill",
             energy=0.4, tempo_bpm=80, valence=0.6, danceability=0.5, acousticness=0.9),
    ]
    return Recommender(songs)


def pop_user() -> UserProfile:
    return UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)


# ── OOP Recommender tests ─────────────────────────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    """Pop/happy user should get the pop song ranked first."""
    rec = make_small_recommender()
    results = rec.recommend(pop_user(), k=2)
    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    """Explanation should be a non-empty string containing a score."""
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(pop_user(), rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
    assert "Score:" in explanation


# ── score_song tests ──────────────────────────────────────────────────────────

def test_score_song_genre_match_scores_higher():
    """A song whose genre matches the preference should outscore one that doesn't."""
    user_prefs = {"genre": "pop", "mood": "chill", "target_energy": 0.5,
                  "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
    song_match    = {"genre": "pop",  "mood": "jazz", "energy": 0.5,
                     "acousticness": 0.5, "valence": 0.5, "danceability": 0.5}
    song_no_match = {"genre": "rock", "mood": "jazz", "energy": 0.5,
                     "acousticness": 0.5, "valence": 0.5, "danceability": 0.5}
    score_match, _    = score_song(user_prefs, song_match)
    score_no_match, _ = score_song(user_prefs, song_no_match)
    assert score_match > score_no_match


def test_score_song_normalized_between_0_and_1():
    """Perfect-match song should produce a score in [0, 1]."""
    user_prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.8,
                  "target_acousticness": 0.1, "target_valence": 0.9, "target_danceability": 0.8}
    song = {"genre": "pop", "mood": "happy", "energy": 0.8,
            "acousticness": 0.1, "valence": 0.9, "danceability": 0.8}
    score, _ = score_song(user_prefs, song)
    assert 0.0 <= score <= 1.0


# ── recommend_songs tests ─────────────────────────────────────────────────────

def test_recommend_songs_returns_k_results():
    """Should return exactly k results."""
    songs = [
        {"id": i, "title": f"Song {i}", "artist": "A", "genre": "pop", "mood": "happy",
         "energy": 0.5, "acousticness": 0.5, "valence": 0.5, "danceability": 0.5, "tempo_bpm": 100}
        for i in range(10)
    ]
    user_prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.5,
                  "target_acousticness": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
    results = recommend_songs(user_prefs, songs, k=3)
    assert len(results) == 3


# ── load_songs tests ──────────────────────────────────────────────────────────

def test_load_songs_returns_correct_count():
    """CSV catalog should load all songs with the expected fields and types."""
    songs = load_songs("data/songs.csv")
    assert len(songs) == 10_020
    assert "title" in songs[0]
    assert "energy" in songs[0]
    assert isinstance(songs[0]["energy"], float)
