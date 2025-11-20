ALTER TABLE videos ADD COLUMN IF NOT EXISTS ignore_reason TEXT;
CREATE INDEX IF NOT EXISTS idx_videos_ignore_reason ON videos(ignore_reason);
