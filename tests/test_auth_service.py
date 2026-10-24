import pytest
from sqlalchemy import select
from app.core.database import SessionFactory, transaction_scope
from app.core.security import hash_password, login_tracker
from app.models import Users, Roles, UserRoles
from app.services.auth_service import AuthService, UserSession

@pytest.fixture
def auth_service():
    return AuthService(secret_key="unit-test-secret-key-32bytes")

@pytest.fixture
def test_user():
    """Create a temporary user with roles for authentication testing."""
    user_code = "GV_TEST_AUTH_01"
    email = "gv_test_auth_01@example.com"
    password = "CorrectPassword123!"

    with transaction_scope() as session:
        # Cleanup if exists
        existing = session.scalar(select(Users).where(Users.user_code == user_code))
        if existing:
            # Delete user_roles first
            session.query(UserRoles).filter(UserRoles.user_id == existing.id).delete()
            session.delete(existing)
            session.flush()

        user = Users(
            user_code=user_code,
            email=email,
            password_hash=hash_password(password),
            full_name="Nguyễn Văn Test GV",
            is_active=1,
        )
        session.add(user)
        session.flush()

        # Assign ADVISOR role
        user_role = UserRoles(user_id=user.id, role_code="ADVISOR")
        session.add(user_role)
        session.flush()

        user_id = user.id

    yield {
        "id": user_id,
        "user_code": user_code,
        "email": email,
        "password": password,
    }

    # Teardown
    with transaction_scope() as session:
        u = session.get(Users, user_id)
        if u:
            session.query(UserRoles).filter(UserRoles.user_id == user_id).delete()
            session.delete(u)

def test_authenticate_success_email(auth_service, test_user):
    """Authenticate successfully via email."""
    session, err = auth_service.authenticate(test_user["email"], test_user["password"])
    assert err is None
    assert session is not None
    assert session.user_id == test_user["id"]
    assert session.email == test_user["email"]
    assert "ADVISOR" in session.roles

def test_authenticate_success_user_code(auth_service, test_user):
    """Authenticate successfully via user_code."""
    session, err = auth_service.authenticate(test_user["user_code"], test_user["password"])
    assert err is None
    assert session is not None
    assert session.user_code == test_user["user_code"]

def test_authenticate_wrong_password(auth_service, test_user):
    """Fail authentication on wrong password."""
    session, err = auth_service.authenticate(test_user["email"], "WrongPassword!")
    assert session is None
    assert "không chính xác" in err

def test_authenticate_lockout_trigger(auth_service, test_user):
    """Account triggers lockout after 5 consecutive wrong passwords."""
    login_tracker.reset(test_user["email"])

    for _ in range(4):
        session, err = auth_service.authenticate(test_user["email"], "WrongPass")
        assert session is None

    # 5th attempt triggers lock
    session, err = auth_service.authenticate(test_user["email"], "WrongPass")
    assert session is None
    assert "tạm khóa" in err

    # Reset tracker after test
    login_tracker.reset(test_user["email"])

def test_change_password_flow(auth_service, test_user):
    """Verify password change flow."""
    # Wrong current password fails
    ok, err = auth_service.change_password(test_user["id"], "WrongPass", "NewPassword123!")
    assert ok is False
    assert "không chính xác" in err

    # Correct current password succeeds
    ok, err = auth_service.change_password(test_user["id"], test_user["password"], "NewPassword123!")
    assert ok is True
    assert err is None

    # New password works
    session, err = auth_service.authenticate(test_user["email"], "NewPassword123!")
    assert session is not None
    assert err is None

def test_password_reset_flow(auth_service, test_user):
    """Verify forgot password and reset token flow."""
    # Generate token
    token, err = auth_service.request_password_reset(test_user["email"])
    assert err is None
    assert token is not None

    # Reset password with token
    ok, err = auth_service.reset_password_with_token(token, "BrandNewPass123!")
    assert ok is True
    assert err is None

    # Authenticate with brand new password
    session, err = auth_service.authenticate(test_user["email"], "BrandNewPass123!")
    assert session is not None
