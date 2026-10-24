"""Epic 8: Archive records, document templates

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0008_epic8_archive.up.sql")


def downgrade() -> None:
    execute_sql_file("0008_epic8_archive.down.sql")
