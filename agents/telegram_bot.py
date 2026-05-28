"""
Telegram Bot — Remote Control for NOVA PRIME
============================================
Send commands from your phone to control agents, get job alerts,
and check system status.

Setup:
    1. Message @BotFather on Telegram -> /newbot -> copy token
    2. Message @userinfobot -> copy your numeric User ID
    3. Set env vars:
       set TELEGRAM_BOT_TOKEN=your_token
       set TELEGRAM_USER_ID=your_user_id
    4. python agents/telegram_bot.py

Commands:
    /start          - Show welcome
    /status         - System & git status
    /jobs           - Run job scraper now
    /jobs_top       - Show today's top 5 jobs
    /research       - Trigger research agent (placeholder)
    /build          - Trigger coder agent (placeholder)
    /help           - Command list
"""
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters,
)

sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, DB_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

# ── Validate env ───────────────────────────────────────────────────
if not TELEGRAM_BOT_TOKEN:
    print("ERROR: Set TELEGRAM_BOT_TOKEN env var.")
    print("  Windows: set TELEGRAM_BOT_TOKEN=123456:ABC-DEF...")
    raise SystemExit(1)

if not TELEGRAM_USER_ID:
    print("WARNING: TELEGRAM_USER_ID not set. Bot will accept messages from ANYONE.")
    AUTHORIZED_USERS = set()
else:
    AUTHORIZED_USERS = {int(TELEGRAM_USER_ID)}


# ── Helpers ────────────────────────────────────────────────────────
def _auth_check(user_id: int) -> bool:
    if not AUTHORIZED_USERS:
        return True
    return user_id in AUTHORIZED_USERS


def _get_today_summary() -> dict:
    summary_path = DATA_DIR / f"summary_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _get_top_jobs(n: int = 5) -> list:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT title, company, location, url, score, tags, scraped_at
        FROM jobs
        WHERE scraped_at > date('now', '-1 day')
        ORDER BY score DESC, scraped_at DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Handlers ───────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text(
        "<b>NOVA PRIME Bot</b> online.\n\n"
        "Agents at your command:\n"
        "  /jobs      — Run job scraper\n"
        "  /jobs_top  — Today's best matches\n"
        "  /status    — System status\n"
        "  /research  — Run research agent\n"
        "  /build     — Run coder agent\n"
        "  /help      — Full command list",
        parse_mode="HTML",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return
    await update.message.reply_text(
        "<b>Commands</b>\n\n"
        "/start     — Welcome\n"
        "/status    — Git status, disk space, uptime\n"
        "/jobs      — Scrape all job boards now\n"
        "/jobs_top  — Top 5 matches from today\n"
        "/research  — Run research agent on NestShift paper\n"
        "/build     — Run coder agent (next feature build)\n"
        "/help      — This message",
        parse_mode="HTML",
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return

    import subprocess

    # Git status
    git_dir = Path(__file__).parent.parent
    try:
        git_status = subprocess.run(
            ["git", "status", "--short"],
            cwd=git_dir,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except Exception:
        git_status = "N/A"

    # Disk space
    try:
        disk = subprocess.run(
            ["wmic", "logicaldisk", "get", "size,freespace,caption"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except Exception:
        disk = "N/A"

    msg = (
        f"<b>System Status</b>\n\n"
        f"<b>Git Changes</b>\n"
        f"<pre>{git_status or 'Clean working tree'}</pre>\n\n"
        f"<b>Disk</b>\n"
        f"<pre>{disk}</pre>"
    )
    await update.message.reply_text(msg[:4000], parse_mode="HTML")


async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return
    await update.message.reply_text("Running job scraper... this takes ~30s.")

    # Run scraper in executor so we don't block the event loop
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(None, _run_scraper)
        hp = summary.get("high_priority", [])
        msg = (
            f"<b>Job Scraper Complete</b>\n\n"
            f"Found: {summary.get('total_found', 0)}\n"
            f"New: {summary.get('new_inserted', 0)}\n"
            f"High-priority: {len(hp)}\n\n"
        )
        for job in hp[:5]:
            tags = ", ".join(job.get("tags", [])[:3])
            msg += (
                f"<b>[{job['score']}] {job['title']}</b>\n"
                f"{job.get('company', 'Unknown')} | {job.get('location', 'N/A')}\n"
                f"Tags: {tags}\n"
                f"<a href='{job['url']}'>Apply</a>\n\n"
            )
        await update.message.reply_text(msg[:4000], parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def _run_scraper():
    # Import here to avoid circular issues
    from job_scraper import run_all
    return run_all()


async def jobs_top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return
    jobs = _get_top_jobs(5)
    if not jobs:
        await update.message.reply_text("No jobs found today. Run /jobs first.")
        return

    msg = "<b>Top 5 Matches Today</b>\n\n"
    for j in jobs:
        tags = j.get("tags", "[]")
        try:
            tags = json.loads(tags)
            tags = ", ".join(tags[:3])
        except Exception:
            tags = str(tags)
        msg += (
            f"<b>[{j['score']}] {j['title']}</b>\n"
            f"{j.get('company', 'Unknown')} | {j.get('location', 'N/A')}\n"
            f"Tags: {tags}\n"
            f"<a href='{j['url']}'>Apply</a>\n\n"
        )
    await update.message.reply_text(msg[:4000], parse_mode="HTML", disable_web_page_preview=True)


async def research_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return
    await update.message.reply_text(
        "Research agent triggered.\n\n"
        "Next tasks:\n"
        "  1. Read latest arXiv papers on quantile regression + energy\n"
        "  2. Check competitor pricing (Octopus, Tesla Powerwall)\n"
        "  3. Generate next paper section outline\n\n"
        "(Full implementation pending — see agents/research_agent.py)",
        parse_mode="HTML",
    )


async def build_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _auth_check(update.effective_user.id):
        return
    await update.message.reply_text(
        "Coder agent triggered.\n\n"
        "Next build targets:\n"
        "  1. Jetson Orin Nano deployment script\n"
        "  2. NARE hardware bridge (GPIO + relay)\n"
        "  3. Dashboard v2 with real-time tariffs\n\n"
        "(Full implementation pending — see agents/coder_agent.py)",
        parse_mode="HTML",
    )


# ── Daily Summary Sender ───────────────────────────────────────────
async def send_daily_summary(app: Application):
    """Called by orchestrator or standalone scheduler."""
    if not AUTHORIZED_USERS:
        return
    summary = _get_today_summary()
    hp = summary.get("high_priority", [])

    msg = (
        f"<b>8 AM Job Report</b>\n"
        f"Run: {summary.get('run_at', 'N/A')[:19]}\n\n"
        f"Found: {summary.get('total_found', 0)} | New: {summary.get('new_inserted', 0)} | "
        f"High-priority: {len(hp)}\n\n"
    )
    for job in hp[:5]:
        tags = ", ".join(job.get("tags", [])[:3])
        msg += (
            f"<b>[{job['score']}] {job['title']}</b>\n"
            f"{job.get('company', 'Unknown')} | {job.get('location', 'N/A')}\n"
            f"Tags: {tags}\n"
            f"<a href='{job['url']}'>Apply</a>\n\n"
        )

    for uid in AUTHORIZED_USERS:
        try:
            await app.bot.send_message(
                chat_id=uid,
                text=msg[:4000],
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"[Telegram] Failed to send to {uid}: {e}")


# ── Main ───────────────────────────────────────────────────────────
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("jobs", jobs_cmd))
    application.add_handler(CommandHandler("jobs_top", jobs_top_cmd))
    application.add_handler(CommandHandler("research", research_cmd))
    application.add_handler(CommandHandler("build", build_cmd))

    print("[Telegram Bot] Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
