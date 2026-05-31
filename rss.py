









import asyncio
import logging
import re
import feedparser
from typing import List
from base import Job

logger = logging.getLogger(__name__)


async def fetch_rss_jobs(feed_urls: List[str]) -> List[Job]:
    jobs = []
    loop = asyncio.get_running_loop()
    for url in feed_urls:
        try:
            feed = await asyncio.wait_for(
                loop.run_in_executor(None, feedparser.parse, url),
                timeout=15
            )
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if not title or not link:
                    continue
                summary = re.sub(r"<[^>]+>", " ", entry.get("summary", "")).strip()
                location = entry.get("location", "") or "Remote"
                remote = "remote" in location.lower() or "remote" in title.lower()
                job = Job(
                    title=title,
                    company=_extract_company(entry),
                    location=location,
                    remote=remote,
                    url=link,
                    description=summary[:300],
                    source="rss",
                )
                jobs.append(job)
        except asyncio.TimeoutError:
            logger.warning(f"RSS timeout: {url}")
        except Exception as e:
            logger.error(f"RSS error ({url}): {e}")
    return jobs


def _extract_company(entry) -> str:
    if hasattr(entry, "author") and entry.author:
        return entry.author
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    return "Unknown"