# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobHunter — a Chinese job aggregation platform that scrapes internship and campus recruitment listings from multiple sources, stores them in SQLite, and serves a Vue 3 single-page frontend via Flask.

## Commands

```bash
# Setup
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Run
python app.py                  # Flask dev server on http://0.0.0.0:5003

# No test suite — testing is manual via the web UI and API
```

## Architecture

```
JobHunter/
├── app.py              # Flask app + all REST API routes + crawler thread management
├── config.py           # All configuration: DB path, crawler params, Flask settings
├── models.py           # SQLite data layer (schema, CRUD, query builder, export)
├── crawler/
│   ├── base_crawler.py     # Abstract base: Playwright lifecycle, stealth, retries, date parsing
│   ├── shixiseng_crawler.py  # Shixiseng.com HTML scraper
│   ├── ncss_crawler.py       # NCSS JSON API scraper (runs inside browser context)
│   └── website_crawler.py    # Generic career page scraper (198 companies from config/company_urls.json)
├── config/company_urls.json  # Company career page URLs with metadata
├── templates/index.html      # Jinja2 template hosting Vue 3 SPA (uses {% raw %} to avoid {{ }} conflict)
├── static/app.js             # Vue 3 Composition API — all frontend logic
└── static/style.css          # Glassmorphism CSS design
```

### Key Design Patterns

- **Callback-driven crawl pipeline**: Crawlers run in daemon threads. `set_jobs_callback()` triggers `batch_insert_jobs()` on each page of results for immediate persistence. `set_progress_callback()` updates a global `crawl_status` dict (lock-protected) that the frontend polls every 2s via `GET /api/crawl/status`.
- **Crawler hierarchy**: `BaseCrawler` provides Playwright browser management, stealth mode (`playwright-stealth`), random delays, retry logic, and captcha detection. Three subclasses implement `crawl()`.
- **SQLite upserts**: `job_url` has a UNIQUE constraint; `batch_insert_jobs()` does insert-or-update to handle re-crawls cleanly.
- **Schema migration**: Inline `ALTER TABLE ADD COLUMN` guarded by `try/except` — no migration framework.
- **Frontend**: Vue 3 loaded from CDN, no build step. All state management, filtering, and pagination in `app.js`. Jinja2 only serves the initial template.

### API Endpoints (all in app.py)

- `GET /api/jobs` — paginated job list with filters (keyword, company, location, salary, source, industry, etc.)
- `GET /api/stats` — aggregate stats (total jobs, companies, sources breakdown)
- `GET /api/companies` / `GET /api/industries` — filter dropdown data
- `POST /api/crawl` — start a crawl task (`source`: shixiseng | ncss | websites | all)
- `GET /api/crawl/status` — poll crawl progress
- `GET /api/export` — Excel download with same filters as /api/jobs

### Source Constants (config.py)

- `SOURCE_SHIXISENG = '实习僧'`
- `SOURCE_NCSS = '国家平台'`
- `SOURCE_WEBSITE = '官网'`

## Important Notes

- The database file (`job_aggregator.db`) and logs are gitignored.
- Flask debug mode is on by default in config.py.
- The frontend language is Chinese — all UI labels, filter names, and source names are in Chinese.
- Crawler delays and retry counts are tuned per-source in config.py to avoid rate limiting.
