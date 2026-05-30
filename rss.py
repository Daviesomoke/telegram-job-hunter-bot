







import asyncio
import feedparser
from typing import List
from .base import Job

async def fetch_rss_jobs(feed_urls: List[str]) -> List[Job]:
    jobs = []
    loop = asyncio.get_running_loop()
    for url in feed_urls:
        try:
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                location = entry.get("location", "Remote")
                remote = "remote" in location.lower() or "remote" in title.lower()
                job = Job(
                    title=title,
                    company=extract_company(entry),
                    location=location,
                    remote=remote,
                    url=link,
                    description=summary[:200],
                    source="rss",
                )
                jobs.append(job)
        except Exception:
            continue
    return jobs

def extract_company(entry) -> str:
    if "author" in entry:
        return entry.author
    if "source" in entry and "title" in entry.source:
        return entry.source.title
    return "Unknown"