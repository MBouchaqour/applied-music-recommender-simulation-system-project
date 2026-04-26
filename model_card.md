# Model Card: AI Music Recommender

**Author:** Mustafa Bouchaqour  
**Model name:** AI Music Recommender  
**Version:** 2.0 (evolved from MoodMatch 1.0 — rule-based CLI)  
**Last updated:** April 2026

---

## 1. How I Collaborated with AI in This Project

This project used AI in two distinct ways — as a component inside the system, and as a collaborator during development.

**AI inside the system (Claude Haiku as the agent)**  
The core of the app is an agentic loop where Claude Haiku interprets a user's natural language request and decides what parameters to pass to the `search_songs` tool. Claude never picks the songs directly — it translates words like "something calm for studying" into structured numeric parameters (genre, mood, energy targets), and the deterministic scoring engine does the rest. This separation was intentional: Claude handles language, code handles logic. Every recommendation is fully auditable because the score comes from a formula, not from what the model "thinks" sounds good.

**AI as a development collaborator (Claude as assistant)**  
Throughout the build I worked with Claude Code to design and implement each layer. The collaboration was iterative: I described what I wanted, Claude proposed an approach, I either approved or redirected it, and then we built it together. Some specific moments where the collaboration shaped the final design:

- When implementing the tool schema, Claude suggested adding `target_valence` and `target_danceability` as optional parameters. I hadn't included them in my original plan, but they turned out to be important — a user asking for "something happy and danceable" now maps to distinct numeric targets rather than just a genre label.
- When expanding the song catalog, I described the goal (10,000 new songs with realistic per-genre parameters) and Claude wrote `expand_songs.py`. I reviewed the genre parameter ranges and word banks before running it — collaborative authorship, not blind delegation.
- When we hit the `400 Bad Request` API error (tool_use IDs without matching tool_result blocks), Claude diagnosed the root cause — the Anthropic SDK returns Pydantic model instances that fail serialization when passed back to the API — and added the `_blocks_to_dicts()` conversion. I wouldn't have found that without it.
- The authentication module was designed collaboratively: I specified the security requirements (PBKDF2, constant-time comparison, lockout), Claude implemented them, and I reviewed the code for correctness before accepting it.

The most important thing I learned about AI collaboration is that it works best when you stay in the driver's seat. Every time I approved code without fully understanding it, I had to come back and debug it later. Every time I understood what was being built and asked targeted questions, the result was better.

---

## 2. Biases in the Recommendation System

**Genre filter bubble**  
Genre carries the highest weight in the scoring formula (+2.0 out of a maximum 8.0 raw score). When a requested genre has few songs in the catalog, the system runs out of good matches and falls back to songs that score well on numeric features alone. A user requesting `reggae` gets one genuine match and then receives hip-hop or pop songs that simply happened to have similar energy values. The user never sees this failure — the results look confident even when they aren't.

**Binary categorical matching**  
Genre and mood are scored as exact string matches. `chill` and `relaxed` are treated as completely different, even though most listeners would consider them nearly identical. `lofi` and `ambient` have no shared score credit despite being semantically close. This means users who describe their taste slightly differently from the catalog's vocabulary get structurally worse results.

**Catalog imbalance**  
Even at 10,020 songs, the distribution across 17 genres is not uniform. Genres like `pop`, `lofi`, and `rock` have many more entries than `blues`, `reggae`, or `soul`. A listener in a well-represented genre consistently gets better, more competitive recommendations than one in a sparse genre — not because the algorithm treats them differently, but because the data does.

**Western-music default**  
The catalog was generated from word banks that reflect Western popular music styles. There are no entries for K-pop, Afrobeats, flamenco, cumbia, or other global genres. The system would be useless for a large portion of the world's music listeners.

**Numeric proximity override**  
A song can "trick" the scoring formula by matching all six numeric targets closely while being from a completely wrong genre or mood. In testing, `Gym Hero` (pop, intense) ranked second for a rock listener because its energy=0.93 closely matched the rock profile's target — even though the genre and mood were wrong. This is a fundamental limitation of content-based filtering: numbers can match without the listening experience matching.

**Profile personalization cold start**  
A new registered user gets the same recommendations as a guest for their first query. Personalization only activates after sufficient history builds up. First impressions may not reflect what the system can eventually deliver.

---

## 3. Testing Results and Edge Cases Discovered

**Final result: 70 / 70 tests passing**

| File | Tests | Focus |
|---|---|---|
| `test_recommender.py` | 6 | Scoring engine correctness: OOP `Recommender`, `score_song` weights, `recommend_songs` output shape, `load_songs` integrity |
| `test_auth.py` | 32 | Full authentication lifecycle: validation, account creation, login, lockout, case-insensitive lookup, failure counter reset |
| `test_agent_tools.py` | 32 | Agent internals under adversarial inputs across 5 categories |

**Interesting discoveries from the test suite:**

*Lockout counter resets on success (test_auth.py)*  
After writing the lockout test, I realized I hadn't explicitly verified that a successful login resets the failed-attempt counter. I added `test_authenticate_failed_attempts_reset_on_success`, which confirmed the reset works — but this was a gap in the original spec that I caught only by thinking through the edge case.

*Numeric genre coercion (test_agent_tools.py)*  
`_execute_search_songs({"genre": 42}, songs)` — passing an integer as the genre. The code does `str(tool_input.get("genre", "")).strip().lower()`, which converts 42 to `"42"`, a valid non-matching string, without crashing. The test documents this implicit behavior rather than leaving it as an assumption.

*`k=0` clamping (test_agent_tools.py)*  
Requesting zero results is clamped to 1 by `max(1, min(20, int(k)))`. Without the test, someone could read that line and miss that k=0 silently becomes k=1 rather than returning an empty list.

*Empty history gives base prompt, not crash (test_agent_tools.py)*  
`_build_system_prompt({"history": []})` returns the base prompt unchanged. This is the correct behavior for a new user, but without a test it was easy to imagine a future change accidentally treating an empty list as a falsy condition and inserting a blank personalization block into every prompt.

*Special characters don't escape into the system prompt (test_agent_tools.py)*  
I tested a profile history containing `<script>alert('xss')</script>` and `'; DROP TABLE users; --` as past queries. Because these strings are just interpolated into a text system prompt (not executed as HTML or SQL), they are inert. The test confirms no crash and the strings appear verbatim as plain text — which is the correct behavior, since the prompt goes to a language model that treats it as text.

*Score tie at perfect match (discovered during manual testing)*  
Two songs that both perfectly match genre and mood and have nearly identical numeric features end up with scores of 0.97 and the ranking between them becomes effectively arbitrary. This isn't a bug — it's a documented limitation of the scoring formula when the catalog has multiple very similar entries.

---

## 4. Limitations of the Current System

**Single-writer CSV storage**  
The authentication and profile files use a read-all → update-in-memory → write-all pattern. This is safe for a single user at a time but would corrupt data under concurrent writes. It is not suitable for production use with multiple simultaneous users.

**No semantic understanding in the scoring engine**  
The scoring engine compares raw numeric features and exact string labels. It has no awareness that `lofi` and `ambient` are sonically similar, that `melancholic` and `sad` describe the same feeling, or that a user asking for "background music" likely wants low energy and high acousticness. All of that semantic translation burden falls entirely on Claude.

**Session state is not persistent**  
A browser refresh clears the Streamlit session, including the chat history shown in the UI. The persisted profile (in `user_profiles.csv`) is reloaded, but the visible conversation history in the current tab is lost. This is a Streamlit limitation.

**Profile personalization is coarse**  
The personalization context injected into the system prompt is a summary: top genre, top mood, and the text of the last 5 queries. It does not include actual songs the user liked, songs they skipped, or the scores those songs received. The system knows what the user asked for but not what they thought of the answer.

**No feedback loop**  
There is no mechanism for a user to rate a recommendation. Clicking away from a song, replaying it, or explicitly thumbing it down has no effect on future results. Recommendations improve only by inferring taste from the genre and mood of songs returned by past queries — a very indirect signal.

**Agent temperature and non-determinism**  
Claude's responses to the same query will vary between runs. The song selection is deterministic (it comes from the scoring engine), but the conversational text, the phrasing of explanations, and occasionally the parameters Claude chooses to pass to `search_songs` will differ. This makes the system harder to unit-test at the integration level.

**CSV credentials file is not production-safe**  
Passwords are hashed correctly (PBKDF2-HMAC-SHA256, 260,000 iterations, per-user salt, constant-time comparison), but storing credentials in a flat CSV file means anyone with filesystem access can read all usernames, inspect the lockout state, and potentially launch offline attacks against the hashes. A proper database with access control is necessary for any real deployment.

---

## 5. What I Would Improve with More Time

**Semantic genre and mood grouping**  
I would build a similarity graph for genres and moods — `lofi` is close to `ambient` and `chillwave`; `melancholic` is close to `sad` and `nostalgic`. When a requested genre has fewer than three songs, the scoring engine would automatically widen the search to neighbors in the graph. This would eliminate the "ran out of matches" problem without requiring a larger catalog.

**Explicit user feedback**  
A thumbs up / thumbs down button on each result card. Thumbs down lowers the weight of that genre and mood in future profile-based personalization; thumbs up raises it. This turns the profile from a passive history log into an active preference model.

**Profile-aware re-ranking**  
Currently the profile biases the Claude system prompt, which then influences the `search_songs` parameters. A more direct approach would be to run the scoring engine with the user's profile weights directly — so a user who has historically loved high-acousticness songs gets a small acousticness bonus applied at the scoring layer, not just at the language interpretation layer.

**Streaming responses**  
Claude's response currently appears all at once after the full API call completes. Streaming the response token-by-token (using `client.messages.stream()`) would make the UI feel much more responsive, especially for longer explanations.

**Catalog diversity and global music**  
Expanding the catalog to include non-Western genres and adding language as a filterable field. A user who wants music in Spanish, or specifically wants Afrobeats, should be able to say so and get meaningful results.

**Replace CSV storage with a proper database**  
SQLite would be the minimal improvement — zero infrastructure, file-based like CSV, but with proper transactions, concurrent-read safety, and SQL querying. A real deployment would use PostgreSQL with row-level security.

**Integration tests for the agent loop**  
The current test suite covers components in isolation. I would add integration tests that mock the Anthropic API response (returning a known `tool_use` block) and verify that the full `run_agent_full()` loop produces the expected structured output — catching regressions that only appear when all layers interact.

---

## 6. Scoring Formula Reference

| Feature | Weight | Maximum contribution |
|---|---|---|
| Genre match (exact) | +2.0 | 2.0 |
| Mood match (exact) | +1.5 | 1.5 |
| Energy proximity | ×1.5 | 1.5 |
| Acousticness proximity | ×1.5 | 1.5 |
| Valence proximity | ×1.0 | 1.0 |
| Danceability proximity | ×0.5 | 0.5 |
| **Maximum raw score** | | **8.0** |

Final score = raw score ÷ 8.0, normalized to [0.0, 1.0].
