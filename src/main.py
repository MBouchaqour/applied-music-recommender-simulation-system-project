"""
Music Recommender — CLI entry point.

Usage:
  python src/main.py            # Interactive AI agent mode (requires ANTHROPIC_API_KEY)
  python src/main.py --demo     # Demo mode — runs three hardcoded profiles, no API key needed
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommender import load_songs, recommend_songs


def print_recommendations(label: str, profile_summary: str, recommendations: list) -> None:
    print("\n" + "═" * 60)
    print(f"  MUSIC RECOMMENDER  —  {label}")
    print(f"  Profile: {profile_summary}")
    print("═" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, 1):
        filled = int(score * 20)
        bar = "█" * filled + "░" * (20 - filled)
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']}")
        print(f"       Score: [{bar}]  {score:.2f}")
        print("       Why?")
        for reason in explanation.split(" | "):
            print(f"         •  {reason}")

    print("\n" + "═" * 60 + "\n")


def run_demo() -> None:
    songs = load_songs("data/songs.csv")

    profiles = [
        (
            "Chill Lofi",
            "genre=lofi | mood=chill | energy=0.38",
            {"genre": "lofi", "mood": "chill", "target_energy": 0.38,
             "target_acousticness": 0.78, "target_valence": 0.58, "target_danceability": 0.55},
        ),
        (
            "High-Energy Pop",
            "genre=pop | mood=happy | energy=0.90",
            {"genre": "pop", "mood": "happy", "target_energy": 0.90,
             "target_acousticness": 0.10, "target_valence": 0.85, "target_danceability": 0.88},
        ),
        (
            "Deep Intense Rock",
            "genre=rock | mood=intense | energy=0.92",
            {"genre": "rock", "mood": "intense", "target_energy": 0.92,
             "target_acousticness": 0.08, "target_valence": 0.30, "target_danceability": 0.60},
        ),
    ]

    for label, summary, prefs in profiles:
        print_recommendations(label, summary, recommend_songs(prefs, songs, k=5))


def run_agent_mode() -> None:
    from agent import run_agent

    print("\n" + "═" * 60)
    print("  AI MUSIC RECOMMENDER  —  Powered by Claude")
    print("  Tell me what you want to listen to.")
    print("  Type 'quit' to exit.")
    print("═" * 60 + "\n")

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\nSearching...\n")
        try:
            response = run_agent(query)
            print(f"Assistant: {response}\n")
        except EnvironmentError as e:
            print(f"\nError: {e}\n")
            break
        except Exception as e:
            print(f"\nSomething went wrong: {e}\n")

        print("─" * 60 + "\n")


def main() -> None:
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_agent_mode()


if __name__ == "__main__":
    main()
