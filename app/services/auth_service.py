from dataclasses import dataclass, field
from typing import Optional
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

@dataclass
class UserSession:
    """Authenticated user session information."""
    user_id: int
    email: str
    full_name: str
    user_code: Optional[str] = None
    phone: Optional[str] = None
    roles: list[str] = field(default_factory=list)

    def has_role(self, role_code: str) -> bool:
        return role_code.upper() in [r.upper() for r in self.roles]

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

        # Retrieve user roles
        role_stmt = select(UserRoles.role_code).where(UserRoles.user_id == user.id)
        user_roles = list(db.scalars(role_stmt).all())

        session_obj = UserSession(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            user_code=user.user_code,
            phone=user.phone,
            roles=user_roles,
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
