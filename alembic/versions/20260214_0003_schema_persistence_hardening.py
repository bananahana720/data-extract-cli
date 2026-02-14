"""Add dispatch/sync/projection persistence fields and composite indexes.

Revision ID: 20260214_0003
Revises: 20260210_0002
Create Date: 2026-02-14
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260214_0003"
down_revision = "20260210_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("dispatch_payload", sa.Text(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "dispatch_state",
            sa.String(length=32),
            nullable=False,
            server_default="pending_dispatch",
        ),
    )
    op.add_column(
        "jobs",
        sa.Column("dispatch_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("jobs", sa.Column("dispatch_last_error", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("dispatch_last_attempt_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("dispatch_next_attempt_at", sa.DateTime(), nullable=True))

    op.add_column(
        "jobs",
        sa.Column(
            "artifact_sync_state",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "jobs",
        sa.Column("artifact_sync_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("jobs", sa.Column("artifact_sync_error", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("artifact_last_synced_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("result_checksum", sa.String(length=128), nullable=True))

    op.add_column("sessions", sa.Column("projection_source", sa.String(length=64), nullable=True))
    op.add_column("sessions", sa.Column("projection_error", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("last_reconciled_at", sa.DateTime(), nullable=True))

    op.create_index(
        "ix_jobs_dispatch_state_next_attempt_at",
        "jobs",
        ["dispatch_state", "dispatch_next_attempt_at"],
    )
    op.create_index(
        "ix_jobs_artifact_sync_state_updated_at",
        "jobs",
        ["artifact_sync_state", "updated_at"],
    )
    op.create_index(
        "ix_job_events_job_id_event_time",
        "job_events",
        ["job_id", "event_time"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_events_job_id_event_time", table_name="job_events")
    op.drop_index("ix_jobs_artifact_sync_state_updated_at", table_name="jobs")
    op.drop_index("ix_jobs_dispatch_state_next_attempt_at", table_name="jobs")

    op.drop_column("sessions", "last_reconciled_at")
    op.drop_column("sessions", "projection_error")
    op.drop_column("sessions", "projection_source")

    op.drop_column("jobs", "result_checksum")
    op.drop_column("jobs", "artifact_last_synced_at")
    op.drop_column("jobs", "artifact_sync_error")
    op.drop_column("jobs", "artifact_sync_attempts")
    op.drop_column("jobs", "artifact_sync_state")
    op.drop_column("jobs", "dispatch_next_attempt_at")
    op.drop_column("jobs", "dispatch_last_attempt_at")
    op.drop_column("jobs", "dispatch_last_error")
    op.drop_column("jobs", "dispatch_attempts")
    op.drop_column("jobs", "dispatch_state")
    op.drop_column("jobs", "dispatch_payload")
