





import hashlib
from dataclasses import dataclass, field
from typing import List


@dataclass
class Job:
    title: str
    company: str
    location: str
    remote: bool = False
    tech_stack: List[str] = field(default_factory=list)
    url: str = ""
    description: str = ""
    source: str = "unknown"

    def to_hash(self) -> str:
        # FIX: Python's built-in hash() is randomised per process (PYTHONHASHSEED).
        # The same job got different hashes on every restart → duplicate deliveries.
        # hashlib.sha256 is stable and deterministic across all runs.
        raw = f"{self.title}|{self.company}|{self.url}".lower()
        return hashlib.sha256(raw.encode()).hexdigest()