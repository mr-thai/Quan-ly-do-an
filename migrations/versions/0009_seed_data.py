"""Seed data: Lookup categories, states, transitions, thesis types, rules, sample formulas

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0009_seed_data.up.sql")


def downgrade() -> None:
    execute_sql_file("0009_seed_data.down.sql")
