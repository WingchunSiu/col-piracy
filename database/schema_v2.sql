-- PostgreSQL Schema for Piracy Detection System (v2)

-- Videos table - stores all detected piracy videos
CREATE TABLE IF NOT EXISTS videos (
    -- Primary identification
    platform VARCHAR(50) NOT NULL DEFAULT 'dailymotion',
    video_id VARCHAR(255) NOT NULL,

    -- Basic info
    url TEXT,
    title TEXT,
    uploader VARCHAR(255),
    duration_sec INTEGER,
    publish_time BIGINT,  -- Unix timestamp from API
    views INTEGER,

    -- Scoring
    raw_score FLOAT,
    score FLOAT,

    -- Metadata
    series_id VARCHAR(255),
    source_term TEXT,

    -- Geo-blocking info
    geoblocking JSONB,
    blocked_regions TEXT[],

    -- Status tracking
    api_status VARCHAR(50),  -- active, removed, private, password_protected, rejected
    api_last_checked DATE,

    -- Timestamps
    first_seen DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Primary key
    PRIMARY KEY(platform, video_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_first_seen ON videos(first_seen);
CREATE INDEX IF NOT EXISTS idx_api_status ON videos(api_status);
CREATE INDEX IF NOT EXISTS idx_series_id ON videos(series_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Useful views
CREATE OR REPLACE VIEW active_videos AS
SELECT * FROM videos
WHERE api_status = 'active' OR api_status IS NULL
ORDER BY first_seen DESC;

CREATE OR REPLACE VIEW recent_detections AS
SELECT * FROM videos
WHERE first_seen >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY first_seen DESC;

CREATE OR REPLACE VIEW videos_need_recheck AS
SELECT * FROM videos
WHERE
    first_seen >= CURRENT_DATE - INTERVAL '30 days'  -- Within 30 days
    AND (first_seen <= CURRENT_DATE - INTERVAL '2 days')  -- At least 2 days old
    AND (api_status IS NULL OR api_status = 'active')  -- Not yet removed
ORDER BY first_seen DESC;
