import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


DB_PATH = os.getenv(
    "DATABASE_PATH",
    "/app/data/vk_content_factory.db"
)


def ensure_data_directory():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    ensure_data_directory()

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                vk_post_id INTEGER,
                error TEXT,
                created_at TEXT NOT NULL,
                published_at TEXT
            )
            """
        )


def add_post(text: str, scheduled_at: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO posts (
                text,
                scheduled_at,
                status,
                created_at
            )
            VALUES (?, ?, 'pending', ?)
            """,
            (
                text,
                scheduled_at,
                datetime.utcnow().isoformat()
            )
        )

        return cursor.lastrowid


def get_pending_posts():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM posts
            WHERE status = 'pending'
            ORDER BY scheduled_at ASC
            """
        )

        return [dict(row) for row in cursor.fetchall()]


def get_due_posts(now_iso: str):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM posts
            WHERE status = 'pending'
              AND scheduled_at <= ?
            ORDER BY scheduled_at ASC
            """,
            (now_iso,)
        )

        return [dict(row) for row in cursor.fetchall()]


def mark_published(post_id: int, vk_post_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE posts
            SET
                status = 'published',
                vk_post_id = ?,
                published_at = ?
            WHERE id = ?
            """,
            (
                vk_post_id,
                datetime.utcnow().isoformat(),
                post_id
            )
        )


def mark_error(post_id: int, error: str):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE posts
            SET
                status = 'error',
                error = ?
            WHERE id = ?
            """,
            (error, post_id)
        )


def get_all_posts(limit: int = 100):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT *
            FROM posts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        return [dict(row) for row in cursor.fetchall()]
