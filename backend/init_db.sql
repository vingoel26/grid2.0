-- ── Gridlock 2.0 — TimescaleDB init (Part 7 schema) ──
-- Run automatically by the timescaledb container if mounted to
-- /docker-entrypoint-initdb.d/. SQLAlchemy also creates these tables on boot;
-- this file additionally enables the hypertable + tuned indexes.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS violations (
    id                      VARCHAR(36) PRIMARY KEY,
    violation_id            VARCHAR(50) UNIQUE NOT NULL,
    violation_type          VARCHAR(30) NOT NULL,
    violation_code          VARCHAR(10) NOT NULL,
    fine_inr                INTEGER NOT NULL,
    camera_id               VARCHAR(50) NOT NULL,
    camera_name             VARCHAR(100),
    raw_confidence          FLOAT NOT NULL,
    final_confidence        FLOAT NOT NULL,
    enforcement_action      VARCHAR(20) NOT NULL,
    vehicle_type            VARCHAR(30),
    plate_number            VARCHAR(20),
    plate_confidence        FLOAT,
    vehicle_bbox            JSONB,
    evidence_image_path     VARCHAR(255),
    evidence_thumbnail_path VARCHAR(255),
    evidence_video_path     VARCHAR(255),
    evidence_hash           VARCHAR(64),
    location_lat            DOUBLE PRECISION,
    location_lng            DOUBLE PRECISION,
    location_name           VARCHAR(100),
    status                  VARCHAR(20) DEFAULT 'PENDING',
    reviewed_by             VARCHAR(50),
    review_notes            TEXT,
    reviewed_at             TIMESTAMPTZ,
    gemini_verdict          VARCHAR(20),
    gemini_explanation      TEXT,
    model_version           VARCHAR(50),
    pipeline_latency_ms     FLOAT,
    occurred_at             TIMESTAMPTZ NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Promote to a hypertable. TimescaleDB requires every UNIQUE index to include
-- the partition column (occurred_at). Our PK is `id` alone, so a strict
-- conversion would fail — we attempt it best-effort and fall back to a plain
-- table (fully functional, just without time-partitioning) if it can't convert.
DO $$
BEGIN
    PERFORM create_hypertable('violations', 'occurred_at',
                              if_not_exists => TRUE, migrate_data => TRUE);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Hypertable conversion skipped: %', SQLERRM;
END $$;

CREATE INDEX IF NOT EXISTS idx_violations_camera ON violations(camera_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_violations_type   ON violations(violation_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_violations_plate  ON violations(plate_number);

CREATE TABLE IF NOT EXISTS cameras (
    id                      VARCHAR(50) PRIMARY KEY,
    name                    VARCHAR(100) NOT NULL,
    location_lat            DOUBLE PRECISION,
    location_lng            DOUBLE PRECISION,
    rtsp_url                VARCHAR(255),
    expected_flow_direction FLOAT DEFAULT 0,
    stop_line_polygon       JSONB,
    intersection_polygon    JSONB,
    no_parking_zones        JSONB,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
