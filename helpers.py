










import html
from base import Job


def format_job_message(job: Job) -> str:
    """Format a job into a clean, human-looking Telegram message."""
    title   = html.escape(job.title)
    company = html.escape(job.company or "Unknown")
    desc    = html.escape(job.description[:180]).strip() if job.description else ""
    tags    = ", ".join(job.tech_stack[:5]) if job.tech_stack else ""

    location = "Remote" if job.remote else job.location

    lines = [f"<b>{title}</b>"]
    lines.append(f"{company}  |  {location}")

    if tags:
        lines.append(tags)
    if desc:
        lines.append(f"\n{desc}")

    lines.append(f'\n<a href="{job.url}">View job</a>  |  {job.source}')

    return "\n".join(lines)


def clean_keywords(text: str) -> str:
    return " ".join(text.split()).strip().rstrip(",")


def chunk_list(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]