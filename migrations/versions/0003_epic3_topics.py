"""Epic 3: Files, topic states, transitions, topics, history, members, change requests

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0003_epic3_topics.up.sql")


def downgrade() -> None:
    execute_sql_file("0003_epic3_topics.down.sql")
