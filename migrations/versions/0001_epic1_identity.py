"""Epic 1: Identity, roles, profiles, notifications, audit log

Revision ID: 0001
Revises: 
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0001_epic1_identity.up.sql")


def downgrade() -> None:
    execute_sql_file("0001_epic1_identity.down.sql")
