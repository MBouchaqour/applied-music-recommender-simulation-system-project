# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**MoodMatch 1.0**

---

## 2. Intended Use  

MoodMatch 1.0 suggests the top 5 songs from a small catalog that best match a user's stated taste. You tell it your preferred genre, mood, energy level, and how acoustic you like your music, and it scores every song in the catalog to find your closest matches.

It assumes the user already knows what they want and can express it in simple terms like "I want chill lofi with low energy." It does not learn from listening history, it does not ask follow-up questions, and it does not know anything about lyrics or cultural context.

This is a classroom exploration tool, not a real product. It is designed to demonstrate how content-based filtering works and to make the scoring logic visible and explainable, not to serve real users at scale.

---

## 3. How the Model Works  

Imagine you are a music store clerk and a customer walks in and says: "I want something lofi, chill, calm, and acoustic." You then walk through every album in the store and give each one a score based on how well it matches that description. The album with the highest score is your top recommendation.

That is exactly what MoodMatch 1.0 does.

Each song in the catalog has six measured properties: genre, mood, energy level, how acoustic it sounds, its emotional positivity (valence), and how danceable it is. The user provides the same six preferences. The system compares the two side by side for every song and adds up a score.

Genre and mood are the biggest factors. If a song's genre matches exactly, it gets a large bonus. Same for mood. These two signals together represent more than 40% of the maximum possible score, because genre and mood are the clearest expressions of what a listener actually wants.

The remaining score comes from how close the song's numbers are to the user's targets. A song with energy=0.35 scores higher for a user who asked for energy=0.38 than a song with energy=0.90. The closer the number, the more points it earns. Acousticness and energy are weighted the most among the numeric features since they most strongly define a listening experience. Valence and danceability are tiebreakers — they barely change the ranking on their own.

All the points are added up and divided by the maximum possible score to produce a final number between 0 and 1. The top 5 songs with the highest scores are returned, along with an explanation of exactly which features contributed.

The main change from the starter logic was adding acousticness, valence, and danceability as scored features, expanding the catalog from 10 to 20 songs, and building a visual score bar in the output so the rankings are easy to read at a glance.

---

## 4. Data  

The catalog has 20 songs stored in `data/songs.csv`. The original starter project came with 10 songs. I expanded it to 20 to cover a wider range of genres and moods and make the recommender more interesting to test.

The 20 songs span 17 genres: lofi, pop, rock, ambient, jazz, synthwave, hip-hop, blues, classical, edm, country, r&b, metal, reggae, dream pop, soul, and indie pop. The moods covered include: chill, happy, intense, relaxed, focused, moody, confident, melancholic, peaceful, euphoric, nostalgic, romantic, angry, and joyful.

However, the distribution is uneven. Most genres have exactly one song. Lofi is the only genre with three songs, which gives lofi listeners a clear advantage — they get better, more competitive results than listeners of genres like metal, blues, or classical, where there is only one song to match against.

The dataset also reflects a particular kind of listener. It leans toward Western popular music styles and does not include genres like K-pop, Afrobeats, flamenco, or traditional folk music. There are no songs in languages other than English. This means the system would not serve listeners outside of these musical traditions at all.

---

## 5. Strengths  

The system works best for users who have a clear, well-represented taste. The **Chill Lofi** profile is the strongest example. That listener got three songs that genuinely matched their genre and mood in the top 3, with scores above 0.79. The recommendations felt right — quiet, acoustic, low-energy tracks that a late-night study session listener would actually enjoy.

The scoring logic also does a good job separating very different profiles from each other. When I ran Chill Lofi and High-Energy Pop side by side, the results shared zero songs in common. The system correctly understood that "calm and acoustic" and "loud and danceable" are opposite asks, and it ranked songs accordingly.

Another strength is transparency. Every recommendation comes with a "Why?" breakdown showing exactly which features contributed to the score and by how much. This is something real apps like Spotify do not show you. A user can look at the output and immediately understand why a song ranked where it did, which makes the system easy to debug and easy to learn from.

Finally, the visual score bar makes the confidence level of each recommendation obvious at a glance. A score of 0.97 with a nearly full bar tells you the system is very confident. A score of 0.48 with a half-empty bar tells you it ran out of good matches. That honesty about uncertainty is a real strength for a teaching tool.

---

## 6. Limitations and Bias 

The most significant weakness I discovered is that the system creates a **genre filter bubble** for underrepresented genres. Because genre carries the highest weight (+2.0 out of a maximum of 8.0), a user requesting `rock` gets one strong match — `Storm Runner` — and then the system has nowhere to go, falling back to songs like `hip-hop` and `synthwave` that share no genre or mood with the request. This means roughly 75% of the top-5 results for a rock listener are structurally irrelevant, not because the scoring logic failed, but because the catalog only contains one rock song. In a real product, this would silently frustrate an entire category of users who would see low-quality recommendations and never know why. A fairer system would either balance the catalog to have equal genre representation, or detect when a genre is sparse and widen the search to semantically similar genres rather than defaulting to numeric-only scoring.

---

## 7. Evaluation  

I tested three distinct user profiles by running the CLI and reading the ranked top-5 output for each: a **Chill Lofi** listener (low energy, acoustic, chill mood), a **High-Energy Pop** listener (high energy, danceability, happy mood), and a **Deep Intense Rock** listener (high energy, low acousticness, intense mood). For each profile I checked whether the top result made intuitive sense, whether the score bar reflected a real quality gap between ranks, and whether the "Why?" explanations matched the formula weights.

The result that surprised me most was in the **Chill Lofi** profile — `Library Rain` and `Midnight Coding` both scored 0.97 and were nearly impossible to separate, even though they are different songs by different artists. This revealed that when genre and mood both match perfectly and the numeric features are close, the system cannot meaningfully differentiate between candidates and the final ranking becomes almost arbitrary. I also did not expect `Velvet Underground` (soul, melancholic) to appear in the Chill Lofi top 5 at all — it has no genre or mood match, but its numeric features (energy=0.44, acousticness=0.67) are close enough to the lofi targets that it outranks songs from more fitting genres, exposing how numeric proximity can override semantic fit when a genre is underrepresented.

---

## 8. Future Work  

First, I would expand the catalog. Right now most genres only have one song. If you ask for rock, the system runs out of good matches almost immediately. More songs per genre would fix that.

Second, I would group similar genres and moods together. Right now `chill` and `relaxed` are treated as completely different. But they feel almost the same. Grouping them would help users who describe their taste slightly differently still get good results.

Third, I would add a diversity rule. Right now the top 5 can all be from the same genre. That gets repetitive fast. A simple rule like "no more than 2 songs from the same genre in the top 5" would make results feel more interesting.

Fourth, I would let the profile update over time. If a user skips a song, that should mean something. Right now the system ignores all feedback. Even a simple "thumbs down lowers that genre's weight" would make it feel smarter.

Finally, I would add a warning when a genre is sparse. Instead of quietly handing back unrelated songs, the system should say "we only found 1 rock song — here are some similar-sounding alternatives." Honesty about limitations is better than silent bad recommendations.

---

## 9. Personal Reflection  

**Chill Lofi vs. High-Energy Pop**

These two profiles are opposites in almost every way — one wants quiet, acoustic, low-energy music to focus, and the other wants loud, danceable, upbeat music to hype up. When I ran both, the top results were completely different, which is what you'd expect. What was interesting is *why* they diverged: the lofi profile rewarded songs that felt "soft" on every dial (low energy, high acousticness, calm mood), while the pop profile rewarded songs that were loud and danceable. The system correctly pulled them apart — but only because the catalog happened to have songs that matched each extreme cleanly. If the catalog were smaller or more uniform, both profiles would have gotten the same recommendations, which would be a sign the system had stopped working.

**Chill Lofi vs. Deep Intense Rock**

Both profiles want a specific genre and mood, but lofi has 3 songs in the catalog while rock only has 1. This is where the system behaved most differently. The lofi profile got a confident, well-matched top 3. The rock profile got one great match at #1 and then basically gave up — it started recommending hip-hop and synthwave songs just because their energy numbers happened to be high. In plain terms: the system ran out of rock songs to recommend, but instead of telling you that, it quietly handed you unrelated music. It's like asking a store for apples and, when they run out, being handed oranges because they're also round.

**High-Energy Pop vs. Deep Intense Rock**

Both profiles want high energy, but pop wants "happy" and rock wants "intense." You would think these are very different vibes — and a human DJ would treat them completely differently. But the system kept recommending `Gym Hero` (pop, intense) to the rock profile as the #2 pick. Why? Because `Gym Hero` has energy=0.93, which is almost identical to what the rock profile asked for, and the mood bonus for "intense" fired. The genre was wrong (pop, not rock), but the numbers were too close to ignore. This is a good example of a song "tricking" the system by matching the numeric signals without matching the actual vibe — exactly the kind of case where a content-based recommender breaks down and human taste judgment would do better.

