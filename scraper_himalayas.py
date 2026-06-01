








import logging
import aiohttp
from typing import List
from base import Job
from config import TARGET_ROLES, REMOTE_ONLY

logger = logging.getLogger(__name__)

HIMALAYAS_URL = "https://himalayas.app/jobs/api?limit=100"

def _is_relevant(title: str, desc: str) -> bool:
    text = f"{title} {desc}".lower()
    return any(role.lower() in text for role in TARGET_ROLES)

async def fetch_himalayas_jobs() -> List[Job]:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; jobot/1.0)",
        "Accept": "application/json",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(HIMALAYAS_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.warning(f"Himalayas returned {resp.status}")
                    return jobs
                data = await resp.json(content_type=None)
                job_list = data.get("jobs", [])

                for item in job_list:
                    title   = item.get("title", "").strip()
                    company = item.get("companyName", "Unknown")
                    url     = item.get("applicationLink", "") or item.get("url", "")
                    desc    = item.get("description", "")[:300]
                    skills  = [s.get("title", "") for s in item.get("skills", [])]

                    if not title:
                        continue
                    if not _is_relevant(title, desc):
                        continue

                    job = Job(
                        title=title,
                        company=company,
                        location="Remote",
                        remote=True,
                        tech_stack=skills[:6],
                        url=url,
                        description=desc,
                        source="himalayas.app",
                    )
                    jobs.append(job)

    except Exception as e:
        logger.error(f"Himalayas scraper error: {e}")

    logger.info(f"Himalayas: {len(jobs)} matching jobs")
    return jobs