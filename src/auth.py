"""
Authentication module — account creation, login, and session management.

Credentials stored in data/users.csv (gitignored).
Passwords hashed with PBKDF2-HMAC-SHA256 + per-user random salt.

NOTE: For production, replace CSV storage with a proper database and use
      a battle-tested framework like Flask-Login or Django auth.
"""

import csv
import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

USERS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "users.csv",
)

FIELDNAMES = [
    "username",
    "password_hash",
    "salt",
    "created_at",
    "failed_attempts",
    "locked_until",
]

SESSION_TIMEOUT_SECONDS = 3600   # 1 hour
MAX_FAILED_ATTEMPTS     = 5
LOCKOUT_MINUTES         = 15
MIN_PASSWORD_LEN        = 8

# Letters, numbers, underscore, hyphen — 3 to 30 chars
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256 with 260,000 iterations."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260_000,
    ).hex()


def _read_users() -> dict:
    if not os.path.exists(USERS_CSV):
        return {}
    users = {}
    with open(USERS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            users[row["username"]] = row
    return users


def _write_users(users: dict) -> None:
    os.makedirs(os.path.dirname(USERS_CSV), exist_ok=True)
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(users.values())


# ── Validation (pure — no I/O) ────────────────────────────────────────────────

def validate_username(username) -> str | None:
    """Return an error message string, or None if the username is valid."""
    if not username or not str(username).strip():
        return "Username is required."
    if not _USERNAME_RE.match(str(username).strip()):
        return (
            "Username must be 3–30 characters and contain only "
            "letters, numbers, underscores, or hyphens."
        )
    return None


def validate_password(password) -> str | None:
    """Return an error message string, or None if the password is valid."""
    if not password:
        return "Password is required."
    pw = str(password)
    if len(pw) < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters long."
    if not any(c.isupper() for c in pw):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in pw):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in pw):
        return "Password must contain at least one number."
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def create_account(username: str, password: str) -> tuple[bool, str]:
    """
    Create a new account.

    Returns (True, success_message) or (False, user-friendly error message).
    The caller must verify that password == confirm_password before calling.
    """
    username = str(username).strip() if username else ""

    err = validate_username(username)
    if err:
        return False, err

    err = validate_password(password)
    if err:
        return False, err

    users = _read_users()

    # Case-insensitive duplicate check
    if any(k.lower() == username.lower() for k in users):
        return False, "That username is already taken. Please choose another."

    salt = secrets.token_hex(32)
    users[username] = {
        "username":        username,
        "password_hash":   _hash_password(password, salt),
        "salt":            salt,
        "created_at":      _now_str(),
        "failed_attempts": "0",
        "locked_until":    "",
    }

    try:
        _write_users(users)
    except OSError as exc:
        logger.error("Failed to write users CSV: %s", exc)
        return False, "Account creation failed due to a storage error. Please try again."

    logger.info("Account created: %r", username)
    return True, f"Welcome, {username}! Your account has been created."


def authenticate(username: str, password: str) -> tuple[bool, str]:
    """
    Authenticate credentials.

    Returns:
        (True,  canonical_username)   — on success; use the returned string
                                        as the authoritative username.
        (False, user-friendly message) — on any failure.

    Never reveals whether a username exists to prevent enumeration.
    """
    if not username or not password:
        return False, "Please enter both username and password."

    username = str(username).strip()
    users = _read_users()

    # Case-insensitive lookup
    key = next((k for k in users if k.lower() == username.lower()), None)
    if key is None:
        logger.warning("Login attempt for unknown user: %r", username)
        return False, "Invalid username or password."

    user = dict(users[key])

    # Lockout check
    locked_str = user.get("locked_until", "")
    if locked_str:
        try:
            lock_dt = datetime.strptime(
                locked_str, "%Y-%m-%d %H:%M:%S UTC"
            ).replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < lock_dt:
                mins = int((lock_dt - datetime.now(timezone.utc)).total_seconds() / 60) + 1
                return False, f"Account temporarily locked. Try again in {mins} minute(s)."
            # Lockout has expired — reset the counter
            user["failed_attempts"] = "0"
            user["locked_until"] = ""
        except ValueError:
            user["locked_until"] = ""

    # Constant-time password comparison prevents timing attacks
    expected = _hash_password(password, user["salt"])
    if not secrets.compare_digest(expected, user["password_hash"]):
        failed = int(user.get("failed_attempts", 0)) + 1
        user["failed_attempts"] = str(failed)

        if failed >= MAX_FAILED_ATTEMPTS:
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            user["locked_until"] = lock_until.strftime("%Y-%m-%d %H:%M:%S UTC")
            users[key] = user
            _write_users(users)
            logger.warning("Account locked after %d attempts: %r", failed, key)
            return False, (
                f"Too many failed attempts. "
                f"Account locked for {LOCKOUT_MINUTES} minutes."
            )

        users[key] = user
        _write_users(users)
        remaining = MAX_FAILED_ATTEMPTS - failed
        logger.warning("Failed login for %r (%d/%d)", key, failed, MAX_FAILED_ATTEMPTS)
        return False, (
            f"Invalid username or password. "
            f"{remaining} attempt(s) remaining before lockout."
        )

    # Success — reset failure counter
    user["failed_attempts"] = "0"
    user["locked_until"] = ""
    users[key] = user
    _write_users(users)
    logger.info("Successful login: %r", key)
    return True, key   # canonical username returned as message on success


def user_exists(username: str) -> bool:
    """Case-insensitive existence check."""
    if not username:
        return False
    users = _read_users()
    return any(k.lower() == str(username).strip().lower() for k in users)
