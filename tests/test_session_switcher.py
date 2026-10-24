import pytest
from app.services.auth_service import UserSession, AuthService
from app.core.database import transaction_scope
from app.core.security import hash_password
from app.models import Users, UserRoles, OrgUnits


def test_default_active_role_priority():
    """Default active role resolves according to system priority hierarchy."""
    # 1. HEAD_OF_DEPT beats ADVISOR_ROLE and STUDENT_ROLE
    session1 = UserSession(
        user_id=1,
        email="gv@example.com",
        full_name="GV A",
        roles=["STUDENT_ROLE", "ADVISOR_ROLE", "HEAD_OF_DEPT"],
    )
    assert session1.active_role == "HEAD_OF_DEPT"

    # 2. ADMIN beats OFFICE and HEAD_OF_DEPT
    session2 = UserSession(
        user_id=2,
        email="admin@example.com",
        full_name="Admin B",
        roles=["OFFICE", "ADMIN", "HEAD_OF_DEPT"],
    )
    assert session2.active_role == "ADMIN"

    # 3. Empty roles
    session3 = UserSession(
        user_id=3,
        email="noroles@example.com",
        full_name="User C",
        roles=[],
    )
    assert session3.active_role is None
    assert session3.active_org_unit_id is None


def test_active_role_org_unit_mapping():
    """Active org unit is automatically synchronized from role_org_mapping."""
    session = UserSession(
        user_id=1,
        email="truongbm@example.com",
        full_name="Trưởng Bộ Môn",
        roles=["ADVISOR_ROLE", "HEAD_OF_DEPT"],
        role_org_mapping={"HEAD_OF_DEPT": 10, "ADVISOR_ROLE": None},
    )
    assert session.active_role == "HEAD_OF_DEPT"
    assert session.active_org_unit_id == 10


def test_switch_role_success_and_listener():
    """Switching active role updates state and notifies registered listeners."""
    events = []

    def on_role_changed(role: str, org_id):
        events.append((role, org_id))

    session = UserSession(
        user_id=1,
        email="gv@example.com",
        full_name="GV A",
        roles=["ADVISOR_ROLE", "HEAD_OF_DEPT"],
        role_org_mapping={"HEAD_OF_DEPT": 10, "ADVISOR_ROLE": None},
    )
    session.add_role_switch_listener(on_role_changed)

    # 1. Switch to ADVISOR_ROLE
    ok, err = session.switch_role("ADVISOR_ROLE")
    assert ok is True
    assert err is None
    assert session.active_role == "ADVISOR_ROLE"
    assert session.active_org_unit_id is None
    assert len(events) == 1
    assert events[0] == ("ADVISOR_ROLE", None)

    # 2. Switch back to HEAD_OF_DEPT with custom org_unit_id
    ok, err = session.switch_role("HEAD_OF_DEPT", org_unit_id=20)
    assert ok is True
    assert err is None
    assert session.active_role == "HEAD_OF_DEPT"
    assert session.active_org_unit_id == 20
    assert len(events) == 2
    assert events[1] == ("HEAD_OF_DEPT", 20)

    # 3. Remove listener
    session.remove_role_switch_listener(on_role_changed)
    session.switch_role("ADVISOR_ROLE")
    assert len(events) == 2  # No new event added after removal


def test_switch_role_unauthorized():
    """Attempting to switch to an unpossessed role fails and preserves active role."""
    session = UserSession(
        user_id=1,
        email="gv@example.com",
        full_name="GV A",
        roles=["ADVISOR_ROLE"],
    )
    assert session.active_role == "ADVISOR_ROLE"

    ok, err = session.switch_role("ADMIN")
    assert ok is False
    assert "không sở hữu vai trò" in err
    assert session.active_role == "ADVISOR_ROLE"


def test_auth_service_integration_role_switcher():
    """AuthService populates active_role and role_org_mapping on login."""
    user_code = "GV_SWITCHER_TEST"
    email = "gv_switcher@example.com"
    org_code = "ORG_SWITCHER_TEST"

    with transaction_scope() as session:
        org = OrgUnits(code=org_code, name="Bộ môn Switcher Test", unit_type="DEPARTMENT")
        session.add(org)
        session.flush()

        user = Users(
            user_code=user_code,
            email=email,
            password_hash=hash_password("Pass123!"),
            full_name="GV Switcher",
            is_active=1,
        )
        session.add(user)
        session.flush()

        ur1 = UserRoles(user_id=user.id, role_code="ADVISOR_ROLE")
        ur2 = UserRoles(user_id=user.id, role_code="HEAD_OF_DEPT", org_unit_id=org.id)
        session.add_all([ur1, ur2])
        session.flush()

        user_id = user.id
        org_id = org.id

    auth_service = AuthService()
    user_session, err = auth_service.authenticate(email, "Pass123!")

    try:
        assert err is None
        assert user_session is not None
        assert set(user_session.roles) == {"ADVISOR_ROLE", "HEAD_OF_DEPT"}
        # Priority HEAD_OF_DEPT > ADVISOR_ROLE
        assert user_session.active_role == "HEAD_OF_DEPT"
        assert user_session.active_org_unit_id == org_id

        # Switch to ADVISOR_ROLE
        ok, err = user_session.switch_role("ADVISOR_ROLE")
        assert ok is True
        assert user_session.active_role == "ADVISOR_ROLE"
        assert user_session.active_org_unit_id is None
    finally:
        with transaction_scope() as session:
            session.query(UserRoles).filter(UserRoles.user_id == user_id).delete()
            u = session.get(Users, user_id)
            if u:
                session.delete(u)
            o = session.get(OrgUnits, org_id)
            if o:
                session.delete(o)
