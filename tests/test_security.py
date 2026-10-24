import time
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    generate_reset_token,
    verify_reset_token,
    LoginAttemptTracker,
)

def test_password_hashing_and_verification():
    """Verify password hashing is salted and verifies correctly."""
    plain = "P@ssword123!"
    hashed1 = hash_password(plain)
    hashed2 = hash_password(plain)

    # Salt ensures different hashes for the same password
    assert hashed1 != hashed2
    assert hashed1.startswith("pbkdf2_sha256$")

    # Correct password succeeds
    assert verify_password(plain, hashed1) is True
    assert verify_password(plain, hashed2) is True

    # Incorrect password fails
    assert verify_password("WrongPassword!", hashed1) is False

def test_reset_token_validity_and_expiration():
    """Verify reset token generation, verification, and expiration."""
    secret = "test-secret-key-12345"
    email = "sinhvien@example.com"

    # Valid token within TTL
    token = generate_reset_token(email, secret_key=secret, ttl_seconds=1800)
    assert verify_reset_token(token, secret_key=secret) == email

    # Tampered token fails
    tampered = token[:-4] + "abcd"
    assert verify_reset_token(tampered, secret_key=secret) is None

    # Expired token fails (1 second TTL)
    short_token = generate_reset_token(email, secret_key=secret, ttl_seconds=1)
    time.sleep(1.1)
    assert verify_reset_token(short_token, secret_key=secret) is None

def test_login_attempt_tracker_lockout():
    """Verify account lockout after 5 consecutive failed attempts."""
    tracker = LoginAttemptTracker(max_attempts=5, lockout_seconds=2)
    user_id = "GV001"

    # 4 failed attempts should not lock account
    for _ in range(4):
        is_locked, _ = tracker.record_failure(user_id)
        assert is_locked is False
        assert tracker.is_locked(user_id)[0] is False

    # 5th failed attempt triggers lock
    is_locked, remaining = tracker.record_failure(user_id)
    assert is_locked is True
    assert remaining > 0

    # While locked, is_locked returns True
    locked, rem = tracker.is_locked(user_id)
    assert locked is True
    assert rem > 0

    # Wait for lockout expiration
    time.sleep(2.1)
    locked_after, _ = tracker.is_locked(user_id)
    assert locked_after is False

    # Success resets tracker
    tracker.record_failure(user_id)
    tracker.reset(user_id)
    assert tracker.is_locked(user_id)[0] is False
