"""Main entrypoint for DACN desktop application."""
import sys
from PySide6.QtWidgets import QApplication
from app.ui.dialogs.login_dialog import LoginDialog


def main() -> None:
    app = QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.Accepted:
        session = login_dialog.session
        if session:
            print(f"Logged in successfully as: {session.full_name} ({session.email}) - Roles: {session.roles}")
            # MainWindow will be initialized here in subsequent stories

    sys.exit(0)


if __name__ == "__main__":
    main()
