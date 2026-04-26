"""
Streamlit web interface for the AI Music Recommender.

Run from the project root:
    streamlit run src/app.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Music Recommender",
    page_icon="🎵",
    layout="centered",
)

# ── API key guard ─────────────────────────────────────────────────────────────
if not os.getenv("ANTHROPIC_API_KEY"):
    st.error(
        "**ANTHROPIC_API_KEY not found.** "
        "Create a `.env` file in the project root with your key and restart."
    )
    st.stop()

from agent import run_agent_full        # noqa: E402
from profiles import load_profile, upsert_profile  # noqa: E402

# ── Session state init ────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""
if "username" not in st.session_state:
    st.session_state.username = ""
if "profile_cache" not in st.session_state:
    st.session_state.profile_cache = None

MIN_QUERY_LEN = 3
MAX_QUERY_LEN = 500

# ── Sidebar — user profile ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Your Profile")

    raw_name = st.text_input(
        "Name",
        value=st.session_state.username,
        placeholder="Enter your name to save history...",
        max_chars=50,
    ).strip()

    # Refresh cached profile when the name changes
    if raw_name != st.session_state.username:
        st.session_state.username = raw_name
        st.session_state.profile_cache = load_profile(raw_name) if raw_name else None

    username = st.session_state.username
    profile  = st.session_state.profile_cache

    if username:
        if profile:
            st.success(f"Welcome back, **{username}**!")
            c1, c2 = st.columns(2)
            c1.metric("Searches",  profile["query_count"])
            c2.metric("Top Genre", profile["top_genre"] or "—")
            st.caption(f"Favourite mood: **{profile['top_mood'] or '—'}**")
            st.caption(f"Member since: {profile['first_seen'][:10]}")

            if profile["history"]:
                with st.expander("Recent searches", expanded=False):
                    for entry in reversed(profile["history"][-10:]):
                        ts = entry.get("timestamp", "")[:10]
                        st.markdown(
                            f"- `{ts}` &nbsp; {entry['query']}"
                            + (f" *(_{entry['genre']}_)*" if entry.get("genre") else "")
                        )
        else:
            st.info(f"Hi **{username}**! Your profile will be created on your first search.")
    else:
        st.caption("Enter a name to save your preferences and search history across sessions.")

    st.divider()
    st.caption("Profiles are stored locally in `data/user_profiles.csv`.")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎵 AI Music Recommender")
col_header, col_clear = st.columns([5, 1])
col_header.markdown(
    "Describe what you want to listen to — Claude searches **10,020 songs** "
    "and explains every pick."
)
if col_clear.button("Clear", help="Clear this session's search history"):
    st.session_state.history = []
    st.rerun()
st.divider()

# ── Example query buttons ─────────────────────────────────────────────────────
st.caption("Try an example:")
col1, col2, col3 = st.columns(3)
examples = {
    col1: "Calm lofi for studying",
    col2: "High energy gym music",
    col3: "Melancholic acoustic songs",
}
for col, label in examples.items():
    if col.button(label, use_container_width=True):
        st.session_state.pending_query = label

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("search_form", clear_on_submit=True):
    user_input = st.text_input(
        "Your request",
        value=st.session_state.pending_query,
        placeholder="e.g. something upbeat and happy for a road trip...",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("🔍  Search", use_container_width=True, type="primary")

# Determine what query to run this render
query_to_run = ""
if submitted and user_input.strip():
    query_to_run = user_input.strip()
    st.session_state.pending_query = ""
elif st.session_state.pending_query and not submitted:
    query_to_run = st.session_state.pending_query
    st.session_state.pending_query = ""

# ── Run the agent ─────────────────────────────────────────────────────────────
if query_to_run:
    if len(query_to_run) < MIN_QUERY_LEN:
        st.warning(f"Please enter at least {MIN_QUERY_LEN} characters.")
    elif len(query_to_run) > MAX_QUERY_LEN:
        st.warning(f"Query too long — please keep it under {MAX_QUERY_LEN} characters.")
    else:
        with st.spinner("Searching the catalog..."):
            try:
                result = run_agent_full(query_to_run)
                st.session_state.history.insert(0, {
                    "query":    query_to_run,
                    "response": result["response"],
                    "songs":    result["songs"],
                })

                # Persist to user_profiles.csv if user gave their name
                if username and result["songs"]:
                    updated = upsert_profile(username, query_to_run, result["songs"])
                    st.session_state.profile_cache = updated

            except EnvironmentError as e:
                st.error(str(e))
            except RuntimeError as e:
                st.warning(str(e))
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ── Results ───────────────────────────────────────────────────────────────────
for idx, entry in enumerate(st.session_state.history):
    if idx > 0:
        st.divider()

    with st.chat_message("user"):
        st.write(entry["query"])

    with st.chat_message("assistant"):
        st.write(entry["response"])

    if entry["songs"]:
        st.markdown("#### Recommendations")
        for rank, song in enumerate(entry["songs"], 1):
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**#{rank} &nbsp; {song['title']}** &nbsp;—&nbsp; {song['artist']}")
                    st.caption(
                        f"Genre: &nbsp;`{song['genre']}`"
                        f"&emsp;Mood: &nbsp;`{song['mood']}`"
                    )
                with right:
                    st.metric(label="Score", value=f"{song['confidence_score']:.2f}")
                safe_score = max(0.0, min(1.0, float(song["confidence_score"])))
                st.progress(safe_score)
                with st.expander("Why this song?"):
                    for reason in song["why"].split(" | "):
                        st.write(f"• {reason}")
    elif not entry["songs"] and entry["response"]:
        st.info("No catalog matches found for this request. Try a different genre or mood.")

# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.history:
    st.markdown(
        "<div style='text-align:center; color:#888; padding: 3rem 0;'>"
        "Your recommendations will appear here."
        "</div>",
        unsafe_allow_html=True,
    )
