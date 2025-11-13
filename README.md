# col-piracy

Local MVP for piracy detection focused on Dailymotion, using a one-time XLSX import to a stable `data/data.json` (with deterministic series IDs), keyword expansion, and a daily search/report workflow.

## Quick Start (Local)

### One-time Setup

Place the spreadsheet `打击盗版相关剧.xlsx` at repo root and import to JSON:

```bash
python3 src/ingest/import_xlsx.py 打击盗版相关剧.xlsx data/data.json
```

### Daily Workflow

#### 1. Detect New Pirated Videos

```bash
python3 -m src.pipeline.run_dailymotion
```

**Outputs:**
- `state/dailymotion_videos.json` - Updated state database
- `reports/dailymotion_candidates_YYYY-MM-DD.csv` - All videos found today
- `reports/new_detections_YYYY-MM-DD.csv` - **Only new videos (send to operations team)**

#### 2. Recheck Known Videos Status

```bash
python3 -m src.pipeline.recheck_videos
```

**Outputs:**
- `state/dailymotion_videos.json` - Updated with current status
- `reports/status_update_YYYY-MM-DD.csv` - Status of all tracked videos with action needed

### Common Options

```bash
# Disable geo-checking (faster)
DAILYMOTION_ENABLE_GEO_CHECK=false python3 -m src.pipeline.run_dailymotion

# Only check specific series
DAILYMOTION_SERIES_IDS=abc123,def456 python3 -m src.pipeline.run_dailymotion

# Recheck only videos from last 7 days
DAILYMOTION_RECHECK_DAYS=7 python3 -m src.pipeline.recheck_videos
```

See `AGENTS.md` for project motivation, scope, conventions, and how future agents should operate in this repo.

Environment variables:
- `DATA_JSON` (default `data/data.json`)
- `REPORT_DIR` (default `reports`)
- `STATE_DIR` (default `state`)
- `DAILYMOTION_MAX_ALIASES` (default `10`) — cap of aliases per series searched
- `DAILYMOTION_PRIMARY_ALIASES` (default `2`) — number of top aliases to treat as high priority
- `DAILYMOTION_PER_TERM_LIMIT` (default `12`) — max results fetched for non-primary aliases
- `DAILYMOTION_PRIMARY_PER_TERM_LIMIT` (default equals `DAILYMOTION_PER_TERM_LIMIT`) — override to pull more results for primary aliases
- `DAILYMOTION_SLEEP_SEC` (default `0.3`) — delay between search API calls
- `DAILYMOTION_SCORE_SCALE` (default `6.0`) — multiplier mapping raw score to the 0–10 normalized score
- `DAILYMOTION_SERIES_IDS` — optional CSV of `series_id`s to limit a run
- `DAILYMOTION_MIN_DURATION_SEC` (default `300`) — filter out videos shorter than this duration (in seconds)
- `DAILYMOTION_MIN_SCORE` (default `3.0`) — filter out candidates with normalized score below this threshold
- `DAILYMOTION_MIN_ALIAS_LENGTH` (default `6`) — skip search terms shorter than this character length
- `DAILYMOTION_ENABLE_GEO_CHECK` (default `true`) — enable geo-blocking detection for new videos
- `DAILYMOTION_CHECK_REGIONS` (default `US,CN`) — comma-separated list of country codes (only affects whether geo-check is enabled)
- `DAILYMOTION_GEO_SLEEP_SEC` (default `0.1`) — delay between geo-check API calls
- `DAILYMOTION_RECHECK_DAYS` (default `30`) — only recheck videos detected within this many days
- `DAILYMOTION_RECHECK_SLEEP_SEC` (default `0.5`) — delay between recheck API calls

## Geo-Blocking Detection

Geo-blocking detection is **enabled by default** for new videos using Dailymotion's `geoblocking` field.

To disable geo-checking:

```bash
DAILYMOTION_ENABLE_GEO_CHECK=false python3 -m src.pipeline.run_dailymotion
```

**How it works:**
- New videos are checked via API to retrieve the `geoblocking` field (single API call per video)
- The `geoblocking` field contains the platform's geo-restriction configuration
- Results are parsed into `blocked_regions` and `available_regions` lists
- Data is stored in state and included in CSV reports with `geo_status` summary:
  - `全球可见` (globally available)
  - `全球屏蔽` (globally blocked)
  - `CN屏蔽` (blocked in specific regions)
  - `仅US,JP可见` (only available in specific regions)

**Efficient:** Uses Dailymotion's native `geoblocking` field instead of making multiple region-specific queries. No proxy servers needed.

## Notes

- Importer generates a stable `series_id` using UUIDv5 from the normalized canonical title so reruns stay consistent. Aliases from all sheets are merged with de-duplication.
- Keyword expansion includes base names plus modest episode patterns (EP1/E01/第1集/etc.).
- Scoring favors exact/near matches in titles; adds small boosts for words like "full/完整/全集/1080p/EP". Reports now include both the raw score and a 0–10 normalized score (controlled by `DAILYMOTION_SCORE_SCALE`). Channels are not yet whitelisted for Dailymotion.
- Network calls are made to Dailymotion's public API (`/videos?search=...`) with conservative rate limiting.
## Workflow

### Daily Operations (每天运行)

```bash
# 1. 检测新盗版视频
python3 -m src.pipeline.run_dailymotion

# Output:
# - reports/new_detections_YYYY-MM-DD.csv  ← 发给运营团队举报

# 2. 检查已知视频状态（是否下架）
python3 -m src.pipeline.recheck_videos

# Output:
# - reports/status_update_YYYY-MM-DD.csv  ← 查看下架情况和需要催办的视频
```

**报告说明：**
- `new_detections` - 只包含新检测到的视频，不含地区信息
- `status_update` - 包含所有视频的状态、地区信息、下架情况

### Status Tracking

Videos are automatically classified based on API status and time since detection:

- **已下架 ✓** - Video removed (404)
- **已变私密** - Made private by uploader
- **已加密码保护** - Password protected
- **被平台拒绝** - Rejected by platform
- **部分地区屏蔽** - Geo-blocked in some regions
- **需要催办 ⚠️** - Still active after 7+ days
- **假设已举报，等待处理** - 2-7 days old
- **等待举报** - Less than 2 days old

## Next Steps

- Add Dailymotion channel whitelist (if available) and support more platforms
- Wire Feishu bot for daily notifications and attach CSVs
- Add CSV import for manual report date tracking (`reported_videos.csv`)