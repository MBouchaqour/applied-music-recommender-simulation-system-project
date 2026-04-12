from typing import List, Dict, Tuple, Optional
import csv
import os
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    # Resolve path relative to the project root (one level up from src/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, csv_path)

    songs = []
    with open(full_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })

    print(f"Loaded {len(songs)} songs from {csv_path}")
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against user preferences and return a (score, reasons) tuple."""
    raw_score = 0.0
    reasons: List[str] = []

    # ── Categorical matches (binary: full points or zero) ──────────────────
    if song["genre"] == user_prefs.get("genre"):
        raw_score += 2.0
        reasons.append(f"genre match ({song['genre']}) (+2.0)")

    if song["mood"] == user_prefs.get("mood"):
        raw_score += 1.5
        reasons.append(f"mood match ({song['mood']}) (+1.5)")

    # ── Numeric proximity (1 − distance, weighted) ─────────────────────────
    # energy — strong conviction feature (weight 1.5, max contribution 1.5)
    energy_sim = (1 - abs(song["energy"] - user_prefs.get("target_energy", 0.5))) * 1.5
    raw_score += energy_sim
    reasons.append(f"energy similarity {energy_sim:.2f}/1.50")

    # acousticness — strong conviction feature (weight 1.5, max contribution 1.5)
    acoustic_sim = (1 - abs(song["acousticness"] - user_prefs.get("target_acousticness", 0.5))) * 1.5
    raw_score += acoustic_sim
    reasons.append(f"acousticness similarity {acoustic_sim:.2f}/1.50")

    # valence — tiebreaker (weight 1.0, max contribution 1.0)
    valence_sim = (1 - abs(song["valence"] - user_prefs.get("target_valence", 0.5))) * 1.0
    raw_score += valence_sim
    reasons.append(f"valence similarity {valence_sim:.2f}/1.00")

    # danceability — weakest signal (weight 0.5, max contribution 0.5)
    dance_sim = (1 - abs(song["danceability"] - user_prefs.get("target_danceability", 0.5))) * 0.5
    raw_score += dance_sim
    reasons.append(f"danceability similarity {dance_sim:.2f}/0.50")

    # ── Normalize to 0.0–1.0 ───────────────────────────────────────────────
    # Max possible raw score: 2.0 + 1.5 + 1.5 + 1.5 + 1.0 + 0.5 = 8.0
    MAX_SCORE = 8.0
    final_score = round(raw_score / MAX_SCORE, 4)

    return final_score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # ── Step 1: Judge — score every song using a list comprehension ────────
    scored = [
        (song, score, " | ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]

    # ── Step 2: Rank — sorted() returns a new list, highest score first ────
    # ── Step 3: Slice — [:k] returns only the top k results ────────────────
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
