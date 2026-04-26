"""
AI Music Recommendation Agent — powered by Claude with tool use.

Agentic workflow:
  1. User sends a natural language request
  2. Claude interprets it and calls the search_songs tool with structured params
  3. The tool runs the existing scoring engine against the catalog
  4. Claude receives the results and formulates a conversational response
"""

import json
import logging
import os

import anthropic
from dotenv import load_dotenv

from recommender import load_songs, recommend_songs

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

_SONGS = None


def _get_songs():
    global _SONGS
    if _SONGS is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _SONGS = load_songs(os.path.join(base_dir, "data", "songs.csv"))
    return _SONGS


SEARCH_SONGS_TOOL = {
    "name": "search_songs",
    "description": (
        "Search the music catalog for songs that match the given preferences. "
        "Always call this tool before making recommendations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "genre": {
                "type": "string",
                "description": "Music genre (e.g. lofi, pop, rock, jazz, ambient, synthwave, hip-hop, blues, classical, edm, country, r&b, metal, reggae, soul)",
            },
            "mood": {
                "type": "string",
                "description": "Desired mood (e.g. chill, happy, intense, relaxed, focused, moody, melancholic, peaceful, euphoric, nostalgic, confident)",
            },
            "target_energy": {
                "type": "number",
                "description": "Energy level 0.0 (very calm) to 1.0 (very intense)",
            },
            "target_acousticness": {
                "type": "number",
                "description": "Acousticness 0.0 (electronic/produced) to 1.0 (acoustic/organic)",
            },
            "target_valence": {
                "type": "number",
                "description": "Emotional positivity 0.0 (dark/sad) to 1.0 (bright/happy)",
            },
            "target_danceability": {
                "type": "number",
                "description": "Danceability 0.0 (not danceable) to 1.0 (very danceable)",
            },
            "k": {
                "type": "integer",
                "description": "Number of songs to return (default: 5)",
            },
        },
        "required": [],
    },
}

SYSTEM_PROMPT = """You are a music recommendation assistant. When a user describes what they want to listen to, you MUST call the search_songs tool before responding.

If the user mentions a real artist or song (e.g. "like Nirvana", "similar to Clair de Lune"), translate their style into the catalog's parameters before calling the tool:
- Nirvana → genre: rock, mood: intense, target_energy: 0.88, target_acousticness: 0.10
- Pink Floyd → genre: rock, mood: moody, target_energy: 0.60, target_acousticness: 0.25
- Bach / classical composers → genre: classical, mood: peaceful, target_energy: 0.25
- Drake / hip-hop artists → genre: hip-hop, mood: confident, target_energy: 0.75
- The Weeknd / R&B artists → genre: r&b, mood: moody, target_energy: 0.65
Use your knowledge of the artist's style to pick the closest genre and mood from the available lists.

After receiving tool results, present recommendations in a friendly, conversational way. For each song mention the title, artist, and one sentence on why it fits. End with a brief confidence note.

Available genres: lofi, pop, rock, ambient, jazz, synthwave, hip-hop, blues, classical, edm, country, r&b, metal, reggae, dream pop, soul, indie pop
Available moods: chill, happy, intense, relaxed, focused, moody, confident, melancholic, peaceful, euphoric, nostalgic, romantic, angry, joyful"""


def _execute_search_songs(tool_input: dict, songs: list) -> list:
    """Run the scoring engine with the parameters Claude chose."""
    user_prefs = {
        "genre": tool_input.get("genre", ""),
        "mood": tool_input.get("mood", ""),
        "target_energy": tool_input.get("target_energy", 0.5),
        "target_acousticness": tool_input.get("target_acousticness", 0.5),
        "target_valence": tool_input.get("target_valence", 0.5),
        "target_danceability": tool_input.get("target_danceability", 0.5),
    }
    k = tool_input.get("k", 5)
    results = recommend_songs(user_prefs, songs, k=k)
    return [
        {
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "confidence_score": score,
            "why": explanation,
        }
        for song, score, explanation in results
    ]


def _blocks_to_dicts(content) -> list:
    """Convert SDK content block objects to plain dicts for message history.

    The Anthropic SDK returns Pydantic model instances. Passing them back
    directly can fail serialization in some SDK versions; converting to dicts
    first is always safe.
    """
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return result


def _run(user_query: str) -> tuple:
    """
    Core agentic loop. Returns (response_text, songs_list).
    songs_list is the raw tool result from the last search_songs call.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file or environment."
        )

    client = anthropic.Anthropic(api_key=api_key)
    songs = _get_songs()
    captured_songs: list = []

    logger.info("User query: %r", user_query)
    messages = [{"role": "user", "content": user_query}]

    while True:
        logger.info("Sending request to Claude...")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[SEARCH_SONGS_TOOL],
            messages=messages,
        )

        logger.info("Claude stop_reason: %s", response.stop_reason)

        if response.stop_reason == "tool_use":
            tool_block = next(b for b in response.content if b.type == "tool_use")
            logger.info("Tool called: %s with params: %s", tool_block.name, tool_block.input)

            captured_songs = _execute_search_songs(tool_block.input, songs)
            top_score = captured_songs[0]["confidence_score"] if captured_songs else "N/A"
            logger.info("Tool returned %d results, top score: %s", len(captured_songs), top_score)

            # Use plain dicts — Pydantic objects from response.content can fail
            # serialization when passed back into the API in some SDK versions.
            messages.append({"role": "assistant", "content": _blocks_to_dicts(response.content)})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps(captured_songs),
                }],
            })

        else:
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "Sorry, I couldn't generate a recommendation.",
            )
            logger.info("Agent completed successfully.")
            return final_text, captured_songs


def run_agent(user_query: str) -> str:
    """Run the agent and return Claude's response as a string."""
    text, _ = _run(user_query)
    return text


def run_agent_full(user_query: str) -> dict:
    """Run the agent and return both the response text and structured song results.

    Returns:
        {"response": str, "songs": list[dict]}
        Each song dict has: title, artist, genre, mood, confidence_score, why
    """
    text, songs = _run(user_query)
    return {"response": text, "songs": songs}
