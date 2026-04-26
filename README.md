# AI Music Recommender — Powered by Claude

## Original Project

**Original project:** Music Recommender Simulation (Modules 1–3)

The original project was a rule-based, content-based music recommender built entirely without AI. It took a hardcoded user taste profile (genre, mood, energy targets) and scored all 20 songs in a CSV catalog using a weighted formula, returning the top 5 matches with visual score bars and explanations. It demonstrated how recommendation algorithms work mechanically — but it required users to manually define numeric preferences and offered no natural language interface.

---

## Title and Summary

**AI Music Recommender** is a conversational music recommendation system that lets users describe what they want in plain English and receive personalized song picks with explanations. Instead of filling out a preference form, a user can say *"I want something calm for studying"* or *"give me high-energy workout music"* and get tailored recommendations instantly.

It matters because it bridges the gap between how recommendation systems actually work (weighted feature scoring) and how people actually think (in words and feelings, not numbers). By combining a deterministic scoring engine with a large language model that interprets natural language, the system is both explainable and conversational — a combination rarely seen in simple demos.

---

## Architecture Overview

The system has six stages (see `Mermaid.js` for the full diagram):

1. **User Input** — A natural language query typed at the CLI.
2. **Claude Agent** (`src/agent.py`) — The query is sent to the Claude API with a system prompt that defines the task and a `search_songs` tool definition. Claude interprets the request and decides which parameters to pass to the tool.
3. **Tool Execution** (`src/recommender.py`) — Claude calls `search_songs` with structured parameters (genre, mood, energy targets, etc.). The tool runs the original scoring engine: `load_songs` → `score_song` × 20 → `recommend_songs`, and returns the top results as JSON with confidence scores and explanations.
4. **Agent Response** — Claude receives the tool results and formulates a conversational reply, explaining each pick in one sentence and ending with a confidence note.
5. **Output** — The final response is printed to the CLI. All steps are logged to `agent.log`.
6. **Testing Layer** — 6 pytest unit tests validate the scoring engine independently of the AI layer. Human review of sample interactions provides a second reliability check.

The key architectural decision is that Claude never replaces the scoring engine — it only interprets language and decides what to search for. The actual recommendations come from deterministic code, making every result auditable.

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MBouchaqour/applied-music-recommender-simulation-system-project.git
   cd applied-music-recommender-simulation-system-project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Mac / Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and replace `sk-ant-your-key-here` with your real Anthropic API key. Never edit `.env.example`.

5. **Run the tests to verify the scoring engine:**
   ```bash
   pytest tests/ -v
   ```
   Expected output: **6 passed**.

6. **Run the AI agent (interactive mode):**
   ```bash
   python src/main.py
   ```

7. **Run demo mode** (no API key required — uses hardcoded profiles):
   ```bash
   python src/main.py --demo
   ```

---

## Sample Interactions

### Interaction 1 — Studying / focus session

**Input:**
```
You: I want something calm and relaxing for a late-night study session
```

**Output:**
```
Assistant: Here are 5 songs perfect for a late-night study session:

1. Library Rain by Ambient Collective — Classic calm lofi with high acousticness
   and low energy, exactly what you need for focus.
2. Midnight Coding by LoFi Developer — A lofi staple with a chill mood and gentle
   tempo that won't break your concentration.
3. Focus Flow by Study Beats — Aptly named; this lofi track balances energy and
   acousticness right in the sweet spot for sustained focus.
4. Spacewalk Thoughts by Cosmo — Ambient and peaceful, with acousticness that
   keeps the room feeling quiet even with music on.
5. Coffee Shop Stories by Java Jazz — Light jazz energy and a relaxed mood make
   this a great background companion.

I'm confident these match your vibe — the catalog has strong lofi coverage for
exactly this kind of request.
```

---

### Interaction 2 — Workout / high energy

**Input:**
```
You: Give me something high energy for the gym, I want to feel pumped up
```

**Output:**
```
Assistant: Here are 5 tracks to power your workout:

1. Iron Will by Metal Machine — Extremely high energy and an intense mood; this
   one is built for pushing through the last set.
2. Gym Hero by Pop Fitness — High danceability and energy with a happy valence —
   great for maintaining pace on cardio.
3. Surge by EDM Force — Electronic production and euphoric mood give this one a
   relentless drive.
4. Rooftop Lights by City Pop — A notch below peak intensity but with strong
   danceability, good for warm-up sets.
5. Neon Sunrise by Synthwave Studio — Synthwave energy and a confident mood round
   out the list with something a bit different.

I'm quite confident on the top 3; the last two are approximate since the catalog
has limited metal and EDM entries.
```

---

### Interaction 3 — Mood-based / emotional

**Input:**
```
You: I'm feeling nostalgic and a bit melancholic, something acoustic and slow
```

**Output:**
```
Assistant: Here are 5 songs for that nostalgic, reflective mood:

1. Rainy Season Blues by Delta Soul — Blues with a melancholic mood and high
   acousticness; it feels like a rainy afternoon.
2. Old Letters by Acoustic Heart — Gentle acoustic guitar and a nostalgic mood
   make this one feel like flipping through old photos.
3. Porch Light by Country Roads — Slow tempo, acoustic, and quietly emotional —
   fits the vibe well.
4. Velvet Underground by Jazz Noir — A moody jazz piece with low energy and high
   acousticness that sits perfectly in a reflective headspace.
5. Evening Harbour by Indie Folk — Indie pop leaning acoustic; the melancholic
   valence and slow energy earn it a spot here.

Some of these genres are underrepresented in the catalog so picks 4 and 5 are
approximate — but the acoustic and emotional character should still land.
```

---

## Design Decisions

**Why Claude with tool use (Agentic Workflow) instead of a pure LLM response?**
Having Claude call a `search_songs` tool means the actual recommendations come from a deterministic scoring engine — not from the LLM's training data. This makes every recommendation auditable. You can inspect the confidence score and the `why` field for each song and verify exactly why it was chosen. A pure LLM would hallucinate song names or confidently recommend songs that don't exist in the catalog.

**Why keep the original scoring engine?**
The scoring engine is the heart of the original project. Rather than replacing it, the agent wraps it — Claude handles the part humans are good at (language), while the engine handles the part code is good at (consistent, reproducible scoring). This separation also means the engine can be tested independently of the AI layer.

**Why `claude-haiku-4-5` instead of a larger model?**
This task (interpret a music request, call one tool, write a short response) does not require deep reasoning. Haiku is fast and cheap, keeping the per-query cost well under a cent while still producing high-quality natural language responses.

**Why logging to `agent.log`?**
Every query, tool call parameters, top confidence score, and stop reason is logged. This makes it possible to audit what the system did after the fact — essential for diagnosing unexpected recommendations without re-running queries.

**Trade-offs:**
- The catalog is only 20 songs, so some genres are underrepresented. Claude is prompted to communicate low-confidence results honestly rather than pretending all picks are equally strong.
- The scoring engine uses binary genre/mood matching. Semantically similar genres (lofi vs. ambient) score identically to completely unrelated ones (lofi vs. metal). This is a known limitation documented in `model_card.md`.

---

## Testing Summary

**Test suite:** 6 pytest unit tests in `tests/test_recommender.py`

| Test | What it checks | Result |
|------|---------------|--------|
| `test_recommend_returns_songs_sorted_by_score` | Pop/happy user gets pop song ranked first | PASSED |
| `test_explain_recommendation_returns_non_empty_string` | Explanation is a non-empty string with a score | PASSED |
| `test_score_song_genre_match_scores_higher` | Genre match beats genre mismatch | PASSED |
| `test_score_song_normalized_between_0_and_1` | Scores stay in [0.0, 1.0] | PASSED |
| `test_recommend_songs_returns_k_results` | Result list length equals k | PASSED |
| `test_load_songs_returns_correct_count` | CSV loads exactly 20 songs with correct fields | PASSED |

**Result: 6/6 passed in 0.12s.**

**What worked:** The scoring engine is reliable and consistent. The same query always produces the same ranked output. The agent layer correctly passes tool parameters and handles multi-turn tool-use conversations.

**What didn't:** The binary genre/mood matching means a user asking for "ambient" music gets zero genre credit against "lofi" tracks even though the two genres are nearly identical in feel. Confidence scores can be misleading when a genre is underrepresented in the catalog — a score of 0.85 might reflect energy/acousticness matches with a completely different genre.

**What I learned:** Testing the scoring engine independently of the AI layer was the right call. It let me catch a bug in the `Recommender` OOP class stubs before they caused silent wrong results in the agent. Separating deterministic logic from AI logic makes both easier to test and debug.

---

## Ethics and Responsibility

### Limitations and Biases

- **Genre filter bubble:** Songs from underrepresented genres dominate low-confidence results. A user asking for reggae gets one strong match then falls back to unrelated songs for the remaining 4 slots.
- **Binary categorical matching:** No partial credit for semantically similar genres or moods. The system treats lofi vs. ambient the same as lofi vs. metal.
- **Static profile:** The system has no memory. Skipping a recommended song has zero effect on future recommendations.
- **Small catalog:** 20 songs covering 17 genres leaves most genres with one representative. Confidence scores can mislead users into trusting results that are actually approximate matches.

### Misuse Prevention

This is a music recommender — misuse potential is low. However, the pattern of using an LLM to interpret user intent and call a backend tool generalizes to more sensitive domains. In those contexts: (1) the tool should validate and sanitize all inputs from the LLM before executing, (2) the LLM should not have write access to any data store, and (3) logging should capture every tool call so that misuse is detectable after the fact. This system follows all three practices.

### Surprises During Testing

The biggest surprise was how confident and polished the output looks even when the underlying catalog is thin. When Claude says *"I'm confident these match your vibe"* for a reggae query, it reads as authoritative — but song #3 onward is actually just the highest-scoring non-reggae songs. The tone of the response creates trust that the data doesn't fully justify. This is a real risk in deployed AI systems: the interface communicates more certainty than the model possesses.

### AI Collaboration

**Helpful instance:** When designing the tool input schema, Claude (acting as a collaborator during development) suggested including `target_valence` and `target_danceability` as optional tool parameters even though the original `UserProfile` dataclass didn't expose them. This made the agent significantly more expressive — a user asking for "something happy and danceable" now maps correctly to numeric targets, not just a genre label.

**Flawed instance:** Early in development, Claude suggested passing the full absolute CSV path into `load_songs()` from `agent.py`. The function was designed to prepend the project root automatically, so passing an absolute path caused it to double-prepend the directory and crash with a file-not-found error. The suggestion looked correct at a glance — it's the kind of mistake that slips past review precisely because the error message points at the file path, not the function that constructed it. The fix was a one-line guard (`if os.path.isabs(csv_path)`), but the lesson is that AI-generated code involving file paths needs an explicit test before being trusted.

---

## Reflection

This project taught me that "using AI" and "building an AI system" are very different things. Calling an API is one line of code. Designing the boundary between what the LLM decides and what deterministic code executes — and making sure those two parts communicate cleanly — is the actual engineering work. The agentic workflow pattern (LLM as planner, existing code as tool) is powerful precisely because it keeps each part accountable to different standards: the LLM is evaluated on how well it interprets language, the scoring engine is evaluated on correctness and consistency.

The hardest problem wasn't technical — it was knowing when to trust the AI's output. A confident-sounding recommendation with a 0.87 confidence score can be completely wrong if the catalog doesn't support the request. Building systems that communicate their own uncertainty honestly is as important as building systems that produce good results.

---

## Project Structure

```
applied-ai-system-final/
├── src/
│   ├── agent.py          # Claude agentic workflow with tool use
│   ├── main.py           # CLI entry point (agent mode + --demo mode)
│   └── recommender.py    # Scoring engine: load_songs, score_song, recommend_songs
├── tests/
│   ├── conftest.py       # pytest path setup
│   └── test_recommender.py  # 6 unit tests
├── data/
│   └── songs.csv         # 20-song catalog
├── Mermaid.js            # System architecture diagram
├── model_card.md         # Bias documentation and evaluation
├── requirements.txt      # Dependencies
├── .env.example          # API key template (never put real keys here)
└── agent.log             # Runtime log (gitignored)
```
