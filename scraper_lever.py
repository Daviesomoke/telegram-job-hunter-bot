








import logging
import aiohttp
from typing import List
from base import Job
from config import TARGET_ROLES

logger = logging.getLogger(__name__)

# Well-known tech companies that use Lever for hiring
# Bot will check each of these for open roles
LEVER_COMPANIES = [
    "airbnb", "stripe", "notion", "figma", "linear", "vercel",
    "netlify", "supabase", "planetscale", "railway", "render",
    "hashicorp", "datadog", "sentry", "postman", "atlassian",
    "shopify", "square", "twilio", "sendgrid", "cloudflare",
    "digitalocean", "mongodb", "elastic", "grafana", "gitlab",
]

LEVER_BASE = "https://api.lever.co/v0/postings/{company}?mode=json"

def _is_relevant(title: str, desc: str) -> bool:
    text = f"{title} {desc}".lower()
    return any(role.lower() in text for role in TARGET_ROLES)

async def fetch_lever_jobs() -> List[Job]:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; jobot/1.0)"}

    async with aiohttp.ClientSession(headers=headers) as session:
        for company in LEVER_COMPANIES:
            url = LEVER_BASE.format(company=company)
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue
                    postings = await resp.json(content_type=None)
                    for p in postings:
                        title    = p.get("text", "").strip()
                        app_url  = p.get("hostedUrl", "")
                        location = p.get("categories", {}).get("location", "Remote")
                        team     = p.get("categories", {}).get("team", "")
                        desc_raw = p.get("descriptionPlain", "")[:300]
                        is_remote = "remote" in location.lower() or "remote" in title.lower()

                        if not title:
                            continue
                        if not _is_relevant(title, f"{desc_raw} {team}"):
                            continue

                        job = Job(
                            title=title,
                            company=company.capitalize(),
                            location="Remote" if is_remote else location,
                            remote=is_remote,
                            url=app_url,
                            description=desc_raw,
                            source=f"lever/{company}",
                        )
                        jobs.append(job)

            except Exception as e:
                logger.debug(f"Lever {company}: {e}")
                continue

    logger.info(f"Lever: {len(jobs)} matching jobs")
    return jobs