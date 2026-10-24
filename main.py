"""Main entrypoint for DACN desktop application."""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.dialogs.user_roles_dialog import UserRolesDialog


def main() -> None:
    app = QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.Accepted:
        session = login_dialog.session
        if session:
            role_list_str = ", ".join(session.roles) if session.roles else "Chưa có"
            msg = (
                f"Đăng nhập thành công!\n\n"
                f"• Họ và tên: {session.full_name}\n"
                f"• Email: {session.email}\n"
                f"• Mã định danh: {session.user_code}\n"
                f"• Vai trò kích hoạt: {session.active_role}\n"
                f"• Danh sách vai trò: {role_list_str}"
            )
            QMessageBox.information(None, "Xác thực Thành công", msg)

            # Nếu là Quản trị viên, mở màn hình phân quyền để thử nghiệm
            if session.has_role("ADMIN"):
                # Mở phân quyền cho tài khoản Giảng viên (ID=47, GV001)
                role_dialog = UserRolesDialog(user_id=47)
                role_dialog.exec()

    sys.exit(0)


if __name__ == "__main__":
    main()
