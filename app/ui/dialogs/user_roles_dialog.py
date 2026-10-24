"""User Roles Management Dialog for Administrators."""
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QPushButton,
    QGroupBox,
    QWidget,
)
from sqlalchemy import select

from app.core.database import SessionFactory
from app.models import Users, OrgUnits
from app.services.rbac_service import RBACService


class UserRolesDialog(QDialog):
    """Modal dialog for Administrator to manage user system roles."""

    def __init__(
        self,
        user_id: int,
        rbac_service: Optional[RBACService] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.user_id = user_id
        self.rbac_service = rbac_service or RBACService()

        # Data placeholders
        self.user_full_name: str = ""
        self.user_email: str = ""
        self.user_code: str = ""
        self.departments: list[tuple[int, str]] = []  # (id, display_name)
        self.role_checkboxes: dict[str, QCheckBox] = {}
        self.dept_combobox: Optional[QComboBox] = None

        self._load_data()
        self._setup_ui()
        self._populate_current_roles()

    def _load_data(self) -> None:
        """Fetch user info and available departments from database."""
        with SessionFactory() as session:
            user = session.get(Users, self.user_id)
            if user:
                self.user_full_name = user.full_name
                self.user_email = user.email
                self.user_code = user.user_code or "N/A"

            orgs = list(
                session.scalars(
                    select(OrgUnits)
                    .where(OrgUnits.unit_type == "DEPARTMENT")
                    .order_by(OrgUnits.name)
                ).all()
            )
            self.departments = [(o.id, f"{o.name} ({o.code})") for o in orgs]

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"Phân quyền Tài khoản - {self.user_full_name}")
        self.setFixedSize(500, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # 1. Header Information Box
        info_box = QGroupBox("Thông tin tài khoản")
        info_box.setStyleSheet("QGroupBox { font-weight: bold; color: #1a237e; }")
        info_layout = QGridLayout(info_box)
        info_layout.setSpacing(6)

        info_layout.addWidget(QLabel("Họ và tên:"), 0, 0)
        name_val = QLabel(self.user_full_name)
        name_val.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_val, 0, 1)

        info_layout.addWidget(QLabel("Email:"), 1, 0)
        info_layout.addWidget(QLabel(self.user_email), 1, 1)

        info_layout.addWidget(QLabel("Mã định danh:"), 2, 0)
        info_layout.addWidget(QLabel(self.user_code), 2, 1)

        layout.addWidget(info_box)

        # 2. Roles Checklist Box
        roles_box = QGroupBox("Danh sách vai trò hệ thống")
        roles_box.setStyleSheet("QGroupBox { font-weight: bold; color: #1a237e; }")
        roles_layout = QVBoxLayout(roles_box)
        roles_layout.setSpacing(10)

        system_roles = self.rbac_service.get_system_roles()
        for role in system_roles:
            cb = QCheckBox(f"{role.name} ({role.code})")
            self.role_checkboxes[role.code] = cb
            roles_layout.addWidget(cb)

            if role.code == "HEAD_OF_DEPT":
                # Create companion department selector
                dept_container = QHBoxLayout()
                dept_container.setContentsMargins(24, 0, 0, 0)
                dept_label = QLabel("Bộ môn quản lý:")
                self.dept_combobox = QComboBox()
                self.dept_combobox.setEnabled(False)

                for dept_id, dept_name in self.departments:
                    self.dept_combobox.addItem(dept_name, dept_id)

                cb.toggled.connect(self.dept_combobox.setEnabled)

                dept_container.addWidget(dept_label)
                dept_container.addWidget(self.dept_combobox)
                roles_layout.addLayout(dept_container)

        layout.addWidget(roles_box)

        # Error / Feedback label
        self.feedback_label = QLabel()
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setWordWrap(True)
        self.feedback_label.hide()
        layout.addWidget(self.feedback_label)

        # 3. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Lưu phân quyền")
        self.btn_save.setStyleSheet(
            "background-color: #1a237e; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self.btn_save.clicked.connect(self._handle_save)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _populate_current_roles(self) -> None:
        """Check the boxes for the user's currently assigned roles."""
        current_roles = self.rbac_service.get_user_roles(self.user_id)
        for ur in current_roles:
            if ur.role_code in self.role_checkboxes:
                self.role_checkboxes[ur.role_code].setChecked(True)

            if ur.role_code == "HEAD_OF_DEPT" and ur.org_unit_id and self.dept_combobox:
                idx = self.dept_combobox.findData(ur.org_unit_id)
                if idx >= 0:
                    self.dept_combobox.setCurrentIndex(idx)

    def _handle_save(self) -> None:
        """Collect selected roles and save via rbac_service.sync_user_roles."""
        role_tuples = []
        for role_code, cb in self.role_checkboxes.items():
            if cb.isChecked():
                org_unit_id = None
                if role_code == "HEAD_OF_DEPT" and self.dept_combobox:
                    org_unit_id = self.dept_combobox.currentData()
                role_tuples.append((role_code, org_unit_id))

        ok, err = self.rbac_service.sync_user_roles(self.user_id, role_tuples)
        if ok:
            self.feedback_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self.feedback_label.setText("Cập nhật phân quyền người dùng thành công!")
            self.feedback_label.show()
            self.accept()
        else:
            self.feedback_label.setStyleSheet("color: #c62828; font-weight: bold;")
            self.feedback_label.setText(err or "Không thể lưu phân quyền.")
            self.feedback_label.show()
