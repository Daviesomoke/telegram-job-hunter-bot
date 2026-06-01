








import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from db import Database
from reddit import fetch_reddit_jobs
from rss import fetch_rss_jobs
from scraper_remoteok import fetch_remoteok_jobs
from scraper_himalayas import fetch_himalayas_jobs
from scraper_lever import fetch_lever_jobs
from base import Job
from config import REDDIT_SUBREDDITS, RSS_FEEDS, MAX_JOBS_PER_MESSAGE
from helpers import format_job_message, chunk_list

logger = logging.getLogger(__name__)


async def fetch_all_jobs() -> list:
    """Fetch jobs from ALL sources concurrently."""
    results = await asyncio.gather(
        fetch_reddit_jobs(REDDIT_SUBREDDITS),
        fetch_rss_jobs(RSS_FEEDS),
        fetch_remoteok_jobs(),
        fetch_himalayas_jobs(),
        fetch_lever_jobs(),
        return_exceptions=True
    )

    source_names = ["Reddit", "RSS", "RemoteOK", "Himalayas", "Lever"]
    all_jobs = []
    for name, res in zip(source_names, results):
        if isinstance(res, list):
            all_jobs.extend(res)
            logger.info(f"{name}: {len(res)} jobs")
        elif isinstance(res, Exception):
            logger.error(f"{name} scraper failed: {res}")

    logger.info(f"Total fetched: {len(all_jobs)} jobs from all sources")
    return all_jobs


async def process_and_send(bot: Bot, db: Database):
    """Main pipeline: fetch → deduplicate → match → deliver."""
    try:
        logger.info("Pipeline started")
        jobs = await fetch_all_jobs()

        # Deduplicate against already-delivered jobs
        new_jobs = []
        for job in jobs:
            h = job.to_hash()
            if not await db.is_job_delivered(h):
                new_jobs.append(job)
                await db.mark_delivered(h)

        if not new_jobs:
            logger.info("No new jobs this cycle")
            return

        logger.info(f"{len(new_jobs)} new jobs to deliver")
        subs = await db.get_all_subscriptions()
        if not subs:
            return

        # Match jobs to each subscriber's preferences
        user_jobs: dict = {}
        for user_id, keywords, remote_only, location in subs:
            matched = []
            for job in new_jobs:
                if remote_only and not job.remote:
                    continue
                if location and location.lower() not in job.location.lower():
                    continue
                if keywords:
                    searchable = f"{job.title} {job.description} {' '.join(job.tech_stack)}".lower()
                    if not any(kw.strip().lower() in searchable for kw in keywords.split(",")):
                        continue
                matched.append(job)
            if matched:
                user_jobs[user_id] = matched

        logger.info(f"Sending to {len(user_jobs)} subscribers")

        for user_id, jobs_list in user_jobs.items():
            for chunk in chunk_list(jobs_list, MAX_JOBS_PER_MESSAGE):
                text = "\n\n".join(format_job_message(j) for j in chunk)
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 <b>New Jobs Found!</b>\n\n{text}",
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(0.05)
                except TelegramForbiddenError:
                    logger.info(f"User {user_id} blocked the bot")
                except TelegramBadRequest as e:
                    logger.warning(f"Bad request for {user_id}: {e}")
                except Exception as e:
                    logger.error(f"Send failed for {user_id}: {e}")

        logger.info("Pipeline complete")

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)