# NOVA PRIME Agents

Multi-agent system for automated job hunting, research, and coding.

## Quick Start

```bash
# 1. Install deps
pip install schedule python-telegram-bot python-dotenv requests beautifulsoup4

# 2. Set env vars (Windows)
set TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234...
set TELEGRAM_USER_ID=12345678

# 3. Run everything once
python agents/orchestrator.py

# 4. Start Telegram bot
python agents/orchestrator.py --telegram

# 5. Register daily 8 AM Windows task (run as Admin)
python agents/orchestrator.py --setup-task
# Then run the generated PowerShell script
```

## Agents

| Agent | File | What It Does | Schedule |
|---|---|---|---|
| **Job Agent** | `job_scraper.py` | Scrapes Greenhouse, Ashby, Lever, RSS for AI/ML roles in London. Scores by keyword match. Saves to SQLite. | Daily 8:00 AM |
| **Research Agent** | `orchestrator.py` (placeholder) | Tracks arXiv papers, competitor pricing, paper improvements | Tue/Fri 9:00 AM |
| **Coder Agent** | `orchestrator.py` (placeholder) | Runs tests, checks TODOs, scaffolds next features | Mon–Fri 10:00 AM |
| **Telegram Bot** | `telegram_bot.py` | Remote control from phone: /jobs, /status, /research, /build | Always on |

## Telegram Commands

- `/start` — Welcome
- `/jobs` — Run scraper now
- `/jobs_top` — Today's top 5 matches
- `/status` — Git + disk status
- `/research` — Trigger research tasks
- `/build` — Trigger build tasks
- `/help` — Full list

## Data

All job data lives in `agents/data/jobs.db` (SQLite).

## Adding Job Sources

Edit `agents/config.py`:
- `GREENHOUSE_COMPANIES` — list of company slugs
- `ASHBY_COMPANIES` — add more Ashby boards
- `LEVER_COMPANIES` — add Lever boards
- `ROLE_KEYWORDS` — tune scoring keywords

## Architecture

```
Orchestrator (orchestrator.py)
  ├── Job Agent ──→ Greenhouse API
  │               ├── Ashby HTML scrape
  │               ├── Lever API
  │               └── RSS feeds
  │               └── SQLite (jobs.db)
  │
  ├── Research Agent ──→ arXiv (planned)
  │                    └── Competitor tracking (planned)
  │
  ├── Coder Agent ──→ Tests + build (planned)
  │
  └── Telegram Bot ──→ Your phone
```
