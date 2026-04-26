"""
Streamlit web interface for the AI Music Recommender.

Run from the project root:
    streamlit run src/app.py
"""

import os
import sys
import time

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

from agent import run_agent_full                    # noqa: E402
from auth import create_account, authenticate, validate_username, validate_password  # noqa: E402
from profiles import load_profile, upsert_profile   # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_QUERY_LEN   = 3
MAX_QUERY_LEN   = 500
SESSION_TIMEOUT = 3600   # seconds (1 hour)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "authenticated": False,
    "is_guest":      False,
    "auth_user":     None,
    "auth_time":     None,
    "history":       [],
    "pending_query": "",
    "profile_cache": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_session(username: str | None, is_guest: bool) -> None:
    """Populate auth session state after login or guest entry."""
    st.session_state.authenticated = not is_guest
    st.session_state.is_guest      = is_guest
    st.session_state.auth_user     = username
    st.session_state.auth_time     = time.time()
    st.session_state.history       = []
    st.session_state.profile_cache = (
        None if is_guest else load_profile(username)
    )


def _clear_session() -> None:
    """Wipe auth state (logout / session expiry)."""
    for key in list(_DEFAULTS.keys()):
        st.session_state[key] = _DEFAULTS[key]


def _is_active_session() -> bool:
    return st.session_state.authenticated or st.session_state.is_guest


def _check_session_timeout() -> bool:
    """Return True (and clear session) if the session has expired."""
    t = st.session_state.auth_time
    if t and (time.time() - t > SESSION_TIMEOUT):
        _clear_session()
        return True
    return False


# ── Auth page ─────────────────────────────────────────────────────────────────

def _render_auth_page() -> None:
    st.title("🎵 AI Music Recommender")
    st.markdown("Your AI-powered music discovery tool. Sign in to get started.")
    st.divider()

    tab_login, tab_register, tab_guest = st.tabs(
        ["Log In", "Create Account", "Continue as Guest"]
    )

    # ── Login tab ──────────────────────────────────────────────────────────────
    with tab_login:
        st.subheader("Welcome back")
        with st.form("login_form"):
            lu = st.text_input("Username", max_chars=30)
            lp = st.text_input("Password", type="password")
            login_submit = st.form_submit_button(
                "Log In", type="primary", use_container_width=True
            )

        if login_submit:
            if not lu or not lp:
                st.error("Please enter both username and password.")
            else:
                success, result = authenticate(lu, lp)
                if success:
                    _set_session(result, is_guest=False)
                    st.rerun()
                else:
                    st.error(result)

    # ── Register tab ───────────────────────────────────────────────────────────
    with tab_register:
        st.subheader("Create a free account")

        # Live username feedback
        reg_user = st.text_input(
            "Username", max_chars=30, key="reg_username",
            help="3–30 characters: letters, numbers, _ or -"
        )
        un_err = validate_username(reg_user) if reg_user else None
        if reg_user and un_err:
            st.caption(f"⚠️ {un_err}")
        elif reg_user:
            st.caption("✅ Username looks good")

        # Live password feedback
        reg_pass = st.text_input(
            "Password", type="password", key="reg_password",
            help="Min 8 chars · uppercase · lowercase · number"
        )
        pw_err = validate_password(reg_pass) if reg_pass else None
        if reg_pass and pw_err:
            st.caption(f"⚠️ {pw_err}")
        elif reg_pass:
            st.caption("✅ Password meets requirements")

        reg_confirm = st.text_input(
            "Confirm password", type="password", key="reg_confirm"
        )

        if st.button("Create Account", type="primary", use_container_width=True):
            # Validate all fields before hitting auth module
            if not reg_user or not reg_pass or not reg_confirm:
                st.error("All fields are required.")
            elif reg_pass != reg_confirm:
                st.error("Passwords do not match.")
            else:
                success, msg = create_account(reg_user, reg_pass)
                if success:
                    # Auto-login after registration
                    _set_session(reg_user.strip(), is_guest=False)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ── Guest tab ──────────────────────────────────────────────────────────────
    with tab_guest:
        st.subheader("Try without an account")
        st.info(
            "You can continue as a guest, but registering will help provide "
            "more precise and personalized recommendations based on your "
            "listening history and preferences."
        )
        if st.button("Continue as Guest", type="primary", use_container_width=True):
            _set_session(None, is_guest=True)
            st.rerun()


# ── Sidebar (shown only in main app) ──────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        if st.session_state.is_guest:
            st.markdown("### 👤 Guest")
            st.warning(
                "You're browsing as a guest. "
                "Create an account to save your history and get personalized picks."
            )
            if st.button("Create Account", use_container_width=True, type="primary"):
                _clear_session()
                st.rerun()
            if st.button("Log In", use_container_width=True):
                _clear_session()
                st.rerun()

        else:
            username = st.session_state.auth_user
            profile  = st.session_state.profile_cache

            st.markdown(f"### 👤 {username}")
            if st.button("Log Out", use_container_width=True):
                _clear_session()
                st.rerun()

            st.divider()

            if profile and int(profile.get("query_count", 0)) > 0:
                c1, c2 = st.columns(2)
                c1.metric("Searches",    profile["query_count"])
                c2.metric("Top Genre",   profile["top_genre"] or "—")
                st.caption(f"Favourite mood: **{profile['top_mood'] or '—'}**")
                st.caption(f"Member since: {str(profile['first_seen'])[:10]}")

                if profile.get("history"):
                    with st.expander("Recent searches", expanded=False):
                        for entry in reversed(profile["history"][-10:]):
                            ts = str(entry.get("timestamp", ""))[:10]
                            genre_tag = (
                                f" *({entry['genre']})*" if entry.get("genre") else ""
                            )
                            st.markdown(f"- `{ts}` &nbsp; {entry['query']}{genre_tag}")
            else:
                st.caption("No searches yet — your stats will appear here.")

        st.divider()
        # Session time remaining
        t = st.session_state.auth_time
        if t:
            remaining = max(0, int(SESSION_TIMEOUT - (time.time() - t)))
            mins = remaining // 60
            st.caption(f"Session expires in {mins} min.")


# ── Main app ──────────────────────────────────────────────────────────────────

def _render_main_app() -> None:
    # Guest banner
    if st.session_state.is_guest:
        st.info(
            "You can continue as a guest, but registering will help provide "
            "more precise and personalized recommendations. "
            "Use the sidebar to create a free account."
        )

    # Header
    col_title, col_clear = st.columns([5, 1])
    col_title.title("🎵 AI Music Recommender")
    if col_clear.button("Clear", help="Clear this session's search history"):
        st.session_state.history = []
        st.rerun()

    st.markdown(
        "Describe what you want to listen to — Claude searches **10,020 songs** "
        "and explains every pick."
    )
    st.divider()

    # Example buttons
    st.caption("Try an example:")
    c1, c2, c3 = st.columns(3)
    for col, label in {
        c1: "Calm lofi for studying",
        c2: "High energy gym music",
        c3: "Melancholic acoustic songs",
    }.items():
        if col.button(label, use_container_width=True):
            st.session_state.pending_query = label

    # Search form
    with st.form("search_form", clear_on_submit=True):
        user_input = st.text_input(
            "Your request",
            value=st.session_state.pending_query,
            placeholder="e.g. something upbeat and happy for a road trip...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "🔍  Search", use_container_width=True, type="primary"
        )

    # Resolve query to run
    query_to_run = ""
    if submitted and user_input.strip():
        query_to_run = user_input.strip()
        st.session_state.pending_query = ""
    elif st.session_state.pending_query and not submitted:
        query_to_run = st.session_state.pending_query
        st.session_state.pending_query = ""

    # Run the agent
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
                    # Persist profile for registered users only
                    if st.session_state.authenticated and result["songs"]:
                        updated = upsert_profile(
                            st.session_state.auth_user,
                            query_to_run,
                            result["songs"],
                        )
                        st.session_state.profile_cache = updated

                except EnvironmentError as exc:
                    st.error(str(exc))
                except RuntimeError as exc:
                    st.warning(str(exc))
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    # Results
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
                        st.markdown(
                            f"**#{rank} &nbsp; {song['title']}**"
                            f" &nbsp;—&nbsp; {song['artist']}"
                        )
                        st.caption(
                            f"Genre: &nbsp;`{song['genre']}`"
                            f"&emsp;Mood: &nbsp;`{song['mood']}`"
                        )
                    with right:
                        st.metric("Score", f"{song['confidence_score']:.2f}")
                    safe_score = max(0.0, min(1.0, float(song["confidence_score"])))
                    st.progress(safe_score)
                    with st.expander("Why this song?"):
                        for reason in song["why"].split(" | "):
                            st.write(f"• {reason}")

        elif not entry["songs"] and entry["response"]:
            st.info(
                "No catalog matches found for this request. "
                "Try a different genre or mood."
            )

    if not st.session_state.history:
        st.markdown(
            "<div style='text-align:center;color:#888;padding:3rem 0'>"
            "Your recommendations will appear here."
            "</div>",
            unsafe_allow_html=True,
        )


# ── Entry point ───────────────────────────────────────────────────────────────

# Session timeout check — must run before rendering anything
if _check_session_timeout():
    st.warning("Your session has expired. Please log in again.")

if not _is_active_session():
    _render_auth_page()
    st.stop()

_render_sidebar()
_render_main_app()
