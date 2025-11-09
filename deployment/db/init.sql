-- YOLOv11 數位雙生分析系統 - 基礎資料庫 Schema
-- 啟動容器時會自動執行此 SQL 建立資料表與索引

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------------------------
-- 1. analysis_tasks (分析任務表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id                   BIGSERIAL PRIMARY KEY,
    task_type            VARCHAR(20) NOT NULL CHECK (task_type IN ('realtime_camera', 'video_file')),
    status               VARCHAR(20) NOT NULL CHECK (status IN ('pending','running','paused','completed','failed')),
    source_info          JSONB,
    source_width         INTEGER,
    source_height        INTEGER,
    source_fps           FLOAT,
    start_time           TIMESTAMPTZ,
    end_time             TIMESTAMPTZ,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    task_name            VARCHAR(200),
    model_id             VARCHAR(100),
    confidence_threshold FLOAT DEFAULT 0.5
);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_created ON analysis_tasks(created_at);

------------------------------------------------------------------------------
-- 2. detection_results (檢測結果表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_results (
    id               BIGSERIAL PRIMARY KEY,
    task_id          BIGINT NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    tracker_id       BIGINT,
    object_speed     FLOAT,
    zones            JSONB,
    frame_number     INTEGER,
    frame_timestamp  TIMESTAMPTZ DEFAULT NOW(),
    object_type      VARCHAR(50),
    confidence       FLOAT,
    bbox_x1          FLOAT,
    bbox_y1          FLOAT,
    bbox_x2          FLOAT,
    bbox_y2          FLOAT,
    center_x         FLOAT,
    center_y         FLOAT
);
CREATE INDEX IF NOT EXISTS idx_detection_results_task ON detection_results(task_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_tracker ON detection_results(tracker_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_timestamp ON detection_results(frame_timestamp);

------------------------------------------------------------------------------
-- 3. line_crossing_events (穿越線事件表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS line_crossing_events (
    id            BIGSERIAL PRIMARY KEY,
    is_enabled    BOOLEAN DEFAULT TRUE,
    task_id       BIGINT NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    tracker_id    BIGINT,
    line_id       VARCHAR(50) NOT NULL,
    direction     VARCHAR(20),
    crossed_at    TIMESTAMPTZ DEFAULT NOW(),
    frame_number  INTEGER,
    enter_count   INTEGER DEFAULT 0,
    leave_count   INTEGER DEFAULT 0,
    extra         JSONB
);
CREATE INDEX IF NOT EXISTS idx_line_events_task_line ON line_crossing_events(task_id, line_id);
CREATE INDEX IF NOT EXISTS idx_line_events_tracker ON line_crossing_events(tracker_id);

------------------------------------------------------------------------------
-- 4. zone_dwell_events (區域停留事件表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zone_dwell_events (
    id              BIGSERIAL PRIMARY KEY,
    is_enabled      BOOLEAN DEFAULT TRUE,
    task_id         BIGINT NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    tracker_id      BIGINT,
    zone_id         VARCHAR(50) NOT NULL,
    entered_at      TIMESTAMPTZ,
    exited_at       TIMESTAMPTZ,
    dwell_seconds   FLOAT,
    current_count   INTEGER,
    average_seconds FLOAT,
    max_seconds     FLOAT,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    extra           JSONB
);
CREATE INDEX IF NOT EXISTS idx_zone_events_task_zone ON zone_dwell_events(task_id, zone_id);
CREATE INDEX IF NOT EXISTS idx_zone_events_tracker ON zone_dwell_events(tracker_id);

------------------------------------------------------------------------------
-- 5. speed_events (速度事件表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS speed_events (
    id              BIGSERIAL PRIMARY KEY,
    is_enabled      BOOLEAN DEFAULT TRUE,
    task_id         BIGINT NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    tracker_id      BIGINT,
    speed_avg       FLOAT,
    speed_max       FLOAT,
    threshold       FLOAT,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    extra           JSONB
);
CREATE INDEX IF NOT EXISTS idx_speed_events_task ON speed_events(task_id);
CREATE INDEX IF NOT EXISTS idx_speed_events_tracker ON speed_events(tracker_id);

------------------------------------------------------------------------------
-- 6. data_sources (資料來源表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    id          BIGSERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('camera','video_file')),
    name        VARCHAR(100) NOT NULL,
    config      JSONB,
    status      VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','error')),
    last_check  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_data_sources_status ON data_sources(status);

------------------------------------------------------------------------------
-- 7. users (使用者表)  - 規劃中，可視需要啟用
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin','operator','viewer')),
    is_active     BOOLEAN DEFAULT TRUE,
    last_login    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

------------------------------------------------------------------------------
-- 8. system_config (系統配置表)
------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_config (
    id           BIGSERIAL PRIMARY KEY,
    config_key   VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description  TEXT,
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);
