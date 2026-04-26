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

from agent import run_agent_full  # noqa: E402 — import after path setup

# ── Session state init ────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""

MIN_QUERY_LEN = 3
MAX_QUERY_LEN = 500

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎵 AI Music Recommender")
col_header, col_clear = st.columns([5, 1])
col_header.markdown(
    "Describe what you want to listen to — Claude searches **10,020 songs** "
    "and explains every pick."
)
if col_clear.button("Clear", help="Clear search history"):
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
    # Example button was clicked — auto-run on next render after state is set
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
                    "query": query_to_run,
                    "response": result["response"],
                    "songs": result["songs"],
                })
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
                # Clamp to [0.0, 1.0] — st.progress crashes on out-of-range values
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
