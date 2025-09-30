# Project Agent Guide (AGENTS.md)

This file gives context and instructions to coding agents working in this repository. Its scope is the entire repo.

## Motivation & Goal

- Purpose: Detect unauthorized redistribution of our short series on public platforms and produce daily reports for ops review/takedown.
- Phase focus (MVP): Dailymotion first; API‑first approach; light, reliable pipeline with human review.
- Constraint: One‑time ingestion of the master catalog spreadsheet; subsequent runs should not re‑process XLSX but use a normalized JSON registry.

## Current State (MVP)

- One‑time import: `src/ingest/import_xlsx.py` → `data/data.json`
  - Reads sheets: 自制版权文件, 自制剧多语言剧名, sereal自制剧单-多语言, YouTube频道链接-投放侧账号.
  - Produces deterministic `series_id` (UUIDv5 of normalized canonical title), merges aliases across languages, captures a YouTube whitelist. Avoids dupes via normalized matching.
- Keyword expansion: `src/keywords/expand.py`
  - Builds search terms from aliases + modest episode patterns (EP1/E01/第1集/etc.).
- Matching & scoring: `src/matching/score.py`
  - Title similarity (RapidFuzz if available; difflib fallback). Small boosts for tokens like “full/完整/全集/1080p/EP”.
- Dailymotion client: `src/platforms/dailymotion.py`
  - Public `/videos?search=` API, conservative rate limiting.
- Local pipeline: `src/pipeline/run_dailymotion.py`
  - Reads `data/data.json`, searches per series, dedupes by `(platform, video_id)`, computes score/status, writes state and CSV report.

## What To Build Next (high‑level)

1. Add Dailymotion channel whitelist usage if data provided.
2. “Likely removed” status by comparing today’s `state` with last seen (3‑day rule).
3. Feishu bot notification posting top N + attach CSV.
4. Add platform modules for YouTube, TikTok, Facebook (API‑first; fallbacks gated).
5. Optional DB persistence (PostgreSQL) replacing local state when ready.

## Conventions & Guardrails

- API‑first: Prefer official APIs; scraping only public search pages, no login, respect robots/ToS.
- Idempotency: UPSERT semantics for records (by `(platform, video_id)`), stable `series_id` keys.
- Deterministic IDs: `series_id` computed as UUIDv5 on normalized canonical title; do not change normalization unless migration is in place.
- Normalization: Unicode NFKC, casefold, apostrophes unified, whitespace collapsed; alias splits on `, ; ， 、 / |`.
- Performance: Cap queries per platform per run; include backoff/rate limits.
- Out of scope (Phase 1): Auto takedown submission; AI email analysis.

## Repo Layout

- `src/` code modules (pure Python; no heavy frameworks).
  - `ingest/` one‑time XLSX importer.
  - `keywords/` keyword expansion utilities.
  - `matching/` normalize/match/score.
  - `platforms/` per‑platform API clients.
  - `pipeline/` runnable scripts (local daily flows).
  - `utils/` shared helpers.
- `data/` generated registry (`data.json`) from XLSX; source of truth for CI runs.
- `state/` day‑to‑day detections (JSON), ephemeral.
- `reports/` CSV outputs, ephemeral.

## Running Locally

1. Import once:
   - `PYTHONPATH=. python3 src/ingest/import_xlsx.py 打击盗版相关剧.xlsx data/data.json`
2. Dailymotion quick run:
   - `PYTHONPATH=. python3 src/pipeline/run_dailymotion.py`
   - Outputs state to `state/dailymotion_videos.json` and CSV report under `reports/`.

Environment vars:
- `DATA_JSON` (default `data/data.json`)
- `REPORT_DIR` (default `reports`)
- `STATE_DIR` (default `state`)

## Coding Style for Agents

- Keep changes minimal and focused; follow existing module layout and naming.
- Prefer small, composable functions; avoid adding heavy dependencies.
- Don’t fix unrelated issues; mention them separately if discovered.
- Document new scripts in `README.md` and keep `AGENTS.md` updated if scope changes.

