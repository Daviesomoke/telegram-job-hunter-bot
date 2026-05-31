









import logging
import aiohttp
from typing import List
from .base import Job

logger = logging.getLogger(__name__)
REDDIT_BASE = "https://www.reddit.com/r/{sub}/new.json?limit=25"


async def fetch_reddit_jobs(subreddits: List[str]) -> List[Job]:
    jobs = []
    headers = {"User-Agent": "jobot/1.0 (job alert telegram bot)"}
    async with aiohttp.ClientSession(headers=headers) as session:
        for sub in subreddits:
            url = REDDIT_BASE.format(sub=sub)
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 429:
                        logger.warning(f"Reddit rate limited on r/{sub}")
                        continue
                    if resp.status != 200:
                        logger.warning(f"Reddit r/{sub} returned {resp.status}")
                        continue
                    data = await resp.json()
                    for post in data["data"]["children"]:
                        pdata = post["data"]
                        title = pdata.get("title", "").strip()
                        if not title:
                            continue
                        flair = pdata.get("link_flair_text", "") or ""
                        # Only pick up hiring/job posts
                        if "[hiring]" not in title.lower() and "job" not in flair.lower():
                            continue
                        job = Job(
                            title=title,
                            company=pdata.get("author", "Reddit Job Post"),
                            location=flair if flair else "Remote",
                            remote="remote" in title.lower() or not flair,
                            url=f"https://reddit.com{pdata.get('permalink', '')}",
                            description=pdata.get("selftext", "")[:300],
                            source=f"reddit/r/{sub}",
                        )
                        jobs.append(job)
            except Exception as e:
                logger.error(f"Reddit scraper error on r/{sub}: {e}")
                continue
    return jobs