# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

This system is a **content-based music recommender** built around a single "late-night focus session" listener. Given a user taste profile, it reads every song from `songs.csv`, scores each one against the profile using a weighted formula, and returns the top 5 ranked by similarity. No listening history or other users are involved — every recommendation is driven entirely by how closely a song's features match what the user declared they want.


--- Answer by Mustapha Bouchaqour: 

### How Real-World Recommendations Work (and What This Version Prioritizes)

Real-world recommendation systems — like those used by Spotify or YouTube Music — typically rely on one of two approaches: **collaborative filtering**, which finds users with similar listening histories and recommends what they liked, or **content-based filtering**, which ignores other users entirely and instead compares the intrinsic attributes of songs. Production systems usually combine both. This simulation focuses exclusively on **content-based filtering**, which means it makes no assumptions about what other listeners do — it only asks: *"How closely does this song's musical DNA match the user's stated preferences?"* The system will prioritize **genre and mood as hard semantic signals** (the user explicitly wants a certain vibe), then use **energy and valence** to fine-tune similarity within that space, with `danceability` and `acousticness` as secondary texture signals. The result is a transparent, explainable system where every recommendation can be justified by specific feature matches.

---

### `Song` Object — Features

| Feature | Type | Role |
|---|---|---|
| `id` | `int` | Unique identifier |
| `title` | `str` | Display only |
| `artist` | `str` | Display only |
| `genre` | `str` | Primary similarity signal |
| `mood` | `str` | Primary similarity signal |
| `energy` | `float` | Acoustic intensity (0–1) |
| `valence` | `float` | Musical positivity (0–1) |
| `danceability` | `float` | Rhythmic fit (0–1) |
| `acousticness` | `float` | Production style (0–1) |
| `tempo_bpm` | `float` | Downweighted; correlated with energy |

---

### `UserProfile` Object — Features

| Feature | Type | Role |
|---|---|---|
| `favorite_genre` | `str` | Matched against `song.genre` |
| `favorite_mood` | `str` | Matched against `song.mood` |
| `target_energy` | `float` | Compared to `song.energy` via distance |
| `likes_acoustic` | `bool` | Maps to `song.acousticness` threshold |

The `UserProfile` is intentionally minimal — it captures only what a user would naturally express ("I want chill lofi with low energy"), keeping the system interpretable without requiring listening history.

---

## Concept Sketch: Recommender Data Flow

```
┌─────────────────────┐         ┌──────────────────────────┐
│     UserProfile      │         │        Song Catalog       │
│─────────────────────│         │──────────────────────────│
│ favorite_genre: lofi│         │ id, title, artist        │
│ favorite_mood: chill│         │ genre, mood              │
│ target_energy: 0.40 │         │ energy, valence          │
│ likes_acoustic: True│         │ danceability, acousticness│
└────────┬────────────┘         └────────────┬─────────────┘
         │                                   │
         │         ┌─────────────┐           │
         └────────►│ score_song()│◄──────────┘
                   │─────────────│
                   │ genre match?│  → +2.0 weight
                   │ mood match? │  → +2.0 weight
                   │ |Δenergy|   │  → penalize distance
                   │ acousticness│  → reward if likes_acoustic
                   └──────┬──────┘
                          │ (score, reasons)
                          ▼
                   ┌─────────────────┐
                   │recommend_songs()│
                   │─────────────────│
                   │ score all songs │
                   │ sort descending │
                   │ exclude seed    │
                   │ return top k    │
                   └──────┬──────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │  Results for lofi/chill │
             │─────────────────────────│
             │ 1. Library Rain   0.97  │  ← genre+mood+acoustic match
             │ 2. Midnight Coding 0.94 │  ← genre+mood+energy match
             │ 3. Focus Flow     0.81  │  ← genre+energy match
             └─────────────────────────┘
```

---

## How Real Systems Do This at Scale

This simulation handles 10 songs with hand-crafted features — real systems handle 100M+ tracks. The core pipeline is the same, but each stage is industrialized:

**Feature extraction** — Spotify doesn't manually label `energy` or `valence`; ML models analyze raw audio waveforms (MFCCs, spectral features) to auto-generate those numbers. What we encode by hand, they learn automatically.

**User profile** — Rather than a static 4-field object, real profiles are dense vectors built from listening history, skips, replays, and playlist behavior. A user who skips every track under 120 BPM implicitly signals a `tempo_bpm` preference without ever stating it.

**Similarity computation** — Cosine similarity over 10 songs is trivial. Over 100M songs it's not — real systems use **Approximate Nearest Neighbor** indexes (e.g., FAISS, ScaNN) that find the closest vectors in milliseconds without comparing everything.

**Hybrid scoring** — Content-based (what this simulation does) is combined with collaborative filtering ("users like you also liked...") via a learned blend weight. Neither alone is as strong as both together.

**What this simulation gets right** — The separation of `score_song` (one song) from `recommend_songs` (ranked list), the weighted feature vector, and the explainability via `reasons` are all patterns used in production. The architecture is sound; only the scale differs.


### User Profile (The Listener)

```python
user_prefs = {
    "genre": "lofi",              # categorical anchor — highest weight
    "mood": "chill",              # categorical anchor — second highest weight
    "target_energy": 0.38,        # strong conviction: must be calm
    "target_acousticness": 0.78,  # strong conviction: prefers organic sound
    "target_valence": 0.58,       # loose tiebreaker: neutral-to-positive
    "target_danceability": 0.55,  # loose tiebreaker: not a priority
    "likes_acoustic": True,       # derived boolean for OOP interface
}
```

### Algorithm Recipe

Each song is scored by `score_song()` using this formula:

```
score = 0

① if song.genre == user.genre        → + 2.0   (genre match)
② if song.mood  == user.mood         → + 1.5   (mood match)

③ energy        → (1 − |song.energy − 0.38|)        × 1.5
④ acousticness  → (1 − |song.acousticness − 0.78|)  × 1.5
⑤ valence       → (1 − |song.valence − 0.58|)       × 1.0
⑥ danceability  → (1 − |song.danceability − 0.55|)  × 0.5

final_score = score ÷ 8.0       →  range 0.0 – 1.0
```

All 20 scored songs are then sorted descending by `final_score` and the top 5 are returned with an explanation of which rules fired.

### Expected Rankings Against the Dataset

| Rank | Song | Score | Why |
|---|---|---|---|
| 1 | Library Rain | ~0.97 | genre ✅ mood ✅ energy ✅ acousticness ✅ |
| 2 | Midnight Coding | ~0.91 | genre ✅ mood ✅ energy close |
| 3 | Focus Flow | ~0.79 | genre ✅ energy ✅ |
| 4 | Spacewalk Thoughts | ~0.63 | mood ✅ acousticness ✅ |
| 5 | Coffee Shop Stories | ~0.54 | acousticness ✅ |



### Potential Biases & Limitations

- **Genre over-prioritization** — With a weight of 2.0, genre is the single most powerful signal. A song like *Rainy Season* (blues, melancholic) that shares almost identical energy (0.33) and acousticness (0.88) with the user's targets will score lower than a mediocre lofi track simply because the genre label differs. Users who care more about sound than label will find this frustrating.

- **Mood label collisions** — Moods like `chill` and `relaxed` feel nearly identical to a human listener but this system treats them as completely different, scoring `relaxed` the same as `intense`. A smarter system would group semantically similar moods.

- **Binary categorical matching** — Genre and mood either fully match (+points) or they don't (+0). There is no partial credit for near-matches (e.g., `lofi` vs `ambient` are both calm low-energy genres but score identically to `metal` as a non-match).

- **Static profile** — The user profile never updates. If a user listens to a recommended song and skips it, the system has no mechanism to learn from that signal.

---

> **Checkpoint:** The system has a fully defined user profile, a 20-song expanded dataset covering 16 genres and 14 moods, and a weighted scoring recipe with explicit bias acknowledgments. Implementation phase can begin.


### CLI Verification
![Top 5 Song Suggestions](photos/Top_5_suggestions.png)



---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

