




import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "data/jobot.db")

# Subreddits to monitor
REDDIT_SUBREDDITS = ["forhire", "remotejs", "PythonJobs", "devopsjobs"]
REDDIT_USER_AGENT = "jobot/1.0"

# RSS feeds
RSS_FEEDS = [
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=Worldwide&f_TPR=r86400",
    "https://www.indeed.com/rss?q=remote+software+engineer&l=",
    "https://workatastartup.com/jobs.rss",
]

# Scraping interval in minutes
FETCH_INTERVAL_MINUTES = 10

# Max jobs per notification
MAX_JOBS_PER_MESSAGE = 5