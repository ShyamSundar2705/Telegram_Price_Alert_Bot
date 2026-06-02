import aiosqlite
from datetime import datetime

DB_PATH = "/app/data/prices.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watched_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                platform TEXT DEFAULT 'amazon',
                product_url TEXT,
                product_name TEXT,
                current_price REAL,
                last_checked DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.commit()


async def add_watch(user_id: str, query: str, platform: str, product_url: str,
                    product_name: str, current_price: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO watched_items
               (user_id, query, platform, product_url, product_name, current_price, last_checked)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, query, platform, product_url, product_name,
             round(current_price, 2), datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def remove_watch(user_id: str, item_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE watched_items SET is_active = 0 WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        )
        await db.commit()


async def get_user_watches(user_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM watched_items WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_active_watches() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM watched_items WHERE is_active = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_price(item_id: int, new_price: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE watched_items SET current_price = ?, last_checked = ? WHERE id = ?",
            (round(new_price, 2), datetime.now().isoformat(), item_id)
        )
        await db.commit()
