"""Epic 5: Final submissions, files, eligibility, similarity checks

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from migrations.helpers import execute_sql_file

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    execute_sql_file("0005_epic5_final_submission.up.sql")


def downgrade() -> None:
    execute_sql_file("0005_epic5_final_submission.down.sql")
