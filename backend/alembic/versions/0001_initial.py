"""initial schema — violations + cameras

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cameras",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location_lat", sa.Float()),
        sa.Column("location_lng", sa.Float()),
        sa.Column("rtsp_url", sa.String(255)),
        sa.Column("expected_flow_direction", sa.Float(), server_default="0"),
        sa.Column("stop_line_polygon", sa.JSON()),
        sa.Column("intersection_polygon", sa.JSON()),
        sa.Column("no_parking_zones", sa.JSON()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "violations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("violation_id", sa.String(50), nullable=False, unique=True),
        sa.Column("violation_type", sa.String(30), nullable=False),
        sa.Column("violation_code", sa.String(10), nullable=False),
        sa.Column("fine_inr", sa.Integer(), nullable=False),
        sa.Column("camera_id", sa.String(50), nullable=False),
        sa.Column("camera_name", sa.String(100)),
        sa.Column("raw_confidence", sa.Float(), nullable=False),
        sa.Column("final_confidence", sa.Float(), nullable=False),
        sa.Column("enforcement_action", sa.String(20), nullable=False),
        sa.Column("vehicle_type", sa.String(30)),
        sa.Column("plate_number", sa.String(20)),
        sa.Column("plate_confidence", sa.Float()),
        sa.Column("vehicle_bbox", sa.JSON()),
        sa.Column("evidence_image_path", sa.String(255)),
        sa.Column("evidence_thumbnail_path", sa.String(255)),
        sa.Column("evidence_video_path", sa.String(255)),
        sa.Column("evidence_hash", sa.String(64)),
        sa.Column("location_lat", sa.Float()),
        sa.Column("location_lng", sa.Float()),
        sa.Column("location_name", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="PENDING"),
        sa.Column("reviewed_by", sa.String(50)),
        sa.Column("review_notes", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("gemini_verdict", sa.String(20)),
        sa.Column("gemini_explanation", sa.Text()),
        sa.Column("model_version", sa.String(50)),
        sa.Column("pipeline_latency_ms", sa.Float()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_violations_camera", "violations", ["camera_id", "occurred_at"])
    op.create_index("idx_violations_type", "violations", ["violation_type", "occurred_at"])
    op.create_index("idx_violations_status", "violations", ["status"])
    op.create_index("idx_violations_plate", "violations", ["plate_number"])


def downgrade() -> None:
    op.drop_table("violations")
    op.drop_table("cameras")
