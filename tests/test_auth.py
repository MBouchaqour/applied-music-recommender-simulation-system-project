"""
Test suite for the authentication module (src/auth.py).

Run from the project root:
  pytest tests/ -v

Coverage:
  - validate_username: valid, empty, too short, too long, invalid characters
  - validate_password: valid, empty, too short, missing uppercase/lowercase/digit
  - create_account:    success, duplicate (exact + case-insensitive), bad username, weak password
  - authenticate:      success, wrong password, unknown user, empty fields,
                       case-insensitive login, lockout after 5 attempts,
                       correct password still accepted before lockout,
                       failed-attempt counter resets on success
  - user_exists:       found, not found, case-insensitive
"""

import pytest
import src.auth as auth_module
from src.auth import (
    validate_username,
    validate_password,
    create_account,
    authenticate,
    user_exists,
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_MINUTES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect USERS_CSV to a fresh temp file for every test."""
    monkeypatch.setattr(auth_module, "USERS_CSV", str(tmp_path / "users.csv"))


def _make_account(username="testuser", password="Secret1234"):
    """Helper: create an account and assert it succeeded."""
    ok, msg = create_account(username, password)
    assert ok, f"Expected account creation to succeed, got: {msg}"
    return username, password


# ── validate_username ─────────────────────────────────────────────────────────

def test_validate_username_valid():
    assert validate_username("alice_99") is None


def test_validate_username_empty():
    assert validate_username("") is not None
    assert validate_username(None) is not None
    assert validate_username("   ") is not None


def test_validate_username_too_short():
    assert validate_username("ab") is not None


def test_validate_username_too_long():
    assert validate_username("a" * 31) is not None


def test_validate_username_invalid_chars():
    assert validate_username("user name") is not None   # space
    assert validate_username("user@name") is not None   # @
    assert validate_username("user.name") is not None   # dot


def test_validate_username_boundary_lengths():
    assert validate_username("abc") is None        # exactly 3
    assert validate_username("a" * 30) is None     # exactly 30


# ── validate_password ─────────────────────────────────────────────────────────

def test_validate_password_valid():
    assert validate_password("Secret1234") is None


def test_validate_password_empty():
    assert validate_password("") is not None
    assert validate_password(None) is not None


def test_validate_password_too_short():
    assert validate_password("Sh0rt") is not None       # 5 chars


def test_validate_password_no_uppercase():
    assert validate_password("secret1234") is not None


def test_validate_password_no_lowercase():
    assert validate_password("SECRET1234") is not None


def test_validate_password_no_digit():
    assert validate_password("SecretPass") is not None


def test_validate_password_exactly_min_length():
    assert validate_password("Secret1!") is None        # exactly 8 chars


# ── create_account ────────────────────────────────────────────────────────────

def test_create_account_success():
    ok, msg = create_account("newuser", "Passw0rd")
    assert ok
    assert "newuser" in msg


def test_create_account_duplicate_exact():
    create_account("alice", "Passw0rd")
    ok, msg = create_account("alice", "Passw0rd")
    assert not ok
    assert "taken" in msg.lower()


def test_create_account_duplicate_case_insensitive():
    create_account("Alice", "Passw0rd")
    ok, msg = create_account("alice", "Passw0rd")
    assert not ok
    assert "taken" in msg.lower()


def test_create_account_invalid_username():
    ok, msg = create_account("u", "Passw0rd")   # too short
    assert not ok


def test_create_account_weak_password():
    ok, msg = create_account("validuser", "weakpass")  # no uppercase, no digit
    assert not ok


def test_create_account_empty_fields():
    ok, _ = create_account("", "Passw0rd")
    assert not ok
    ok, _ = create_account("validuser", "")
    assert not ok


# ── authenticate ──────────────────────────────────────────────────────────────

def test_authenticate_success():
    _make_account("bob", "Hunter2!!a")
    ok, result = authenticate("bob", "Hunter2!!a")
    assert ok
    assert result == "bob"   # canonical username returned


def test_authenticate_wrong_password():
    _make_account("carol", "Hunter2!!a")
    ok, msg = authenticate("carol", "WrongPass1")
    assert not ok
    assert "invalid" in msg.lower()


def test_authenticate_unknown_user():
    ok, msg = authenticate("nobody", "Passw0rd1")
    assert not ok
    assert "invalid" in msg.lower()


def test_authenticate_empty_fields():
    ok, _ = authenticate("", "Passw0rd1")
    assert not ok
    ok, _ = authenticate("bob", "")
    assert not ok


def test_authenticate_case_insensitive_username():
    _make_account("Dave", "Passw0rd1")
    ok, canonical = authenticate("dave", "Passw0rd1")
    assert ok
    assert canonical == "Dave"    # original casing preserved


def test_authenticate_failed_attempts_increment():
    _make_account("eve", "Correct1a")
    for i in range(MAX_FAILED_ATTEMPTS - 1):
        ok, msg = authenticate("eve", "WrongPass1")
        assert not ok
        assert "remaining" in msg.lower()


def test_authenticate_lockout_after_max_attempts():
    _make_account("frank", "Correct1a")
    for _ in range(MAX_FAILED_ATTEMPTS):
        authenticate("frank", "WrongPass1")
    ok, msg = authenticate("frank", "Correct1a")   # correct — but locked
    assert not ok
    assert "locked" in msg.lower()


def test_authenticate_correct_before_lockout():
    """Correct password accepted even after some (but not all) failed attempts."""
    _make_account("grace", "Correct1a")
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        authenticate("grace", "WrongPass1")
    ok, result = authenticate("grace", "Correct1a")
    assert ok
    assert result == "grace"


def test_authenticate_failed_attempts_reset_on_success():
    """After a successful login, failed_attempts counter is cleared."""
    _make_account("heidi", "Correct1a")
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        authenticate("heidi", "WrongPass1")
    authenticate("heidi", "Correct1a")   # resets counter

    # Should now have full MAX_FAILED_ATTEMPTS attempts before lockout again
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        ok, _ = authenticate("heidi", "WrongPass1")
        assert not ok

    ok, result = authenticate("heidi", "Correct1a")
    assert ok
    assert result == "heidi"


# ── user_exists ───────────────────────────────────────────────────────────────

def test_user_exists_true():
    _make_account("ivan", "Passw0rd1")
    assert user_exists("ivan") is True


def test_user_exists_false():
    assert user_exists("nobody") is False


def test_user_exists_case_insensitive():
    _make_account("Judy", "Passw0rd1")
    assert user_exists("judy") is True
    assert user_exists("JUDY") is True


def test_user_exists_empty():
    assert user_exists("") is False
    assert user_exists(None) is False
