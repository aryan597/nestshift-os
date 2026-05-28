"""
Job Agent — Unified Scraper
===========================
Scrapes AI/ML engineering roles from Greenhouse, Ashby, Lever, RSS feeds,
and generic career pages. Scores by keyword match and outputs ranked JSON.

Run manually:
    python agents/job_scraper.py

Or via orchestrator:
    python agents/orchestrator.py --agent job
"""
import json
import re
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Add parent to path so we can import config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    AGENTS_DIR,
    DATA_DIR,
    GREENHOUSE_COMPANIES,
    HIGH_PRIORITY_THRESHOLD,
    LOCATIONS,
    ROLE_KEYWORDS,
    WEIGHT_LOCATION_MATCH,
    WEIGHT_ROLE_MATCH,
)

requests.packages.urllib3.disable_warnings()
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, application/xhtml+xml",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
})

DB_PATH = DATA_DIR / "jobs.db"


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_at: Optional[str] = None
    description: str = ""
    score: float = 0.0
    tags: List[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            source TEXT,
            posted_at TEXT,
            description TEXT,
            score REAL,
            tags TEXT,
            scraped_at TEXT,
            notified INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scraper_log (
            run_at TEXT PRIMARY KEY,
            source TEXT,
            jobs_found INTEGER,
            jobs_new INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_jobs(jobs: List[Job]) -> tuple[int, int]:
    """Insert jobs, return (total_found, new_inserted)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0
    for job in jobs:
        try:
            cursor.execute(
                """
                INSERT INTO jobs (id, title, company, location, url, source, posted_at,
                                  description, score, tags, scraped_at, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET
                    score=excluded.score,
                    tags=excluded.tags,
                    scraped_at=excluded.scraped_at
                """,
                (
                    job.id,
                    job.title,
                    job.company,
                    job.location,
                    job.url,
                    job.source,
                    job.posted_at,
                    job.description[:2000],
                    job.score,
                    json.dumps(job.tags),
                    job.scraped_at,
                ),
            )
            if cursor.rowcount > 0:
                new_count += 1
        except Exception as e:
            print(f"[DB] Error saving job {job.id}: {e}")
    conn.commit()
    conn.close()
    return len(jobs), new_count


def score_job(title: str, location: str, description: str = "") -> tuple[float, List[str]]:
    """Score a job 0-10+ based on keyword matches."""
    text = f"{title} {location} {description}".lower()
    score = 0.0
    tags = []

    for kw in ROLE_KEYWORDS:
        if kw in text:
            score += WEIGHT_ROLE_MATCH
            tags.append(kw)

    for loc in LOCATIONS:
        if loc in text:
            score += WEIGHT_LOCATION_MATCH
            tags.append(loc)

    # Dedupe tags
    tags = list(dict.fromkeys(tags))
    return round(score, 1), tags


# ── Greenhouse ─────────────────────────────────────────────────────

def scrape_greenhouse(company: str) -> List[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[Greenhouse] {company}: {e}")
        return []

    jobs = []
    for j in data.get("jobs", []):
        title = j.get("title", "")
        loc = j.get("location", {}).get("name", "")
        score, tags = score_job(title, loc)
        job_id = f"gh:{company}:{j['id']}"
        jobs.append(Job(
            id=job_id,
            title=title,
            company=company.replace("-", " ").title(),
            location=loc,
            url=j.get("absolute_url", ""),
            source="greenhouse",
            posted_at=j.get("updated_at", ""),
            score=score,
            tags=tags,
        ))
    print(f"[Greenhouse] {company}: {len(jobs)} jobs")
    return jobs


# ── Ashby ──────────────────────────────────────────────────────────

def scrape_ashby(company: str) -> List[Job]:
    """Scrape Ashby board by parsing the HTML career page."""
    board_url = f"https://jobs.ashbyhq.com/{company}"
    try:
        r = SESSION.get(board_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[Ashby] {company}: {e}")
        return []

    jobs = []
    # Ashby uses <a> tags with job posting links inside containers
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/jobs/" in href or "/job/" in href:
            title = a.get_text(strip=True)
            if len(title) < 3 or title.lower() in ("apply", "learn more", "view"):
                continue
            # Try to find location in nearby text
            loc = ""
            parent = a.find_parent(["div", "li", "tr"])
            if parent:
                loc_text = parent.get_text(separator=" ", strip=True)
                # Remove the title from location text
                loc = loc_text.replace(title, "").strip()
                # Clean up common separators
                loc = re.sub(r"^[\-|\·]+\s*", "", loc)
                loc = loc.split("·")[0].strip() if "·" in loc else loc

            full_url = urljoin(board_url, href)
            score, tags = score_job(title, loc)
            job_id = f"ashby:{company}:{hash(full_url) & 0xFFFFFFFF}"
            jobs.append(Job(
                id=job_id,
                title=title,
                company=company.replace("-", " ").title(),
                location=loc,
                url=full_url,
                source="ashby",
                score=score,
                tags=tags,
            ))

    # Deduplicate by URL
    seen = set()
    deduped = []
    for job in jobs:
        if job.url not in seen:
            seen.add(job.url)
            deduped.append(job)

    print(f"[Ashby] {company}: {len(deduped)} jobs")
    return deduped


# ── Lever ──────────────────────────────────────────────────────────

def scrape_lever(company: str) -> List[Job]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
    except Exception as e:
        print(f"[Lever] {company}: {e}")
        return []

    jobs = []
    for j in data:
        title = j.get("text", "")
        loc = ", ".join(j.get("categories", {}).get("location", [])) or j.get("categories", {}).get("allLocations", "")
        score, tags = score_job(title, loc)
        job_id = f"lever:{company}:{j['id']}"
        jobs.append(Job(
            id=job_id,
            title=title,
            company=company.replace("-", " ").title(),
            location=loc,
            url=j.get("applyUrl", ""),
            source="lever",
            posted_at=j.get("createdAt", ""),
            score=score,
            tags=tags,
        ))
    print(f"[Lever] {company}: {len(jobs)} jobs")
    return jobs


# ── RSS / Generic XML ──────────────────────────────────────────────

def scrape_rss(feed_name: str, feed_url: str) -> List[Job]:
    """Lightweight RSS/Atom parser for LinkedIn and other feeds."""
    try:
        r = SESSION.get(feed_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "xml")
    except Exception as e:
        print(f"[RSS] {feed_name}: {e}")
        return []

    jobs = []
    items = soup.find_all("item") or soup.find_all("entry")
    for item in items:
        title = item.find("title")
        title = title.get_text(strip=True) if title else ""
        link = item.find("link")
        url = ""
        if link:
            url = link.get("href", "") or link.get_text(strip=True)
        loc = ""
        desc = ""
        description = item.find("description") or item.find("summary")
        if description:
            desc = description.get_text(strip=True)
            # Try to extract location from description
            m = re.search(r"(london|remote|hybrid|uk|united kingdom)[\w\s,]*", desc, re.I)
            if m:
                loc = m.group(0)

        score, tags = score_job(title, loc, desc)
        job_id = f"rss:{feed_name}:{hash(url) & 0xFFFFFFFF}"
        jobs.append(Job(
            id=job_id,
            title=title,
            company="",  # RSS often doesn't have clear company
            location=loc,
            url=url,
            source=f"rss:{feed_name}",
            description=desc[:500],
            score=score,
            tags=tags,
        ))

    print(f"[RSS] {feed_name}: {len(jobs)} items")
    return jobs


# ── Orchestration ──────────────────────────────────────────────────

def run_all() -> dict:
    init_db()
    all_jobs: List[Job] = []

    # 1. Greenhouse (very reliable)
    for company in GREENHOUSE_COMPANIES:
        time.sleep(0.5)  # be polite
        all_jobs.extend(scrape_greenhouse(company))

    # 2. Ashby (HTML scraping)
    # Build from a curated list of UK AI companies using Ashby
    # Curated Ashby boards - UK & global AI/ML companies
    ashby_companies = [
        "faculty", "speechmatics", "darktrace", "benevolentai",
        "wayve", "humanising-autonomy", "monolith-ai", "prolific",
        "poolside", "aleph-alpha", "elevenlabs",
        "stability", "runwayml", "midjourney",
        "xai", "perplexity", "cursor", "figure-ai",
        "deepmind", "google", "meta", "openai",
    ]
    for company in ashby_companies:
        time.sleep(0.8)
        all_jobs.extend(scrape_ashby(company))

    # 3. Lever
    # Curated Lever boards - verified active ones
    lever_companies = [
        "spotify", "netflix", "reddit", "discord",
        "roblox", "duolingo", "plaid", "gusto",
    ]
    for company in lever_companies:
        time.sleep(0.8)
        all_jobs.extend(scrape_lever(company))

    # 4. RSS feeds
    from config import RSS_FEEDS
    for name, url in RSS_FEEDS.items():
        time.sleep(1.0)
        all_jobs.extend(scrape_rss(name, url))

    # Filter high-scoring jobs
    high_priority = [j for j in all_jobs if j.score >= HIGH_PRIORITY_THRESHOLD]
    high_priority.sort(key=lambda x: x.score, reverse=True)

    # Save everything
    total_found, new_inserted = save_jobs(all_jobs)

    # Write daily summary JSON
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_found": total_found,
        "new_inserted": new_inserted,
        "high_priority_count": len(high_priority),
        "high_priority": [asdict(j) for j in high_priority[:20]],
    }
    summary_path = DATA_DIR / f"summary_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Log run
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scraper_log (run_at, source, jobs_found, jobs_new) VALUES (?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), "all", total_found, new_inserted),
    )
    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"Run complete: {total_found} found, {new_inserted} new, {len(high_priority)} high-priority")
    print(f"Summary: {summary_path}")
    print(f"{'='*50}")

    return summary


if __name__ == "__main__":
    summary = run_all()
    # Print top 5 high-priority jobs to console
    for job in summary.get("high_priority", [])[:5]:
        print(f"\n  [{job['score']}] {job['title']} @ {job['company']} ({job['location']})")
        print(f"      -> {job['url']}")
