"""Login Dialog component for user authentication."""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
)

from app.services.auth_service import AuthService, UserSession
from app.ui.dialogs.reset_password_dialog import ResetPasswordDialog


class LoginDialog(QDialog):
    """Modal dialog for logging into the DACN system."""

    def __init__(self, auth_service: Optional[AuthService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self.session: Optional[UserSession] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Đăng nhập - Quản lý Luận văn, Đồ án Viện KTCN")
        self.setFixedSize(420, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(32, 28, 32, 28)

        # Title & Subtitle
        title_label = QLabel("HỆ THỐNG QUẢN LÝ LUẬN VĂN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a237e;")
        layout.addWidget(title_label)

        sub_label = QLabel("Đăng nhập tài khoản để tiếp tục")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet("font-size: 12px; color: #616161; margin-bottom: 8px;")
        layout.addWidget(sub_label)

        # Identifier field
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Email hoặc Mã SV / Mã Cán bộ")
        self.identifier_input.setStyleSheet("padding: 8px; font-size: 13px;")
        self.identifier_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.identifier_input)

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 8px; font-size: 13px;")
        self.password_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.password_input)

        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # Login button
        self.login_btn = QPushButton("Đăng nhập")
        self.login_btn.setDefault(True)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; padding: 9px; font-size: 14px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1565c0; }"
            "QPushButton:disabled { background-color: #90caf9; }"
        )
        self.login_btn.clicked.connect(self._handle_login)
        layout.addWidget(self.login_btn)

        # Bottom actions (Forgot password & Exit)
        bottom_layout = QHBoxLayout()
        self.forgot_btn = QPushButton("Quên mật khẩu?")
        self.forgot_btn.setFlat(True)
        self.forgot_btn.setStyleSheet("color: #1976d2; text-decoration: underline; font-size: 12px;")
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.clicked.connect(self._handle_forgot_password)
        bottom_layout.addWidget(self.forgot_btn)

        bottom_layout.addStretch()

        self.exit_btn = QPushButton("Thoát")
        self.exit_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        self.exit_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.exit_btn)

        layout.addLayout(bottom_layout)

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()

    def _handle_login(self) -> None:
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text()

        if not identifier or not password:
            self._show_error("Vui lòng nhập đầy đủ tài khoản và mật khẩu.")
            return

        self.login_btn.setEnabled(False)
        self.error_label.hide()

        try:
            result = self.auth_service.authenticate(identifier, password)
            if isinstance(result, tuple):
                session, err = result
            else:
                session, err = result, None if result else "Mã định danh hoặc mật khẩu không chính xác."

            if session:
                self.session = session
                self.accept()
            else:
                self._show_error(err or "Mã định danh hoặc mật khẩu không chính xác.")
        finally:
            self.login_btn.setEnabled(True)

    def _handle_forgot_password(self) -> None:
        dialog = ResetPasswordDialog(auth_service=self.auth_service, parent=self)
        dialog.exec()
