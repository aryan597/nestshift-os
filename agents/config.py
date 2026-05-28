"""
Agent Orchestrator Configuration
================================
Shared settings for job scraper, telegram bot, and research agents.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
AGENTS_DIR = Path(__file__).parent.resolve()
DATA_DIR = AGENTS_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Job Search Config ──────────────────────────────────────────────
# Role keywords to score job relevance
ROLE_KEYWORDS = [
    "ai engineer", "ml engineer", "machine learning engineer",
    "llm engineer", "ai researcher", "data scientist",
    "applied scientist", "foundation models", "edge ai",
    "robotics", "autonomous systems", "nlp engineer",
    "computer vision", "deep learning", "quantitative researcher",
    "mlops", "ai infrastructure", "research engineer",
    "spiking neural", "neuromorphic", "time series",
    "forecasting", "smart home", "iot", "energy",
]

# Location filters
LOCATIONS = ["london", "remote uk", "hybrid london", "united kingdom"]

# Companies with Ashby boards (UK AI/ML startups & scaleups)
ASHBY_COMPANIES = [
    # Top UK AI startups
    "bleeding-edge", " faculty", "speechmatics", "darktrace",
    "benevolentai", "deepmind", "wayve", "magic-pony",
    "humanising-autonomy", "monolith-ai", "prolific",
    "synthesia", "inworld-ai", "poolside", "mistral",
    # Scale-ups with London offices
    "aleph-alpha", "cohere", "anthropic", "openai",
    "stability-ai", "hugging-face", "weights-biases",
    # Add your own targets here
]

# Companies with Greenhouse boards
GREENHOUSE_COMPANIES = [
    "openai", "anthropic", "cohere", "stabilityai",
    "mistralai", "deepmind", "google", "meta",
    "alephalpha", "poolside", "elevenlabs", "huggingface",
]

# Job boards with RSS / public feeds
RSS_FEEDS = {
    "linkedin_ai_london": (
        "https://www.linkedin.com/jobs/search/?f_TPR=r86400"
        "&keywords=AI%20Engineer&location=London%2C%20England%2C%20United%20Kingdom"
    ),
    "linkedin_ml_london": (
        "https://www.linkedin.com/jobs/search/?f_TPR=r86400"
        "&keywords=Machine%20Learning%20Engineer&location=London%2C%20England%2C%20United%20Kingdom"
    ),
    "linkedin_llm_london": (
        "https://www.linkedin.com/jobs/search/?f_TPR=r86400"
        "&keywords=LLM%20Engineer&location=London%2C%20England%2C%20United%20Kingdom"
    ),
}

# ── Telegram ───────────────────────────────────────────────────────
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Your Telegram user ID (numeric) – get from @userinfobot
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "")

# ── Schedule ───────────────────────────────────────────────────────
DAILY_SCRAPE_HOUR = 8     # 8:00 AM
DAILY_SCRAPE_MINUTE = 0

# ── Scoring Weights ────────────────────────────────────────────────
WEIGHT_ROLE_MATCH = 3.0
WEIGHT_LOCATION_MATCH = 2.0
WEIGHT_SENIORITY_MATCH = 1.0

# Minimum score to flag as "high priority"
HIGH_PRIORITY_THRESHOLD = 5.0
