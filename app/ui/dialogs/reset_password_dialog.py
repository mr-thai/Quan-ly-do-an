"""Dialog for requesting and completing password reset."""
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

from app.services.auth_service import AuthService


class ResetPasswordDialog(QDialog):
    """Dialog allowing users to reset their password using a temporary token."""

    def __init__(self, auth_service: Optional[AuthService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Khôi phục mật khẩu - DACN")
        self.setFixedSize(400, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("KHÔI PHỤC MẬT KHẨU")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a237e;")
        layout.addWidget(title)

        desc = QLabel("Nhập email để nhận mã xác nhận, sau đó nhập mã và mật khẩu mới.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #616161;")
        layout.addWidget(desc)

        # Step 1: Email and request button
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email đăng ký tài khoản")
        self.email_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.email_input)

        self.request_token_btn = QPushButton("Gửi yêu cầu khôi phục")
        self.request_token_btn.setStyleSheet("padding: 7px; font-weight: bold;")
        self.request_token_btn.clicked.connect(self._handle_request_token)
        layout.addWidget(self.request_token_btn)

        # Step 2: Token and new password
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Mã khôi phục (nhận qua email)")
        self.token_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.token_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Mật khẩu mới (tối thiểu 8 ký tự)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.new_password_input)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 12px;")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Đổi mật khẩu")
        self.submit_btn.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; padding: 8px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1b5e20; }"
        )
        self.submit_btn.clicked.connect(self._handle_reset_password)
        btn_layout.addWidget(self.submit_btn)

        self.close_btn = QPushButton("Đóng")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _handle_request_token(self) -> None:
        email = self.email_input.text().strip()
        if not email:
            self._show_message("Vui lòng nhập email.", is_error=True)
            return

        token = self.auth_service.request_password_reset(email)
        if token:
            self._show_message(f"Mã xác nhận đã sinh (thử nghiệm): {token[:12]}... (Hết hạn sau 30 phút).", is_error=False)
            self.token_input.setText(token)
        else:
            self._show_message("Email không tồn tại hoặc tài khoản bị vô hiệu hóa.", is_error=True)

    def _handle_reset_password(self) -> None:
        email = self.email_input.text().strip()
        token = self.token_input.text().strip()
        new_password = self.new_password_input.text()

        if not email or not token or not new_password:
            self._show_message("Vui lòng điền đầy đủ các thông tin.", is_error=True)
            return

        if len(new_password) < 8:
            self._show_message("Mật khẩu mới phải có ít nhất 8 ký tự.", is_error=True)
            return

        success = self.auth_service.reset_password_with_token(email, token, new_password)
        if success:
            QMessageBox.information(self, "Thành công", "Mật khẩu đã được đặt lại thành công. Bạn có thể đăng nhập ngay.")
            self.accept()
        else:
            self._show_message("Mã xác thực không hợp lệ hoặc đã quá hạn 30 phút.", is_error=True)

    def _show_message(self, message: str, is_error: bool) -> None:
        color = "#d32f2f" if is_error else "#2e7d32"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.status_label.setText(message)
        self.status_label.show()
