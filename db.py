







import os
import aiosqlite

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    preferences TEXT DEFAULT '{}'
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    keywords TEXT,
                    remote_only BOOLEAN DEFAULT 0,
                    location TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS delivered_jobs (
                    job_hash TEXT PRIMARY KEY,
                    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def add_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def add_subscription(self, user_id: int, keywords: str, remote_only: bool, location: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO subscriptions (user_id, keywords, remote_only, location) VALUES (?, ?, ?, ?)",
                (user_id, keywords, remote_only, location)
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
            rows = await cursor.fetchall()
            return rows

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
            row = await cursor.fetchone()
            return row is not None

    async def mark_delivered(self, job_hash: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO delivered_jobs (job_hash) VALUES (?)",
                (job_hash,)
            )
            await db.commit()