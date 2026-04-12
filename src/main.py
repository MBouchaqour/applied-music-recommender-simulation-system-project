"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Taste profile: late-night focus session listener
    user_prefs = {
        "genre": "lofi",
        "mood": "chill",
        "target_energy": 0.38,
        "target_acousticness": 0.78,
        "target_valence": 0.58,
        "target_danceability": 0.55,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # ── Header ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  🎵  MUSIC RECOMMENDER  —  Top 5 Results")
    print("  Profile: genre=lofi | mood=chill | energy=0.38")
    print("═" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, 1):
        # Score bar: visualize 0.0–1.0 as filled blocks (max 20 blocks)
        filled = int(score * 20)
        bar = "█" * filled + "░" * (20 - filled)

        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']}")
        print(f"       Score: [{bar}]  {score:.2f}")
        print(f"       Why?")
        for reason in explanation.split(" | "):
            print(f"         •  {reason}")

    print("\n" + "═" * 60 + "\n")


if __name__ == "__main__":
    main()
