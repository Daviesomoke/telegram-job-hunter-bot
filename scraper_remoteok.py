









import logging
import aiohttp
from typing import List
from base import Job
from config import TARGET_ROLES, REMOTE_ONLY

logger = logging.getLogger(__name__)

REMOTEOK_URL = "https://remoteok.com/api"

def _is_relevant(title: str, tags: str) -> bool:
    text = f"{title} {tags}".lower()
    return any(role.lower() in text for role in TARGET_ROLES)

async def fetch_remoteok_jobs() -> List[Job]:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; jobot/1.0)",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(REMOTEOK_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.warning(f"RemoteOK returned {resp.status}")
                    return jobs
                data = await resp.json(content_type=None)
                # First item is a legal notice dict, skip it
                for item in data[1:]:
                    if not isinstance(item, dict):
                        continue
                    title    = item.get("position", "").strip()
                    company  = item.get("company", "Unknown")
                    url      = item.get("url", "")
                    tags     = " ".join(item.get("tags", []))
                    desc     = item.get("description", "")[:300]

                    if not title:
                        continue
                    if not _is_relevant(title, tags):
                        continue

                    job = Job(
                        title=title,
                        company=company,
                        location="Remote",
                        remote=True,
                        tech_stack=item.get("tags", [])[:6],
                        url=url,
                        description=desc,
                        source="remoteok.com",
                    )
                    jobs.append(job)

    except Exception as e:
        logger.error(f"RemoteOK scraper error: {e}")

    logger.info(f"RemoteOK: {len(jobs)} matching jobs")
    return jobs