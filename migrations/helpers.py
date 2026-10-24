import re
from pathlib import Path
from alembic import op

SQL_DIR = Path(__file__).resolve().parent / "sql"


def execute_sql_file(filename: str) -> None:
    """Execute raw SQL statements from a file in migrations/sql/ sequentially."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Migration SQL file not found: {file_path}")

    raw_content = file_path.read_text(encoding="utf-8")

    # Group lines into complete SQL statements ending with ;
    statements = []
    current_stmt_lines = []

    for line in raw_content.splitlines():
        trimmed = line.strip()
        # Skip pure comment lines
        if trimmed.startswith("--"):
            continue
        current_stmt_lines.append(line)
        if trimmed.endswith(";"):
            full_stmt = "\n".join(current_stmt_lines).strip()
            # Remove trailing semicolon
            if full_stmt.endswith(";"):
                full_stmt = full_stmt[:-1].strip()
            if full_stmt:
                statements.append(full_stmt)
            current_stmt_lines = []

    # In case the last statement didn't have a trailing semicolon
    if current_stmt_lines:
        remainder = "\n".join(current_stmt_lines).strip()
        if remainder:
            statements.append(remainder)

    for stmt in statements:
        if stmt:
            op.execute(stmt)
