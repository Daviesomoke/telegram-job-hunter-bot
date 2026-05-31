








import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "data/jobot.db")

# ── Job sources ───────────────────────────────────────────────────────────────
REDDIT_SUBREDDITS: list[str] = [
    "forhire",
    "remotejs",
    "PythonJobs",
    "devopsjobs",
    "cscareerquestions",
]

RSS_FEEDS: list[str] = [
    # We Work Remotely — well-structured, reliable RSS
    "https://weworkremotely.com/remote-jobs.rss",
    # Remotive — remote tech jobs
    "https://remotive.com/remote-jobs/feed",
    # Stack Overflow Jobs RSS
    "https://stackoverflow.com/jobs/feed?r=true",
]

# ── Behaviour ─────────────────────────────────────────────────────────────────
FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "10"))
MAX_JOBS_PER_MESSAGE: int = 5

# ── Server ────────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8080"))
