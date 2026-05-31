






import html
from scrapers.base import Job


def format_job_message(job: Job) -> str:
    """Format a Job into a clean Telegram message (HTML parse mode)."""
    tags = " · ".join(job.tech_stack) if job.tech_stack else ""
    location_str = "🌍 Remote" if job.remote else f"📍 {job.location}"

    # Escape user-supplied text to prevent HTML injection
    title = html.escape(job.title)
    company = html.escape(job.company or "Unknown")
    description = html.escape(job.description[:200]) if job.description else ""

    lines = [
        f"<b>🚀 {title}</b>",
        f"🏢 {company}",
        location_str,
    ]
    if tags:
        lines.append(f"🛠 {html.escape(tags)}")
    if description:
        lines.append(f"<i>{description}…</i>")
    lines.append(f"🔗 <a href='{job.url}'>View Job</a>")

    return "\n".join(lines)


def clean_keywords(text: str) -> str:
    """Normalise keyword string from user input."""
    # Remove flags leftovers, strip whitespace and trailing commas
    return " ".join(text.split()).strip().rstrip(",")


def chunk_list(lst: list, size: int):
    """Split a list into chunks of given size."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]