# col-piracy

Local MVP for piracy detection focused on Dailymotion, using a one-time XLSX import to a stable `data/data.json` (with deterministic series IDs), keyword expansion, and a daily search/report workflow.

## Quick Start (Local)

- Place the spreadsheet `打击盗版相关剧.xlsx` at repo root (already present).
- Import once to JSON:
  - `python3 src/ingest/import_xlsx.py 打击盗版相关剧.xlsx data/data.json`
- Run Dailymotion pipeline (reads `data/data.json`):
  - `python3 src/pipeline/run_dailymotion.py`
  - Outputs state to `state/dailymotion_videos.json` and report to `reports/dailymotion_candidates_YYYY-MM-DD.csv`.

See `AGENTS.md` for project motivation, scope, conventions, and how future agents should operate in this repo.

Environment variables:
- `DATA_JSON` (default `data/data.json`)
- `REPORT_DIR` (default `reports`)
- `STATE_DIR` (default `state`)

## Notes

- Importer generates a stable `series_id` using UUIDv5 from the normalized canonical title so reruns stay consistent. Aliases from all sheets are merged with de-duplication.
- Keyword expansion includes base names plus modest episode patterns (EP1/E01/第1集/etc.).
- Scoring favors exact/near matches in titles; adds small boosts for words like “full/完整/全集/1080p/EP”. Channels are not yet whitelisted for Dailymotion.
- Network calls are made to Dailymotion’s public API (`/videos?search=...`) with conservative rate limiting.

## Next Steps

- Add Dailymotion channel whitelist (if available) and support more platforms.
- Add “likely_removed” detection comparing previous `state` snapshots across days.
- Wire Feishu bot for daily notifications and attach the CSV.
