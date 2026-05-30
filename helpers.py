




from scrapers.base import Job

def format_job_message(job: Job) -> str:
    tags = " · ".join(job.tech_stack) if job.tech_stack else ""
    location_str = "🌍 Remote" if job.remote else f"📍 {job.location}"
    msg = (
        f"🚀 {job.title}\n"
        f"🏢 {job.company or 'Unknown'}\n"
        f"{location_str}\n"
        + (f"🛠 {tags}\n" if tags else "")
        + f"🔗 {job.url}\n"
        f"{job.description[:150]}"
    )
    return msg

def clean_keywords(text: str) -> str:
    """Clean up keywords from user input"""
    return text.strip().rstrip(",")