"""
Agent Orchestrator — NOVA PRIME Multi-Agent System
==================================================
Coordinates daily runs of:
  • Job Agent      — scrapes + scores + alerts
  • Research Agent — paper research + competitor tracking
  • Coder Agent    — automated build tasks + PR generation

Modes:
    python agents/orchestrator.py --daemon      # Run all agents on schedule
    python agents/orchestrator.py --job         # Run job agent once
    python agents/orchestrator.py --research    # Run research agent once
    python agents/orchestrator.py --build       # Run coder agent once
    python agents/orchestrator.py --telegram    # Start Telegram bot
"""
import argparse
import asyncio
import importlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DAILY_SCRAPE_HOUR, DAILY_SCRAPE_MINUTE


def run_job_agent():
    print(f"\n{'='*60}")
    print(f"[JOB AGENT] {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")
    from job_scraper import run_all
    return run_all()


def run_research_agent():
    print(f"\n{'='*60}")
    print(f"[RESEARCH AGENT] {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")
    # Placeholder — will be expanded with arXiv scraping, competitor tracking, etc.
    tasks = [
        "Check arXiv for new quantile regression + energy forecasting papers",
        "Track Octopus Agile / Tesla Powerwall pricing changes",
        "Update literature review section in paper_main.tex",
        "Monitor HuggingFace trending models for edge deployment",
    ]
    for t in tasks:
        print(f"  [ ] {t}")
    print("[Research Agent] Complete (manual review required)")
    return {"agent": "research", "tasks": tasks}


def run_coder_agent():
    print(f"\n{'='*60}")
    print(f"[CODER AGENT] {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")
    # Placeholder — will be expanded with automated build + test + PR generation
    tasks = [
        "Run full test suite (pytest tests/)",
        "Check for TODO comments in codebase",
        "Generate next feature branch scaffold",
        "Update CHANGELOG.md with recent commits",
    ]
    for t in tasks:
        print(f"  [ ] {t}")
    print("[Coder Agent] Complete (manual implementation required)")
    return {"agent": "coder", "tasks": tasks}


async def daemon_mode():
    """Background daemon: run agents on schedule + Telegram alerts."""
    import schedule

    # Schedule daily job scrape at 8:00 AM
    schedule.every().day.at(f"{DAILY_SCRAPE_HOUR:02d}:{DAILY_SCRAPE_MINUTE:02d}").do(run_job_agent)
    # Schedule research agent twice a week (Tue, Fri)
    schedule.every().tuesday.at("09:00").do(run_research_agent)
    schedule.every().friday.at("09:00").do(run_research_agent)
    # Schedule coder agent every weekday at 10:00 AM
    schedule.every().monday.at("10:00").do(run_coder_agent)
    schedule.every().tuesday.at("10:00").do(run_coder_agent)
    schedule.every().wednesday.at("10:00").do(run_coder_agent)
    schedule.every().thursday.at("10:00").do(run_coder_agent)
    schedule.every().friday.at("10:00").do(run_coder_agent)

    print(f"[Orchestrator] Daemon started. Daily job scrape at {DAILY_SCRAPE_HOUR:02d}:{DAILY_SCRAPE_MINUTE:02d}.")
    print("[Orchestrator] Press Ctrl+C to stop.")

    # If Telegram is configured, start it in background
    telegram_task = None
    try:
        from telegram_bot import main as telegram_main, TELEGRAM_BOT_TOKEN
        if TELEGRAM_BOT_TOKEN:
            telegram_task = asyncio.create_task(_telegram_bg())
    except Exception as e:
        print(f"[Orchestrator] Telegram not started: {e}")

    while True:
        schedule.run_pending()
        await asyncio.sleep(30)


async def _telegram_bg():
    """Run Telegram bot in background within the same event loop."""
    from telegram_bot import main as telegram_main
    await telegram_main()


async def run_telegram_bot():
    from telegram_bot import main as telegram_main
    await telegram_main()


def setup_windows_task():
    """Generate PowerShell commands to register with Windows Task Scheduler."""
    python_exe = sys.executable.replace("\\", "/")
    script_path = (Path(__file__).parent / "orchestrator.py").resolve()
    log_path = (Path(__file__).parent / "data" / "orchestrator.log").resolve()

    ps = f"""
# Run these in PowerShell as Administrator to register the daily task:

$Action = New-ScheduledTaskAction -Execute '{python_exe}' -Argument '{script_path} --daemon'
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:55am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName "NOVA_PRIME_Agents" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force

# To remove later:
# Unregister-ScheduledTask -TaskName "NOVA_PRIME_Agents" -Confirm:$false
"""
    print(ps)
    setup_path = Path(__file__).parent / "setup_windows_task.ps1"
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(ps.strip())
    print(f"\n[Setup] PowerShell script written to: {setup_path}")
    print("[Setup] Run it as Administrator to register the daily task.")


def main():
    parser = argparse.ArgumentParser(description="NOVA PRIME Agent Orchestrator")
    parser.add_argument("--daemon", action="store_true", help="Run scheduled daemon")
    parser.add_argument("--job", action="store_true", help="Run job agent once")
    parser.add_argument("--research", action="store_true", help="Run research agent once")
    parser.add_argument("--build", action="store_true", help="Run coder agent once")
    parser.add_argument("--telegram", action="store_true", help="Start Telegram bot")
    parser.add_argument("--setup-task", action="store_true", help="Generate Windows Task Scheduler script")
    args = parser.parse_args()

    if args.job:
        run_job_agent()
    elif args.research:
        run_research_agent()
    elif args.build:
        run_coder_agent()
    elif args.telegram:
        asyncio.run(run_telegram_bot())
    elif args.setup_task:
        setup_windows_task()
    elif args.daemon:
        try:
            asyncio.run(daemon_mode())
        except KeyboardInterrupt:
            print("\n[Orchestrator] Shutting down.")
    else:
        # Default: run all agents once sequentially
        run_job_agent()
        run_research_agent()
        run_coder_agent()
        print("\n[Orchestrator] All agents complete. Use --daemon for scheduled runs.")


if __name__ == "__main__":
    main()
