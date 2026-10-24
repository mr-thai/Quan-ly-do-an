from dataclasses import dataclass, field
from typing import Optional, Callable
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.database import SessionFactory, transaction_scope
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    generate_reset_token,
    verify_reset_token,
    login_tracker,
)
from app.models import Users, UserRoles, Roles

# System role priority order for defaulting active role
ROLE_PRIORITY: list[str] = [
    "ADMIN",
    "OFFICE",
    "HEAD_OF_DEPT",
    "ADVISOR_ROLE",
    "STUDENT_ROLE",
]


@dataclass
class UserSession:
    """Authenticated user session information with active role switching capability."""
    user_id: int
    email: str
    full_name: str
    user_code: Optional[str] = None
    phone: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    active_role: Optional[str] = None
    active_org_unit_id: Optional[int] = None
    role_org_mapping: dict[str, Optional[int]] = field(default_factory=dict)
    _listeners: list[Callable[[str, Optional[int]], None]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        # Standardize roles to uppercase
        self.roles = [r.upper() for r in self.roles]

        # Standardize mapping keys to uppercase
        self.role_org_mapping = {k.upper(): v for k, v in self.role_org_mapping.items()}

        # Auto-determine default active_role if not provided
        if not self.active_role and self.roles:
            selected_role = None
            for candidate in ROLE_PRIORITY:
                if candidate in self.roles:
                    selected_role = candidate
                    break
            self.active_role = selected_role or self.roles[0]

        # Initialize active_org_unit_id from mapping if applicable
        if self.active_role and self.active_org_unit_id is None:
            self.active_org_unit_id = self.role_org_mapping.get(self.active_role)

    def has_role(self, role_code: str) -> bool:
        """Check if user has a specific role (case-insensitive)."""
        return role_code.upper() in self.roles

    def switch_role(
        self, new_role: str, org_unit_id: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """Switch current active role in session.
        
        Validates that user actually possesses the role.
        Triggers all registered listeners upon successful switch.
        """
        role_upper = new_role.upper()
        if role_upper not in self.roles:
            return False, f"Người dùng không sở hữu vai trò '{new_role}'."

        self.active_role = role_upper
        if org_unit_id is not None:
            self.active_org_unit_id = org_unit_id
        else:
            self.active_org_unit_id = self.role_org_mapping.get(role_upper)

        # Notify all registered listeners
        for callback in self._listeners:
            try:
                callback(self.active_role, self.active_org_unit_id)
            except Exception:
                pass  # Guard against listener failures affecting session state

        return True, None

    def add_role_switch_listener(
        self, callback: Callable[[str, Optional[int]], None]
    ) -> None:
        """Register a callback to be invoked when active_role is switched."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_role_switch_listener(
        self, callback: Callable[[str, Optional[int]], None]
    ) -> None:
        """Remove a previously registered role switch listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

class AuthService:
    """Service handling user authentication, session creation, and password life cycle."""

    def __init__(self, secret_key: Optional[str] = None):
        # Fallback secret key for token signing
        self.secret_key = secret_key or getattr(settings, "SECRET_KEY", "dacn-auth-secret-key-32bytes-min")
        self.tracker = login_tracker

    def authenticate(
        self,
        identifier: str,
        password: str,
        session: Optional[Session] = None,
    ) -> tuple[Optional[UserSession], Optional[str]]:
        """Authenticate a user by email or user_code.
        
        Returns (UserSession, None) on success, or (None, error_message) on failure.
        """
        # 1. Check if account is locked by brute-force guard
        is_locked, remaining_seconds = login_tracker.is_locked(identifier)
        if is_locked:
            return None, f"Tài khoản đang bị tạm khóa do nhập sai nhiều lần. Vui lòng thử lại sau {remaining_seconds} giây."

        # 2. Database query for user
        def _query(db: Session):
            stmt = select(Users).where(
                or_(Users.email == identifier, Users.user_code == identifier)
            )
            return db.scalar(stmt)

        if session is not None:
            user = _query(session)
            user_session, err = self._verify_user(user, identifier, password, session)
            return user_session, err
        else:
            with SessionFactory() as db:
                user = _query(db)
                return self._verify_user(user, identifier, password, db)

    def _verify_user(
        self,
        user: Optional[Users],
        identifier: str,
        password: str,
        db: Session,
    ) -> tuple[Optional[UserSession], Optional[str]]:
        if not user:
            login_tracker.record_failure(identifier)
            return None, "Tài khoản hoặc mật khẩu không chính xác."

        if not user.is_active:
            return None, "Tài khoản hiện đang bị vô hiệu hóa."

        if not verify_password(password, user.password_hash):
            is_locked, remaining = login_tracker.record_failure(identifier)
            if is_locked:
                return None, f"Mật khẩu sai. Tài khoản đã bị tạm khóa {remaining} giây do nhập sai quá 5 lần."
            return None, "Tài khoản hoặc mật khẩu không chính xác."

        # Authentication succeeded - reset attempts
        login_tracker.reset(identifier)

        # Retrieve user roles and org units
        role_stmt = select(UserRoles.role_code, UserRoles.org_unit_id).where(UserRoles.user_id == user.id)
        role_rows = db.execute(role_stmt).all()
        user_roles = [r[0] for r in role_rows]
        role_org_mapping = {r[0]: r[1] for r in role_rows}

        session_obj = UserSession(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            user_code=user.user_code,
            phone=user.phone,
            roles=user_roles,
            role_org_mapping=role_org_mapping,
        )
        return session_obj, None

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[str]]:
        """Change user password after verifying the current password."""
        if len(new_password) < 6:
            return False, "Mật khẩu mới phải có tối thiểu 6 ký tự."

        with transaction_scope(session) as db:
            user = db.get(Users, user_id)
            if not user:
                return False, "Không tìm thấy người dùng."

            if not verify_password(current_password, user.password_hash):
                return False, "Mật khẩu hiện tại không chính xác."

            user.password_hash = hash_password(new_password)
            db.flush()
            return True, None

    def request_password_reset(
        self,
        identifier: str,
        session: Optional[Session] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """Generate a reset token if user exists."""
        def _find(db: Session):
            return db.scalar(
                select(Users).where(
                    or_(Users.email == identifier, Users.user_code == identifier)
                )
            )

        if session is not None:
            user = _find(session)
        else:
            with SessionFactory() as db:
                user = _find(db)

        if not user or not user.is_active:
            return None, "Không tìm thấy tài khoản hoặc tài khoản bị vô hiệu hóa."

        token = generate_reset_token(user.email, self.secret_key, ttl_seconds=1800)
        return token, None

    def reset_password_with_token(
        self,
        token: str,
        new_password: str,
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[str]]:
        """Reset password using a valid reset token."""
        if len(new_password) < 6:
            return False, "Mật khẩu mới phải có tối thiểu 6 ký tự."

        email = verify_reset_token(token, self.secret_key)
        if not email:
            return False, "Mã khôi phục không hợp lệ hoặc đã hết hạn (quá 30 phút)."

        with transaction_scope(session) as db:
            user = db.scalar(select(Users).where(Users.email == email))
            if not user:
                return False, "Người dùng không còn tồn tại."

            user.password_hash = hash_password(new_password)
            db.flush()
            return True, None
