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

_BASE_SYSTEM_PROMPT = """You are a music recommendation assistant. Only answer music-related requests.

If the user asks about something unrelated to music (coding, math, weather, personal advice, general knowledge, etc.), do NOT call the search_songs tool. Instead respond: "I can only help with music recommendations. What kind of music are you looking for?"

If the user asks for something harmful or inappropriate, politely decline without calling the tool.

For all valid music requests, you MUST call the search_songs tool before responding. All numeric parameters must be between 0.0 and 1.0.

If the user mentions a real artist or song, translate their style before calling the tool:
- Nirvana → genre: rock, mood: intense, target_energy: 0.88, target_acousticness: 0.10
- Pink Floyd → genre: rock, mood: moody, target_energy: 0.60, target_acousticness: 0.25
- Bach / classical composers → genre: classical, mood: peaceful, target_energy: 0.25
- Drake / hip-hop artists → genre: hip-hop, mood: confident, target_energy: 0.75
- The Weeknd / R&B artists → genre: r&b, mood: moody, target_energy: 0.65
Use your knowledge of the artist's style to pick the closest genre and mood from the lists below.

After receiving tool results, present recommendations conversationally. For each song mention title, artist, and one sentence on why it fits. End with a brief confidence note.

Available genres: lofi, pop, rock, ambient, jazz, synthwave, hip-hop, blues, classical, edm, country, r&b, metal, reggae, dream pop, soul, indie pop
Available moods: chill, happy, intense, relaxed, focused, moody, confident, melancholic, peaceful, euphoric, nostalgic, romantic, angry, joyful"""


def _build_system_prompt(profile: dict | None) -> str:
    """Return the base system prompt, extended with personalization if available."""
    if not profile or not profile.get("history"):
        return _BASE_SYSTEM_PROMPT

    history = profile["history"]  # already a list of dicts (parsed in load_profile)
    top_genre = profile.get("top_genre") or ""
    top_mood  = profile.get("top_mood")  or ""
    query_count = int(profile.get("query_count", 0))

    recent_queries = [h["query"] for h in history[-5:] if h.get("query")]

    lines = ["\n\n--- Personalization context (registered user) ---"]
    if top_genre:
        lines.append(f"Favourite genre: {top_genre} (inferred from {query_count} past search(es))")
    if top_mood:
        lines.append(f"Favourite mood: {top_mood}")
    if recent_queries:
        quoted = ", ".join(f'"{q}"' for q in reversed(recent_queries))
        lines.append(f"Recent searches: {quoted}")
    lines.append(
        "Use this history to bias your search_songs parameters toward the user's "
        "established tastes unless the current request explicitly asks for something "
        "different. Do not mention the stored history directly in your response."
    )

    return _BASE_SYSTEM_PROMPT + "\n".join(lines)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def _execute_search_songs(tool_input: dict, songs: list) -> list:
    """Run the scoring engine with the parameters Claude chose."""
    user_prefs = {
        "genre": str(tool_input.get("genre", "")).strip().lower(),
        "mood":  str(tool_input.get("mood",  "")).strip().lower(),
        "target_energy":       _clamp(tool_input.get("target_energy",       0.5)),
        "target_acousticness": _clamp(tool_input.get("target_acousticness", 0.5)),
        "target_valence":      _clamp(tool_input.get("target_valence",      0.5)),
        "target_danceability": _clamp(tool_input.get("target_danceability", 0.5)),
    }
    # Clamp k to a safe range so Claude can't request 0 or 10000 results
    k = max(1, min(20, int(tool_input.get("k", 5))))
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


def _run(user_query: str, profile: dict | None = None) -> tuple:
    """
    Core agentic loop. Returns (response_text, songs_list).
    songs_list is the raw tool result from the last search_songs call.
    profile — optional parsed user profile dict (history already a list).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file or environment."
        )

    client = anthropic.Anthropic(api_key=api_key)
    songs = _get_songs()
    captured_songs: list = []

    system_prompt = _build_system_prompt(profile)
    is_personalized = bool(profile and profile.get("history"))
    logger.info("User query: %r (personalized=%s)", user_query, is_personalized)
    messages = [{"role": "user", "content": user_query}]

    while True:
        logger.info("Sending request to Claude...")
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=system_prompt,
                tools=[SEARCH_SONGS_TOOL],
                messages=messages,
            )
        except anthropic.AuthenticationError:
            raise RuntimeError("Invalid API key. Check your ANTHROPIC_API_KEY in .env.")
        except anthropic.RateLimitError:
            raise RuntimeError("Rate limit reached. Please wait 30 seconds and try again.")
        except anthropic.APITimeoutError:
            raise RuntimeError("Request timed out. Please try again.")
        except anthropic.APIConnectionError:
            raise RuntimeError("Could not connect to the API. Check your internet connection.")
        except anthropic.BadRequestError as e:
            raise RuntimeError(f"Bad request: {e}")

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
            if not captured_songs:
                logger.warning("Agent returned end_turn without calling search_songs.")
            logger.info("Agent completed successfully.")
            return final_text, captured_songs


def run_agent(user_query: str, profile: dict | None = None) -> str:
    """Run the agent and return Claude's response as a string."""
    text, _ = _run(user_query, profile)
    return text


def run_agent_full(user_query: str, profile: dict | None = None) -> dict:
    """Run the agent and return both the response text and structured song results.

    profile — optional parsed user profile dict; when provided, Claude's
    search_songs parameters are biased toward the user's established tastes.

    Returns:
        {"response": str, "songs": list[dict]}
        Each song dict has: title, artist, genre, mood, confidence_score, why
    """
    text, songs = _run(user_query, profile)
    return {"response": text, "songs": songs}
