import pytest
from sqlalchemy import select
from app.core.database import transaction_scope
from app.core.security import hash_password
from app.models import Users, Roles, UserRoles, OrgUnits
from app.services.rbac_service import RBACService


@pytest.fixture
def rbac_service():
    return RBACService()


@pytest.fixture
def test_data():
    """Create a temporary test user and test org unit for RBAC testing."""
    user_code = "USER_TEST_RBAC_01"
    email = "user_test_rbac_01@example.com"
    org_code = "CNTT_TEST_RBAC"

    with transaction_scope() as session:
        # Cleanup user if exists
        existing_user = session.scalar(select(Users).where(Users.user_code == user_code))
        if existing_user:
            session.query(UserRoles).filter(UserRoles.user_id == existing_user.id).delete()
            session.delete(existing_user)
            session.flush()

        # Cleanup org unit if exists
        existing_org = session.scalar(select(OrgUnits).where(OrgUnits.code == org_code))
        if existing_org:
            session.delete(existing_org)
            session.flush()

        # Create test org unit
        org = OrgUnits(
            code=org_code,
            name="Bộ môn Kỹ thuật Phần mềm (Test)",
            unit_type="DEPARTMENT",
        )
        session.add(org)
        session.flush()

        # Create test user
        user = Users(
            user_code=user_code,
            email=email,
            password_hash=hash_password("Password123!"),
            full_name="Trần Văn RBAC",
            is_active=1,
        )
        session.add(user)
        session.flush()

        user_id = user.id
        org_id = org.id

    yield {
        "user_id": user_id,
        "user_code": user_code,
        "email": email,
        "org_id": org_id,
        "org_code": org_code,
    }

    # Teardown
    with transaction_scope() as session:
        u = session.get(Users, user_id)
        if u:
            session.query(UserRoles).filter(UserRoles.user_id == user_id).delete()
            session.delete(u)
        o = session.get(OrgUnits, org_id)
        if o:
            session.delete(o)


def test_get_system_roles(rbac_service):
    """Retrieve all available roles that have SYSTEM scope."""
    roles = rbac_service.get_system_roles()
    assert len(roles) >= 5
    role_codes = [r.code for r in roles]
    assert "ADMIN" in role_codes
    assert "OFFICE" in role_codes
    assert "HEAD_OF_DEPT" in role_codes
    assert "ADVISOR_ROLE" in role_codes
    assert "STUDENT_ROLE" in role_codes
    # TOPIC or COMMITTEE roles should not be in system roles
    assert "ADVISOR" not in role_codes
    assert "CHAIR" not in role_codes


def test_assign_and_get_user_roles(rbac_service, test_data):
    """Assign system roles with and without org_unit and verify."""
    user_id = test_data["user_id"]
    org_id = test_data["org_id"]

    # 1. Assign OFFICE role (no org unit)
    ok, err = rbac_service.assign_role(user_id=user_id, role_code="OFFICE")
    assert ok is True
    assert err is None

    # 2. Assign HEAD_OF_DEPT role (with org unit)
    ok, err = rbac_service.assign_role(user_id=user_id, role_code="HEAD_OF_DEPT", org_unit_id=org_id)
    assert ok is True
    assert err is None

    # 3. Retrieve user roles
    roles = rbac_service.get_user_roles(user_id)
    assert len(roles) == 2

    office_role = next(r for r in roles if r.role_code == "OFFICE")
    assert office_role.org_unit_id is None
    assert office_role.scope == "SYSTEM"

    dept_role = next(r for r in roles if r.role_code == "HEAD_OF_DEPT")
    assert dept_role.org_unit_id == org_id
    assert dept_role.org_unit_code == test_data["org_code"]


def test_assign_role_idempotent(rbac_service, test_data):
    """Assigning the same role twice is safe and returns success."""
    user_id = test_data["user_id"]
    ok1, err1 = rbac_service.assign_role(user_id=user_id, role_code="OFFICE")
    assert ok1 is True
    assert err1 is None

    ok2, err2 = rbac_service.assign_role(user_id=user_id, role_code="OFFICE")
    assert ok2 is True
    assert err2 is None

    roles = rbac_service.get_user_roles(user_id)
    assert len([r for r in roles if r.role_code == "OFFICE"]) == 1


def test_assign_role_invalid_user(rbac_service):
    """Assigning role to non-existent user returns error."""
    ok, err = rbac_service.assign_role(user_id=9999999, role_code="OFFICE")
    assert ok is False
    assert "Không tìm thấy người dùng" in err


def test_assign_role_non_system_or_missing(rbac_service, test_data):
    """Assigning role that does not exist or has non-SYSTEM scope returns error."""
    user_id = test_data["user_id"]

    # Missing role
    ok, err = rbac_service.assign_role(user_id=user_id, role_code="NON_EXISTENT_ROLE")
    assert ok is False
    assert "không tồn tại" in err

    # Topic-scoped role (ADVISOR) cannot be assigned as system role
    ok, err = rbac_service.assign_role(user_id=user_id, role_code="ADVISOR")
    assert ok is False
    assert "không thuộc phạm vi hệ thống" in err


def test_assign_role_invalid_org_unit(rbac_service, test_data):
    """Assigning role with non-existent org_unit_id returns error."""
    user_id = test_data["user_id"]
    ok, err = rbac_service.assign_role(user_id=user_id, role_code="HEAD_OF_DEPT", org_unit_id=999999)
    assert ok is False
    assert "Không tìm thấy đơn vị" in err


def test_revoke_role(rbac_service, test_data):
    """Revoking an assigned role removes it; revoking unassigned returns error."""
    user_id = test_data["user_id"]
    org_id = test_data["org_id"]

    rbac_service.assign_role(user_id=user_id, role_code="HEAD_OF_DEPT", org_unit_id=org_id)
    assert len(rbac_service.get_user_roles(user_id)) == 1

    # Revoke with wrong org_unit_id
    ok, err = rbac_service.revoke_role(user_id=user_id, role_code="HEAD_OF_DEPT", org_unit_id=None)
    assert ok is False
    assert "chưa được gán" in err

    # Revoke with correct org_unit_id
    ok, err = rbac_service.revoke_role(user_id=user_id, role_code="HEAD_OF_DEPT", org_unit_id=org_id)
    assert ok is True
    assert err is None
    assert len(rbac_service.get_user_roles(user_id)) == 0


def test_sync_user_roles(rbac_service, test_data):
    """Synchronize user roles with a new list replacing old roles."""
    user_id = test_data["user_id"]
    org_id = test_data["org_id"]

    # Initially assign OFFICE
    rbac_service.assign_role(user_id=user_id, role_code="OFFICE")
    assert len(rbac_service.get_user_roles(user_id)) == 1

    # Sync to [ADVISOR_ROLE, HEAD_OF_DEPT]
    ok, err = rbac_service.sync_user_roles(
        user_id=user_id,
        role_tuples=[
            ("ADVISOR_ROLE", None),
            ("HEAD_OF_DEPT", org_id),
        ],
    )
    assert ok is True
    assert err is None

    roles = rbac_service.get_user_roles(user_id)
    assert len(roles) == 2
    codes = {r.role_code for r in roles}
    assert codes == {"ADVISOR_ROLE", "HEAD_OF_DEPT"}

    # Sync to empty list removes all roles
    ok, err = rbac_service.sync_user_roles(user_id=user_id, role_tuples=[])
    assert ok is True
    assert len(rbac_service.get_user_roles(user_id)) == 0
