import base64
import hashlib
import hmac
import json
import secrets
import time
from threading import Lock

# PBKDF2 parameters (NIST SP 800-63B compliant)
ALGORITHM = "sha256"
ITERATIONS = 600_000
SALT_BYTES = 16

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(ALGORITHM, password.encode("utf-8"), salt, ITERATIONS)
    salt_hex = salt.hex()
    hash_hex = derived.hex()
    return f"pbkdf2_{ALGORITHM}${ITERATIONS}${salt_hex}${hash_hex}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash string."""
    try:
        parts = hashed.split("$")
        if len(parts) != 4 or not parts[0].startswith("pbkdf2_"):
            return False
        algo = parts[0].replace("pbkdf2_", "")
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        candidate_hash = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False

def generate_reset_token(identifier: str, secret_key: str, ttl_seconds: int = 1800) -> str:
    """Generate a tamper-proof HMAC-signed password reset token with TTL."""
    payload = {
        "sub": identifier,
        "exp": time.time() + ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii").rstrip("=")

    signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"

def verify_reset_token(token: str, secret_key: str) -> str | None:
    """Verify token signature and expiration. Returns identifier if valid, else None."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts

        # Verify HMAC signature
        expected_sig = hmac.new(
            secret_key.encode("utf-8"),
            payload_b64.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Decode payload
        padding = "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        if time.time() >= payload.get("exp", 0):
            return None

        return payload.get("sub")
    except Exception:
        return None

class LoginAttemptTracker:
    """Thread-safe in-memory login attempt counter and lockout guard."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = Lock()

    def record_failure(self, identifier: str) -> tuple[bool, int]:
        """Record a failed attempt.
        
        Returns (is_locked, remaining_lockout_seconds).
        """
        now = time.time()
        with self._lock:
            # If already locked, check remaining time
            locked_until = self._locked_until.get(identifier, 0)
            if now < locked_until:
                return True, int(locked_until - now)

            # Record failure timestamp
            attempts = self._attempts.setdefault(identifier, [])
            # Purge attempts older than lockout duration window
            attempts = [t for t in attempts if now - t < self.lockout_seconds]
            attempts.append(now)
            self._attempts[identifier] = attempts

            # Check if threshold reached
            if len(attempts) >= self.max_attempts:
                lock_end = now + self.lockout_seconds
                self._locked_until[identifier] = lock_end
                self._attempts.pop(identifier, None)
                return True, self.lockout_seconds

            return False, 0

    def is_locked(self, identifier: str) -> tuple[bool, int]:
        """Check if an identifier is currently locked out."""
        now = time.time()
        with self._lock:
            locked_until = self._locked_until.get(identifier, 0)
            if now < locked_until:
                return True, int(locked_until - now)
            # Lock has expired
            if identifier in self._locked_until:
                del self._locked_until[identifier]
            return False, 0

    def reset(self, identifier: str) -> None:
        """Reset attempts on successful login."""
        with self._lock:
            self._attempts.pop(identifier, None)
            self._locked_until.pop(identifier, None)

# Default global instance
login_tracker = LoginAttemptTracker(max_attempts=5, lockout_seconds=900)
