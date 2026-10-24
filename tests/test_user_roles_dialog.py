"""Automated tests for UserRolesDialog UI Component."""
import os
from unittest.mock import MagicMock
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from sqlalchemy import select
from app.core.database import transaction_scope
from app.core.security import hash_password
from app.models import Users, UserRoles, OrgUnits, Roles
from app.services.rbac_service import RBACService, UserRoleInfo
from app.ui.dialogs.user_roles_dialog import UserRolesDialog


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for offscreen tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_rbac_service():
    """Mock RBACService for pure UI unit tests."""
    service = MagicMock(spec=RBACService)
    # Mock system roles
    role_admin = Roles(code="ADMIN", name="Quản trị hệ thống", scope="SYSTEM")
    role_office = Roles(code="OFFICE", name="Giáo vụ Viện", scope="SYSTEM")
    role_head = Roles(code="HEAD_OF_DEPT", name="Trưởng bộ môn", scope="SYSTEM")
    role_adv = Roles(code="ADVISOR_ROLE", name="Giảng viên hướng dẫn", scope="SYSTEM")
    role_stu = Roles(code="STUDENT_ROLE", name="Sinh viên", scope="SYSTEM")
    service.get_system_roles.return_value = [role_admin, role_office, role_head, role_adv, role_stu]

    # Mock user roles
    service.get_user_roles.return_value = [
        UserRoleInfo(
            id=1,
            user_id=10,
            role_code="ADVISOR_ROLE",
            role_name="Giảng viên",
            scope="SYSTEM",
        )
    ]
    service.sync_user_roles.return_value = (True, None)
    return service


def test_user_roles_dialog_init_and_precheck(qapp, mock_rbac_service, monkeypatch):
    """Dialog loads user info and checks pre-assigned roles."""
    # Patch _load_data to avoid DB query in unit test
    def fake_load_data(self):
        self.user_full_name = "Nguyễn Văn Giảng Viên"
        self.user_email = "gv_test@school.edu.vn"
        self.user_code = "GV123"
        self.departments = [(1, "Bộ môn CNPM (CNPM)"), (2, "Bộ môn Mạng (MMT)")]

    monkeypatch.setattr(UserRolesDialog, "_load_data", fake_load_data)

    dialog = UserRolesDialog(user_id=10, rbac_service=mock_rbac_service)

    assert "Nguyễn Văn Giảng Viên" in dialog.windowTitle()
    assert dialog.role_checkboxes["ADVISOR_ROLE"].isChecked() is True
    assert dialog.role_checkboxes["ADMIN"].isChecked() is False
    assert dialog.role_checkboxes["HEAD_OF_DEPT"].isChecked() is False

    # Check companion department combobox
    assert dialog.dept_combobox is not None
    assert dialog.dept_combobox.isEnabled() is False


def test_user_roles_dialog_toggle_head_of_dept(qapp, mock_rbac_service, monkeypatch):
    """Checking HEAD_OF_DEPT enables the department selector combobox."""
    def fake_load_data(self):
        self.user_full_name = "Trưởng BM Test"
        self.user_email = "head_test@school.edu.vn"
        self.user_code = "HEAD123"
        self.departments = [(1, "Bộ môn CNPM (CNPM)")]

    monkeypatch.setattr(UserRolesDialog, "_load_data", fake_load_data)

    dialog = UserRolesDialog(user_id=10, rbac_service=mock_rbac_service)
    cb_head = dialog.role_checkboxes["HEAD_OF_DEPT"]

    # Toggle checked
    cb_head.setChecked(True)
    assert dialog.dept_combobox.isEnabled() is True

    # Toggle unchecked
    cb_head.setChecked(False)
    assert dialog.dept_combobox.isEnabled() is False


def test_user_roles_dialog_save_success(qapp, mock_rbac_service, monkeypatch):
    """Saving roles sends selected roles to rbac_service and accepts dialog."""
    def fake_load_data(self):
        self.user_full_name = "GV A"
        self.user_email = "gva@school.edu.vn"
        self.user_code = "GVA01"
        self.departments = [(10, "Bộ môn KTPM (KTPM)")]

    monkeypatch.setattr(UserRolesDialog, "_load_data", fake_load_data)

    dialog = UserRolesDialog(user_id=10, rbac_service=mock_rbac_service)

    # Check HEAD_OF_DEPT and ADMIN
    dialog.role_checkboxes["ADMIN"].setChecked(True)
    dialog.role_checkboxes["HEAD_OF_DEPT"].setChecked(True)
    dialog.dept_combobox.setCurrentIndex(0)

    dialog._handle_save()

    mock_rbac_service.sync_user_roles.assert_called_once()
    args = mock_rbac_service.sync_user_roles.call_args[0]
    assert args[0] == 10
    role_tuples = args[1]

    # Verify both ADMIN and HEAD_OF_DEPT are in role_tuples
    codes = [r[0] for r in role_tuples]
    assert "ADMIN" in codes
    assert "HEAD_OF_DEPT" in codes
    head_tuple = next(r for r in role_tuples if r[0] == "HEAD_OF_DEPT")
    assert head_tuple[1] == 10


def test_user_roles_dialog_save_error(qapp, mock_rbac_service, monkeypatch):
    """When rbac_service returns error, dialog displays feedback without closing."""
    def fake_load_data(self):
        self.user_full_name = "GV Error"
        self.user_email = "gverr@school.edu.vn"
        self.user_code = "GVERR"
        self.departments = []

    monkeypatch.setattr(UserRolesDialog, "_load_data", fake_load_data)
    mock_rbac_service.sync_user_roles.return_value = (False, "Lỗi kết nối CSDL hoặc dữ liệu không hợp lệ.")

    dialog = UserRolesDialog(user_id=10, rbac_service=mock_rbac_service)
    dialog.role_checkboxes["ADMIN"].setChecked(True)

    dialog._handle_save()

    assert not dialog.feedback_label.isHidden()
    assert "Lỗi kết nối CSDL" in dialog.feedback_label.text()


# =============================================================================
# Integration Test with Real Database
# =============================================================================

def test_user_roles_dialog_real_db_integration(qapp):
    """Full integration test loading and modifying user roles in MySQL."""
    email = "test_ui_roles_dialog@example.com"
    org_code = "DEPT_UI_TEST_01"

    with transaction_scope() as session:
        # 1. Org Unit
        org = session.scalar(select(OrgUnits).where(OrgUnits.code == org_code))
        if not org:
            org = OrgUnits(code=org_code, name="Bộ môn UI Test", unit_type="DEPARTMENT")
            session.add(org)
            session.flush()

        # 2. User
        user = Users(
            email=email,
            user_code="GV_UI_ROLES",
            password_hash=hash_password("Pass123!"),
            full_name="Nguyễn Văn UI Test",
            is_active=1,
        )
        session.add(user)
        session.flush()

        # Assign initial role: STUDENT_ROLE
        session.add(UserRoles(user_id=user.id, role_code="STUDENT_ROLE"))
        session.flush()

        user_id = user.id
        org_id = org.id

    try:
        # Open dialog with real RBACService and database
        dialog = UserRolesDialog(user_id=user_id)
        assert dialog.role_checkboxes["STUDENT_ROLE"].isChecked() is True
        assert dialog.role_checkboxes["ADMIN"].isChecked() is False

        # Modify: Uncheck STUDENT_ROLE, Check ADVISOR_ROLE and HEAD_OF_DEPT
        dialog.role_checkboxes["STUDENT_ROLE"].setChecked(False)
        dialog.role_checkboxes["ADVISOR_ROLE"].setChecked(True)
        dialog.role_checkboxes["HEAD_OF_DEPT"].setChecked(True)

        idx = dialog.dept_combobox.findData(org_id)
        if idx >= 0:
            dialog.dept_combobox.setCurrentIndex(idx)

        dialog._handle_save()

        # Verify database updated
        rbac = RBACService()
        updated_roles = rbac.get_user_roles(user_id)
        role_codes = {r.role_code for r in updated_roles}
        assert role_codes == {"ADVISOR_ROLE", "HEAD_OF_DEPT"}

        head_role = next(r for r in updated_roles if r.role_code == "HEAD_OF_DEPT")
        assert head_role.org_unit_id == org_id
    finally:
        with transaction_scope() as session:
            session.query(UserRoles).filter(UserRoles.user_id == user_id).delete()
            u = session.get(Users, user_id)
            if u:
                session.delete(u)
            o = session.get(OrgUnits, org_id)
            if o:
                session.delete(o)
