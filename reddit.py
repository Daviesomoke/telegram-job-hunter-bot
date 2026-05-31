






import logging
import aiohttp
from typing import List
from base import Job
from config import TARGET_ROLES, REMOTE_ONLY

logger = logging.getLogger(__name__)
REDDIT_BASE = "https://www.reddit.com/r/{sub}/new.json?limit=50"


def _is_relevant(title: str, body: str) -> bool:
    """Return True if the post matches any target role keyword."""
    text = f"{title} {body}".lower()
    return any(role.lower() in text for role in TARGET_ROLES)


async def fetch_reddit_jobs(subreddits: List[str]) -> List[Job]:
    jobs = []
    headers = {"User-Agent": "jobot/1.0"}

    async with aiohttp.ClientSession(headers=headers) as session:
        for sub in subreddits:
            url = REDDIT_BASE.format(sub=sub)
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 429:
                        logger.warning(f"Rate limited on r/{sub}")
                        continue
                    if resp.status != 200:
                        continue

                    data = await resp.json()
                    for post in data["data"]["children"]:
                        pdata = post["data"]
                        title = pdata.get("title", "").strip()
                        body  = pdata.get("selftext", "")
                        flair = pdata.get("link_flair_text", "") or ""

                        if not title:
                            continue

                        # Must mention hiring/job intent OR match a role keyword
                        hiring_signal = (
                            "[hiring]" in title.lower()
                            or "[for hire]" in title.lower()
                            or "job" in flair.lower()
                            or "hiring" in flair.lower()
                            or "hire" in title.lower()
                        )
                        if not hiring_signal and not _is_relevant(title, body):
                            continue

                        is_remote = (
                            "remote" in title.lower()
                            or "remote" in body.lower()
                            or "remote" in flair.lower()
                        )

                        # Skip non-remote if remote-only mode is on
                        if REMOTE_ONLY and not is_remote:
                            continue

                        # Skip if no role keyword matches
                        if not _is_relevant(title, body):
                            continue

                        job = Job(
                            title=title,
                            company=pdata.get("author", "Reddit"),
                            location="Remote" if is_remote else flair or "Unknown",
                            remote=is_remote,
                            url=f"https://reddit.com{pdata.get('permalink', '')}",
                            description=body[:300],
                            source=f"reddit/r/{sub}",
                        )
                        jobs.append(job)

            except Exception as e:
                logger.error(f"Reddit error r/{sub}: {e}")

    logger.info(f"Reddit: fetched {len(jobs)} matching jobs")
    return jobs