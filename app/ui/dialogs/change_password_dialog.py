"""Dialog for changing password when logged in."""
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


class ChangePasswordDialog(QDialog):
    """Dialog allowing authenticated users to change their password."""

    def __init__(self, user_id: int, auth_service: Optional[AuthService] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.auth_service = auth_service or AuthService()

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Đổi mật khẩu - DACN")
        self.setFixedSize(380, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("ĐỔI MẬT KHẨU")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a237e;")
        layout.addWidget(title)

        self.old_password_input = QLineEdit()
        self.old_password_input.setPlaceholderText("Mật khẩu hiện tại")
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.old_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Mật khẩu mới (tối thiểu 8 ký tự)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Xác nhận mật khẩu mới")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("padding: 7px; font-size: 13px;")
        layout.addWidget(self.confirm_password_input)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Lưu thay đổi")
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; padding: 8px; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1565c0; }"
        )
        self.save_btn.clicked.connect(self._handle_change_password)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Hủy bỏ")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()

    def _handle_change_password(self) -> None:
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not old_password or not new_password or not confirm_password:
            self._show_error("Vui lòng nhập đầy đủ các trường.")
            return

        if len(new_password) < 8:
            self._show_error("Mật khẩu mới phải có ít nhất 8 ký tự.")
            return

        if new_password != confirm_password:
            self._show_error("Mật khẩu xác nhận không khớp.")
            return

        if old_password == new_password:
            self._show_error("Mật khẩu mới không được trùng mật khẩu cũ.")
            return

        success = self.auth_service.change_password(self.user_id, old_password, new_password)
        if success:
            QMessageBox.information(self, "Thành công", "Mật khẩu đã được thay đổi thành công.")
            self.accept()
        else:
            self._show_error("Mật khẩu hiện tại không chính xác.")
