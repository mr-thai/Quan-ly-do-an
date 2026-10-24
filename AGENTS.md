# DACN — Agent Guide

## Single Source of Truth (SSOT)

- **Product Backlog & Business Requirements**:
  `/home/mr-thai/Documents/Obsidian/10 projects/11 luận văn Đồ án/Product-Backlog - Hệ thống Quản lý Luận văn, Đồ án Viện KTCN.md`
  - **Requirement**: Whenever designing architecture, database schemas, APIs, workflows, or implementing business features, you MUST read the relevant sections in the backlog document to ensure full compliance with the institute's rules and business flows.
  - **Exemption**: Purely technical, non-business operations (e.g., git commits, tool configurations, typo fixes) do not require reading this file.

## Technical Stack & Environment

- **Language**: Python (3.11+)
- **Package & Dependency Manager**: `uv` (use `uv add`, `uv run`, `uv lock`)
- **GUI Framework**: `PySide6` (Qt for Python)
- **Database**: MySQL 8.x (running in an isolated container via Docker Compose)
- **Data Access & Schema**: SQLAlchemy (ORM) + Alembic (Migrations)
- **Target Users & Scope**: Academic desktop application exclusively for Giáo vụ (Academic Affairs), Giảng viên (Lecturers / Advisors / Reviewers), and Quản trị viên (Admin).

## Conventions

- Architecture and code decisions must adhere to the roles, state transitions, and exception rules specified in the Product Backlog document.
- Use `uv run` for executing scripts, tests, and database migrations.
- Keep database credentials and local configurations isolated in `.env`.
