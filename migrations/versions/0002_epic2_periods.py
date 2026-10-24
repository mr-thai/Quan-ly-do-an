"""Epic 2: Thesis types, steps, grading formulas, criteria, periods, milestones, quotas

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0002_epic2_periods.up.sql")


def downgrade() -> None:
    execute_sql_file("0002_epic2_periods.down.sql")
