"""Automated tests for PySide6 UI Dialogs."""
import os
from unittest.mock import MagicMock, patch
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from app.services.auth_service import AuthService, UserSession
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.dialogs.change_password_dialog import ChangePasswordDialog
from app.ui.dialogs.reset_password_dialog import ResetPasswordDialog


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_auth_service():
    """Create a mock AuthService for isolated UI testing."""
    service = MagicMock(spec=AuthService)
    service.tracker = MagicMock()
    service.tracker.is_locked.return_value = False
    return service


def test_login_dialog_empty_fields(qapp, mock_auth_service):
    """Test validation when fields are submitted empty."""
    dialog = LoginDialog(auth_service=mock_auth_service)
    dialog.identifier_input.setText("")
    dialog.password_input.setText("")

    dialog._handle_login()

    assert not dialog.error_label.isHidden()
    assert "Vui lòng nhập đầy đủ" in dialog.error_label.text()
    assert dialog.session is None
    mock_auth_service.authenticate.assert_not_called()


def test_login_dialog_account_locked(qapp, mock_auth_service):
    """Test login attempt when account is currently locked."""
    mock_auth_service.authenticate.return_value = (None, "Tài khoản đang bị tạm khóa 15 phút do nhập sai nhiều lần.")

    dialog = LoginDialog(auth_service=mock_auth_service)
    dialog.identifier_input.setText("locked@school.edu.vn")
    dialog.password_input.setText("Password123")

    dialog._handle_login()

    assert not dialog.error_label.isHidden()
    assert "tạm khóa" in dialog.error_label.text()
    assert dialog.session is None
    mock_auth_service.authenticate.assert_called_once_with("locked@school.edu.vn", "Password123")


def test_login_dialog_auth_failed(qapp, mock_auth_service):
    """Test login failure on incorrect credentials."""
    mock_auth_service.authenticate.return_value = (None, "Mã định danh hoặc mật khẩu không chính xác.")

    dialog = LoginDialog(auth_service=mock_auth_service)
    dialog.identifier_input.setText("gv01@school.edu.vn")
    dialog.password_input.setText("WrongPass")

    dialog._handle_login()

    assert not dialog.error_label.isHidden()
    assert "không chính xác" in dialog.error_label.text()
    assert dialog.session is None


def test_login_dialog_auth_success(qapp, mock_auth_service):
    """Test successful authentication sets session and accepts dialog."""
    dummy_session = UserSession(
        user_id=1,
        email="gv01@school.edu.vn",
        full_name="Nguyễn Văn A",
        user_code="GV001",
        phone=None,
        roles=["ADVISOR"],
    )
    mock_auth_service.authenticate.return_value = (dummy_session, None)

    dialog = LoginDialog(auth_service=mock_auth_service)
    dialog.identifier_input.setText("gv01@school.edu.vn")
    dialog.password_input.setText("CorrectPass123")

    dialog._handle_login()

    assert dialog.session == dummy_session
    assert dialog.result() == 1  # QDialog.Accepted is 1


def test_change_password_dialog_validation(qapp, mock_auth_service):
    """Test input validations in ChangePasswordDialog."""
    dialog = ChangePasswordDialog(user_id=1, auth_service=mock_auth_service)

    # 1. Short password (< 8 chars)
    dialog.old_password_input.setText("oldpass")
    dialog.new_password_input.setText("short")
    dialog.confirm_password_input.setText("short")
    dialog._handle_change_password()
    assert "ít nhất 8 ký tự" in dialog.error_label.text()

    # 2. Mismatched confirm password
    dialog.new_password_input.setText("newpass123")
    dialog.confirm_password_input.setText("differentpass")
    dialog._handle_change_password()
    assert "không khớp" in dialog.error_label.text()

    # 3. Duplicate old and new password
    dialog.old_password_input.setText("samepassword")
    dialog.new_password_input.setText("samepassword")
    dialog.confirm_password_input.setText("samepassword")
    dialog._handle_change_password()
    assert "không được trùng" in dialog.error_label.text()


@patch("PySide6.QtWidgets.QMessageBox.information")
def test_change_password_dialog_success(mock_msgbox, qapp, mock_auth_service):
    """Test successful password change in dialog."""
    mock_auth_service.change_password.return_value = True

    dialog = ChangePasswordDialog(user_id=1, auth_service=mock_auth_service)
    dialog.old_password_input.setText("oldpassword123")
    dialog.new_password_input.setText("newpassword456")
    dialog.confirm_password_input.setText("newpassword456")

    dialog._handle_change_password()

    mock_auth_service.change_password.assert_called_once_with(1, "oldpassword123", "newpassword456")
    assert dialog.result() == 1  # Accepted


def test_reset_password_dialog_request_token(qapp, mock_auth_service):
    """Test requesting token in ResetPasswordDialog."""
    mock_auth_service.request_password_reset.return_value = "mocked-token-xyz"

    dialog = ResetPasswordDialog(auth_service=mock_auth_service)
    dialog.email_input.setText("user@school.edu.vn")
    dialog._handle_request_token()

    mock_auth_service.request_password_reset.assert_called_once_with("user@school.edu.vn")
    assert dialog.token_input.text() == "mocked-token-xyz"
    assert not dialog.status_label.isHidden()
