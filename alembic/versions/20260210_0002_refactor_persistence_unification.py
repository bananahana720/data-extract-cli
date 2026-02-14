"""Refactor persistence unification columns and indexes.

Revision ID: 20260210_0002
Revises: 20260210_0001
Create Date: 2026-02-10
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260210_0002"
down_revision = "20260210_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("request_hash", sa.String(length=128), nullable=True))
    op.add_column("jobs", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.add_column("jobs", sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("jobs", sa.Column("artifact_dir", sa.Text(), nullable=True))
    op.create_index("ix_jobs_request_hash", "jobs", ["request_hash"])
    op.create_index("ix_jobs_idempotency_key", "jobs", ["idempotency_key"])
    op.create_index(
        "ix_jobs_idempotency_hash",
        "jobs",
        ["idempotency_key", "request_hash"],
        unique=True,
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.alter_column("jobs", "attempt", server_default=None)

    op.add_column("sessions", sa.Column("artifact_dir", sa.Text(), nullable=True))
    op.add_column(
        "sessions", sa.Column("is_archived", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("sessions", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.alter_column("sessions", "is_archived", server_default=None)

    op.add_column("job_files", sa.Column("normalized_source_path", sa.Text(), nullable=True))
    op.add_column(
        "job_files", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.create_unique_constraint(
        "uq_job_files_job_norm_path",
        "job_files",
        ["job_id", "normalized_source_path"],
    )
    op.alter_column("job_files", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_job_files_job_norm_path", "job_files", type_="unique")
    op.drop_column("job_files", "retry_count")
    op.drop_column("job_files", "normalized_source_path")

    op.drop_column("sessions", "archived_at")
    op.drop_column("sessions", "is_archived")
    op.drop_column("sessions", "artifact_dir")

    op.drop_index("ix_jobs_idempotency_hash", table_name="jobs")
    op.drop_index("ix_jobs_idempotency_key", table_name="jobs")
    op.drop_index("ix_jobs_request_hash", table_name="jobs")
    op.drop_column("jobs", "artifact_dir")
    op.drop_column("jobs", "attempt")
    op.drop_column("jobs", "idempotency_key")
    op.drop_column("jobs", "request_hash")
