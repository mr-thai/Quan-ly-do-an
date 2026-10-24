from dataclasses import dataclass
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.database import SessionFactory, transaction_scope
from app.models import Users, Roles, UserRoles, OrgUnits


@dataclass
class UserRoleInfo:
    """Information about a role assigned to a user."""
    id: int
    user_id: int
    role_code: str
    role_name: str
    scope: str
    org_unit_id: Optional[int] = None
    org_unit_code: Optional[str] = None
    org_unit_name: Optional[str] = None


class RBACService:
    """Service handling multi-role management and system role assignments for accounts."""

    def get_system_roles(self, session: Optional[Session] = None) -> list[Roles]:
        """Retrieve all system-scope roles defined in the system."""
        def _query(db: Session):
            return list(db.scalars(select(Roles).where(Roles.scope == "SYSTEM")).all())

        if session is not None:
            return _query(session)
        with SessionFactory() as db:
            return _query(db)

    def get_user_roles(self, user_id: int, session: Optional[Session] = None) -> list[UserRoleInfo]:
        """Retrieve all system roles assigned to a given user."""
        def _query(db: Session):
            stmt = (
                select(UserRoles, Roles, OrgUnits)
                .join(Roles, UserRoles.role_code == Roles.code)
                .outerjoin(OrgUnits, UserRoles.org_unit_id == OrgUnits.id)
                .where(UserRoles.user_id == user_id)
            )
            results = []
            for ur, r, org in db.execute(stmt):
                results.append(
                    UserRoleInfo(
                        id=ur.id,
                        user_id=ur.user_id,
                        role_code=ur.role_code,
                        role_name=r.name,
                        scope=r.scope,
                        org_unit_id=ur.org_unit_id,
                        org_unit_code=org.code if org else None,
                        org_unit_name=org.name if org else None,
                    )
                )
            return results

        if session is not None:
            return _query(session)
        with SessionFactory() as db:
            return _query(db)

    def assign_role(
        self,
        user_id: int,
        role_code: str,
        org_unit_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[str]]:
        """Assign a system role to a user.
        
        Enforces:
        - User must exist.
        - Role must exist and have scope == 'SYSTEM'.
        - If org_unit_id is provided, the org unit must exist.
        - Idempotent: returns success if already assigned.
        """
        with transaction_scope(session) as db:
            user = db.get(Users, user_id)
            if not user:
                return False, f"Không tìm thấy người dùng với ID: {user_id}."

            role = db.get(Roles, role_code)
            if not role:
                return False, f"Vai trò '{role_code}' không tồn tại trong hệ thống."

            if role.scope != "SYSTEM":
                return False, f"Vai trò '{role_code}' không thuộc phạm vi hệ thống (scope: {role.scope})."

            if org_unit_id is not None:
                org = db.get(OrgUnits, org_unit_id)
                if not org:
                    return False, f"Không tìm thấy đơn vị với ID: {org_unit_id}."

            # Check if role is already assigned with matching org_unit_id
            existing = db.scalar(
                select(UserRoles).where(
                    and_(
                        UserRoles.user_id == user_id,
                        UserRoles.role_code == role_code,
                        UserRoles.org_unit_id == org_unit_id,
                    )
                )
            )
            if existing:
                return True, None

            new_role = UserRoles(
                user_id=user_id,
                role_code=role_code,
                org_unit_id=org_unit_id,
            )
            db.add(new_role)
            db.flush()
            return True, None

    def revoke_role(
        self,
        user_id: int,
        role_code: str,
        org_unit_id: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[str]]:
        """Revoke a role from a user."""
        with transaction_scope(session) as db:
            stmt = select(UserRoles).where(
                and_(
                    UserRoles.user_id == user_id,
                    UserRoles.role_code == role_code,
                    UserRoles.org_unit_id == org_unit_id,
                )
            )
            assigned_role = db.scalar(stmt)
            if not assigned_role:
                return False, f"Người dùng chưa được gán vai trò '{role_code}'."

            db.delete(assigned_role)
            db.flush()
            return True, None

    def sync_user_roles(
        self,
        user_id: int,
        role_tuples: list[tuple[str, Optional[int]]],
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[str]]:
        """Synchronize user roles with a given list of (role_code, org_unit_id).
        
        Replaces existing system roles with the provided set atomically.
        """
        with transaction_scope(session) as db:
            user = db.get(Users, user_id)
            if not user:
                return False, f"Không tìm thấy người dùng với ID: {user_id}."

            # Pre-validate all target roles
            for role_code, org_unit_id in role_tuples:
                role = db.get(Roles, role_code)
                if not role:
                    return False, f"Vai trò '{role_code}' không tồn tại trong hệ thống."
                if role.scope != "SYSTEM":
                    return False, f"Vai trò '{role_code}' không thuộc phạm vi hệ thống (scope: {role.scope})."
                if org_unit_id is not None:
                    org = db.get(OrgUnits, org_unit_id)
                    if not org:
                        return False, f"Không tìm thấy đơn vị với ID: {org_unit_id}."

            # Remove current roles
            existing_roles = list(
                db.scalars(select(UserRoles).where(UserRoles.user_id == user_id)).all()
            )
            for ur in existing_roles:
                db.delete(ur)
            db.flush()

            # Insert new roles
            added_keys = set()
            for role_code, org_unit_id in role_tuples:
                key = (role_code, org_unit_id)
                if key in added_keys:
                    continue
                added_keys.add(key)
                db.add(UserRoles(user_id=user_id, role_code=role_code, org_unit_id=org_unit_id))

            db.flush()
            return True, None
