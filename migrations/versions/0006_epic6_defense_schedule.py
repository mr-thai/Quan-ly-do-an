"""Epic 6: Rules, reviews, committees, rooms, slots, defense sessions, participants

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0006_epic6_defense_schedule.up.sql")


def downgrade() -> None:
    execute_sql_file("0006_epic6_defense_schedule.down.sql")
