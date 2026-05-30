






import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "data/jobot.db")

REDDIT_SUBREDDITS = ["forhire", "remotejs", "PythonJobs", "devopsjobs"]
REDDIT_USER_AGENT = "jobot/1.0"

RSS_FEEDS = [
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=Worldwide&f_TPR=r86400",
    "https://www.indeed.com/rss?q=remote+software+engineer&l=",
]

FETCH_INTERVAL_MINUTES = 10
MAX_JOBS_PER_MESSAGE = 5

# Render port
PORT = int(os.getenv("PORT", 8080))
