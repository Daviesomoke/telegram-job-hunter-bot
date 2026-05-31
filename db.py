










import os
import logging
import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")  # Better concurrent write performance
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id    INTEGER PRIMARY KEY,
                    username   TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    keywords    TEXT,
                    remote_only BOOLEAN DEFAULT 0,
                    location    TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS delivered_jobs (
                    job_hash     TEXT PRIMARY KEY,
                    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Auto-clean delivered jobs older than 30 days to keep DB small
            await db.execute("""
                DELETE FROM delivered_jobs
                WHERE delivered_at < datetime('now', '-30 days')
            """)
            await db.commit()
        logger.info(f"Database ready at {self.db_path}")

    async def add_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            # Update username in case they changed it
            await db.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (username, user_id)
            )
            await db.commit()

    async def add_subscription(self, user_id: int, keywords: str,
                                remote_only: bool, location: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO subscriptions (user_id, keywords, remote_only, location)
                   VALUES (?, ?, ?, ?)""",
                (user_id, keywords, int(remote_only), location)
            )
            await db.commit()

    async def remove_subscription(self, user_id: int, sub_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
                (sub_id, user_id)
            )
            await db.commit()

    async def get_subscriptions(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, keywords, remote_only, location FROM subscriptions WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchall()

    async def get_all_subscriptions(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id, keywords, remote_only, location FROM subscriptions"
            )
            return await cursor.fetchall()

    async def is_job_delivered(self, job_hash: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM delivered_jobs WHERE job_hash = ?", (job_hash,)
            )
            return await cursor.fetchone() is not None

    async def mark_delivered(self, job_hash: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO delivered_jobs (job_hash) VALUES (?)",
                (job_hash,)
            )
            await db.commit()

    async def get_user_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_subscription_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM subscriptions")
            row = await cursor.fetchone()
            return row[0] if row else 0