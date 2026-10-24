"""Epic 4: Milestone submissions, files, reviews, supervision meetings, extensions

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0004_epic4_progress.up.sql")


def downgrade() -> None:
    execute_sql_file("0004_epic4_progress.down.sql")
