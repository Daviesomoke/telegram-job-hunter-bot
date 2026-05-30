








from database.db import Database
from scrapers.reddit import fetch_reddit_jobs
from scrapers.rss import fetch_rss_jobs
from scrapers.base import Job
from config import REDDIT_SUBREDDITS, RSS_FEEDS, MAX_JOBS_PER_MESSAGE
from utils.helpers import format_job_message
from aiogram import Bot
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_all_jobs() -> list[Job]:
    tasks = [
        fetch_reddit_jobs(REDDIT_SUBREDDITS),
        fetch_rss_jobs(RSS_FEEDS),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_jobs = []
    for res in results:
        if isinstance(res, list):
            all_jobs.extend(res)
        elif isinstance(res, Exception):
            logger.error(f"Scraper error: {res}")
    return all_jobs

async def process_and_send(bot: Bot, db: Database):
    try:
        logger.info("Starting job fetch cycle...")
        jobs = await fetch_all_jobs()
        logger.info(f"Fetched {len(jobs)} total jobs")
        
        new_jobs = []
        for job in jobs:
            if not await db.is_job_delivered(job.to_hash()):
                new_jobs.append(job)
                await db.mark_delivered(job.to_hash())
        
        if not new_jobs:
            logger.info("No new jobs to deliver")
            return
        
        logger.info(f"Found {len(new_jobs)} new jobs")
        subs = await db.get_all_subscriptions()
        
        if not subs:
            logger.info("No subscribers yet")
            return
        
        user_jobs = {}
        for user_id, keywords, remote_only, location in subs:
            matched = []
            for job in new_jobs:
                if remote_only and not job.remote:
                    continue
                if location and location.lower() not in job.location.lower():
                    continue
                if keywords:
                    text = f"{job.title} {job.description} {' '.join(job.tech_stack)}".lower()
                    if not any(kw.strip().lower() in text for kw in keywords.split(",")):
                        continue
                matched.append(job)
            if matched:
                user_jobs[user_id] = matched
        
        for user_id, jobs_list in user_jobs.items():
            for i in range(0, len(jobs_list), MAX_JOBS_PER_MESSAGE):
                chunk = jobs_list[i:i+MAX_JOBS_PER_MESSAGE]
                text = "\n\n".join(format_job_message(j) for j in chunk)
                try:
                    await bot.send_message(user_id, f"🔔 *New Jobs Found!*\n\n{text}", 
                                         disable_web_page_preview=True, parse_mode="Markdown")
                    await asyncio.sleep(0.5)  # Rate limit protection
                except Exception as e:
                    logger.error(f"Failed to send to {user_id}: {e}")
                    continue
        
        logger.info("Job delivery cycle complete")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)