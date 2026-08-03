import asyncio
import sqlite3
from pathlib import Path
from typing import Optional

from bot.config import DATA_DIR

DB_PATH = DATA_DIR / "bot.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0,
            rank INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS uid_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            rejection_reason TEXT,
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            UNIQUE(user_id, uid)
        );

        CREATE TABLE IF NOT EXISTS withdraw_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            withdrawal_info TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute("PRAGMA table_info(users)")
    user_columns = {row[1] for row in cursor.fetchall()}
    if "language" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")

    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user(telegram_id: int, username: Optional[str], first_name: str, last_name: str, full_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            """
            UPDATE users
            SET username = ?, first_name = ?, last_name = ?, full_name = ?
            WHERE telegram_id = ?
            """,
            (username, first_name, last_name, full_name, telegram_id),
        )
        conn.commit()
        conn.close()
        return int(row["id"])

    cursor.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, last_name, full_name, balance, created_at)
        VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
        """,
        (telegram_id, username, first_name, last_name, full_name),
    )
    user_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return user_id


def add_submission(user_id: int, uid: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO uid_submissions (user_id, uid, status, created_at) VALUES (?, ?, 'Pending', datetime('now'))",
        (user_id, uid),
    )
    submission_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return submission_id


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_telegram_id(telegram_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
    conn.close()
    return row


def set_user_language(telegram_id: int, language: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
    conn.commit()
    conn.close()


def get_user_stats(user_id: int) -> dict:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    approved = conn.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE user_id = ? AND status = 'Approved'", (user_id,)).fetchone()["count"]
    total_earnings = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND transaction_type = 'reward'", (user_id,)).fetchone()["total"]
    conn.close()
    return {
        "balance": float(user["balance"]),
        "approved_count": int(approved),
        "total_earnings": float(total_earnings),
    }


def set_balance(user_id: int, balance: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET balance = ? WHERE id = ?", (balance, user_id))
    conn.commit()
    conn.close()


def add_transaction(user_id: int, transaction_type: str, amount: float, description: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (user_id, transaction_type, amount, description, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (user_id, transaction_type, amount, description),
    )
    conn.commit()
    conn.close()


def create_withdraw_request(user_id: int, amount: float, info: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO withdraw_requests (user_id, amount, withdrawal_info, status, created_at) VALUES (?, ?, ?, 'Pending', datetime('now'))",
        (user_id, amount, info),
    )
    request_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return request_id


def get_pending_uid_submissions() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM uid_submissions WHERE status = 'Pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_pending_withdrawals() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM withdraw_requests WHERE status = 'Pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_all_users() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_submission_by_id(submission_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM uid_submissions WHERE id = ?", (submission_id,)).fetchone()
    conn.close()
    return row


def update_submission_status(submission_id: int, status: str, rejection_reason: Optional[str] = None) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE uid_submissions SET status = ?, rejection_reason = ?, reviewed_at = datetime('now') WHERE id = ?",
        (status, rejection_reason, submission_id),
    )
    conn.commit()
    conn.close()


def update_withdraw_request_status(request_id: int, status: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE withdraw_requests SET status = ?, reviewed_at = datetime('now') WHERE id = ?",
        (status, request_id),
    )
    conn.commit()
    conn.close()


def log_action(actor_id: Optional[int], action: str, details: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO action_logs (actor_id, action, details, created_at) VALUES (?, ?, ?, datetime('now'))",
        (actor_id, action, details),
    )
    conn.commit()
    conn.close()


def get_stats_summary() -> dict:
    conn = get_connection()
    total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
    pending_uid = conn.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Pending'").fetchone()["count"]
    approved_uid = conn.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Approved'").fetchone()["count"]
    rejected_uid = conn.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Rejected'").fetchone()["count"]
    pending_withdrawals = conn.execute("SELECT COUNT(*) as count FROM withdraw_requests WHERE status = 'Pending'").fetchone()["count"]
    total_rewards_paid = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE transaction_type = 'reward'").fetchone()["total"]
    conn.close()
    return {
        "total_users": int(total_users),
        "pending_uid_submissions": int(pending_uid),
        "approved_uid_submissions": int(approved_uid),
        "rejected_uid_submissions": int(rejected_uid),
        "pending_withdrawals": int(pending_withdrawals),
        "total_rewards_paid": float(total_rewards_paid),
    }


def refresh_ranks() -> None:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT u.id,
               COUNT(CASE WHEN s.status = 'Approved' THEN 1 END) as approved_count,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'reward' THEN t.amount END), 0) as total_earnings
        FROM users u
        LEFT JOIN uid_submissions s ON s.user_id = u.id
        LEFT JOIN transactions t ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY approved_count DESC, total_earnings DESC, u.id ASC
        """
    ).fetchall()
    for index, row in enumerate(rows, start=1):
        conn.execute("UPDATE users SET rank = ? WHERE id = ?", (index, int(row["id"])))
    conn.commit()
    conn.close()


def get_leaderboard() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT u.id, u.full_name, u.username, u.telegram_id, u.rank,
               COUNT(CASE WHEN s.status = 'Approved' THEN 1 END) as approved_count,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'reward' THEN t.amount END), 0) as total_earnings
        FROM users u
        LEFT JOIN uid_submissions s ON s.user_id = u.id
        LEFT JOIN transactions t ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY approved_count DESC, total_earnings DESC, u.id ASC
        """
    ).fetchall()
    conn.close()
    return rows
