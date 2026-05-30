
















import aiohttp
from typing import List
from .base import Job

REDDIT_BASE = "https://www.reddit.com/r/{sub}/new.json?limit=25"

async def fetch_reddit_jobs(subreddits: List[str]) -> List[Job]:
    jobs = []
    async with aiohttp.ClientSession() as session:
        for sub in subreddits:
            url = REDDIT_BASE.format(sub=sub)
            try:
                async with session.get(url, headers={"User-Agent": "jobot/1.0"}) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    for post in data["data"]["children"]:
                        pdata = post["data"]
                        title = pdata.get("title", "")
                        if not title:
                            continue
                        # Simple heuristic: only posts with "[hiring]" or "job" flair
                        if "[hiring]" not in title.lower() and "job" not in pdata.get("link_flair_text", "").lower():
                            continue
                        # Basic extraction
                        job = Job(
                            title=pdata.get("title", "Untitled"),
                            company="",  # reddit often doesn't specify cleanly
                            location=pdata.get("link_flair_text", "Remote"),
                            remote=True if "remote" in title.lower() else False,
                            url=pdata.get("url", ""),
                            description=pdata.get("selftext", "")[:200],
                            source=f"reddit/r/{sub}",
                        )
                        jobs.append(job)
            except Exception:
                continue
    return jobs