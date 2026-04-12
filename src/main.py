"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def print_recommendations(label: str, profile_summary: str, recommendations: list) -> None:
    print("\n" + "═" * 60)
    print(f"  🎵  MUSIC RECOMMENDER  —  {label}")
    print(f"  Profile: {profile_summary}")
    print("═" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, 1):
        filled = int(score * 20)
        bar = "█" * filled + "░" * (20 - filled)

        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']}")
        print(f"       Score: [{bar}]  {score:.2f}")
        print(f"       Why?")
        for reason in explanation.split(" | "):
            print(f"         •  {reason}")

    print("\n" + "═" * 60 + "\n")


def main() -> None:
    songs = load_songs("data/songs.csv")

    # ── Profile 1: Chill Lofi — late-night focus session listener ──────────
    chill_lofi = {
        "genre": "lofi",
        "mood": "chill",
        "target_energy": 0.38,
        "target_acousticness": 0.78,
        "target_valence": 0.58,
        "target_danceability": 0.55,
    }

    # ── Profile 2: High-Energy Pop — workout / hype listener ───────────────
    high_energy_pop = {
        "genre": "pop",
        "mood": "happy",
        "target_energy": 0.90,
        "target_acousticness": 0.10,
        "target_valence": 0.85,
        "target_danceability": 0.88,
    }

    # ── Profile 3: Deep Intense Rock — heavy / aggressive listener ──────────
    deep_intense_rock = {
        "genre": "rock",
        "mood": "intense",
        "target_energy": 0.92,
        "target_acousticness": 0.08,
        "target_valence": 0.30,
        "target_danceability": 0.60,
    }

    print_recommendations(
        "Top 5 Results — Chill Lofi",
        "genre=lofi | mood=chill | energy=0.38",
        recommend_songs(chill_lofi, songs, k=5),
    )

    print_recommendations(
        "Top 5 Results — High-Energy Pop",
        "genre=pop | mood=happy | energy=0.90",
        recommend_songs(high_energy_pop, songs, k=5),
    )

    print_recommendations(
        "Top 5 Results — Deep Intense Rock",
        "genre=rock | mood=intense | energy=0.92",
        recommend_songs(deep_intense_rock, songs, k=5),
    )


if __name__ == "__main__":
    main()
