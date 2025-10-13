# col-piracy

Local MVP for piracy detection focused on Dailymotion, using a one-time XLSX import to a stable `data/data.json` (with deterministic series IDs), keyword expansion, and a daily search/report workflow.

## Quick Start (Local)

- Place the spreadsheet `打击盗版相关剧.xlsx` at repo root (already present).
- Import once to JSON:
  - `python3 src/ingest/import_xlsx.py 打击盗版相关剧.xlsx data/data.json`
- Run Dailymotion pipeline (reads `data/data.json`):
  - `python3 -m src.pipeline.run_dailymotion  `
  - Outputs state to `state/dailymotion_videos.json` and report to `reports/dailymotion_candidates_YYYY-MM-DD.csv`.

See `AGENTS.md` for project motivation, scope, conventions, and how future agents should operate in this repo.

Environment variables:
- `DATA_JSON` (default `data/data.json`)
- `REPORT_DIR` (default `reports`)
- `STATE_DIR` (default `state`)
- `DAILYMOTION_MAX_ALIASES` (default `10`) — cap of aliases per series searched
- `DAILYMOTION_PRIMARY_ALIASES` (default `2`) — number of top aliases to treat as high priority
- `DAILYMOTION_PER_TERM_LIMIT` (default `12`) — max results fetched for non-primary aliases
- `DAILYMOTION_PRIMARY_PER_TERM_LIMIT` (default equals `DAILYMOTION_PER_TERM_LIMIT`) — override to pull more results for primary aliases
- `DAILYMOTION_SLEEP_SEC` (default `0.3`) — delay between API calls
- `DAILYMOTION_LIKELY_REMOVED_DAYS` (default `3`) — days missing before an item is marked `likely_removed`
- `DAILYMOTION_SCORE_SCALE` (default `6.0`) — multiplier mapping raw score to the 0–10 normalized score
- `DAILYMOTION_SERIES_IDS` — optional CSV of `series_id`s to limit a run
- `DAILYMOTION_MIN_DURATION_SEC` (default `300`) — filter out videos shorter than this duration (in seconds)
- `DAILYMOTION_MIN_SCORE` (default `3.0`) — filter out candidates with normalized score below this threshold
- `DAILYMOTION_MIN_ALIAS_LENGTH` (default `6`) — skip search terms shorter than this character length

## Notes

- Importer generates a stable `series_id` using UUIDv5 from the normalized canonical title so reruns stay consistent. Aliases from all sheets are merged with de-duplication.
- Keyword expansion includes base names plus modest episode patterns (EP1/E01/第1集/etc.).
- Scoring favors exact/near matches in titles; adds small boosts for words like “full/完整/全集/1080p/EP”. Reports now include both the raw score and a 0–10 normalized score (controlled by `DAILYMOTION_SCORE_SCALE`). Channels are not yet whitelisted for Dailymotion.
- Network calls are made to Dailymotion’s public API (`/videos?search=...`) with conservative rate limiting.

## Next Steps

- Add Dailymotion channel whitelist (if available) and support more platforms.
- Add “likely_removed” detection comparing previous `state` snapshots across days.
- Wire Feishu bot for daily notifications and attach the CSV.
- Implement a follow-up job that rechecks historical video IDs directly via the platform API to confirm removals instead of relying solely on search misses.
