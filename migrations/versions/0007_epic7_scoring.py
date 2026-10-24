"""Epic 7: Scores, grade results, history, defense minutes, revisions, appeals

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0007_epic7_scoring.up.sql")


def downgrade() -> None:
    execute_sql_file("0007_epic7_scoring.down.sql")
