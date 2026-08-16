import os
from typing import Optional

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_connection() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0,
            rank INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uid_submissions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            rejection_reason TEXT,
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            UNIQUE(user_id, uid)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdraw_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            withdrawal_info TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_logs (
            id SERIAL PRIMARY KEY,
            actor_id BIGINT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Add language column if missing (migration safety)
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='language'
            ) THEN
                ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en';
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='action_logs' AND column_name='actor_id' AND data_type='integer'
            ) THEN
                ALTER TABLE action_logs ALTER COLUMN actor_id TYPE BIGINT;
            END IF;
        END
        $$;
    """)

    conn.commit()
    cursor.close()
    conn.close()


def ensure_user(telegram_id: int, username: Optional[str], first_name: str, last_name: str, full_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            """
            UPDATE users
            SET username = %s, first_name = %s, last_name = %s, full_name = %s
            WHERE telegram_id = %s
            """,
            (username, first_name, last_name, full_name, telegram_id),
        )
        conn.commit()
        user_id = int(row["id"])
        cursor.close()
        conn.close()
        return user_id

    cursor.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, last_name, full_name, balance, created_at)
        VALUES (%s, %s, %s, %s, %s, 0, NOW()::text)
        RETURNING id
        """,
        (telegram_id, username, first_name, last_name, full_name),
    )
    user_id = int(cursor.fetchone()["id"])
    conn.commit()
    cursor.close()
    conn.close()
    return user_id


def add_submission(user_id: int, uid: str) -> int:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO uid_submissions (user_id, uid, status, created_at) VALUES (%s, %s, 'Pending', NOW()::text) RETURNING id",
        (user_id, uid),
    )
    submission_id = int(cursor.fetchone()["id"])
    conn.commit()
    cursor.close()
    conn.close()
    return submission_id


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def set_user_language(telegram_id: int, language: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = %s WHERE telegram_id = %s", (language, telegram_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_user_stats(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(*) as count FROM uid_submissions WHERE user_id = %s AND status = 'Approved'",
        (user_id,),
    )
    approved = cursor.fetchone()["count"]
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = %s AND transaction_type = 'reward'",
        (user_id,),
    )
    total_earnings = cursor.fetchone()["total"]
    cursor.close()
    conn.close()
    return {
        "balance": float(user["balance"]),
        "approved_count": int(approved),
        "total_earnings": float(total_earnings),
    }


def set_balance(user_id: int, balance: float) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (balance, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def add_transaction(user_id: int, transaction_type: str, amount: float, description: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (user_id, transaction_type, amount, description, created_at) VALUES (%s, %s, %s, %s, NOW()::text)",
        (user_id, transaction_type, amount, description),
    )
    conn.commit()
    cursor.close()
    conn.close()


def create_withdraw_request(user_id: int, amount: float, info: str) -> int:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO withdraw_requests (user_id, amount, withdrawal_info, status, created_at) VALUES (%s, %s, %s, 'Pending', NOW()::text) RETURNING id",
        (user_id, amount, info),
    )
    request_id = int(cursor.fetchone()["id"])
    conn.commit()
    cursor.close()
    conn.close()
    return request_id


def get_pending_uid_submissions() -> list:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM uid_submissions WHERE status = 'Pending' ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def get_pending_withdrawals() -> list:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM withdraw_requests WHERE status = 'Pending' ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def get_all_users() -> list:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def get_submission_by_id(submission_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM uid_submissions WHERE id = %s", (submission_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def is_uid_submitted(uid: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM uid_submissions WHERE uid = %s", (uid,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return bool(row)


def get_withdraw_request_by_id(request_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM withdraw_requests WHERE id = %s", (request_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def update_submission_status(submission_id: int, status: str, rejection_reason: Optional[str] = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE uid_submissions SET status = %s, rejection_reason = %s, reviewed_at = NOW()::text WHERE id = %s",
        (status, rejection_reason, submission_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def update_withdraw_request_status(request_id: int, status: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE withdraw_requests SET status = %s, reviewed_at = NOW()::text WHERE id = %s",
        (status, request_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def log_action(actor_id: Optional[int], action: str, details: str) -> None:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO action_logs (actor_id, action, details, created_at) VALUES (%s, %s, %s, NOW()::text)",
            (actor_id, action, details),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as exc:
        print(f"Failed to log action {action}: {exc}")


def get_stats_summary() -> dict:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Pending'")
    pending_uid = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Approved'")
    approved_uid = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM uid_submissions WHERE status = 'Rejected'")
    rejected_uid = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM withdraw_requests WHERE status = 'Pending'")
    pending_withdrawals = cursor.fetchone()["count"]
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE transaction_type = 'reward'")
    total_rewards_paid = cursor.fetchone()["total"]
    cursor.close()
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT u.id,
               COUNT(CASE WHEN s.status = 'Approved' THEN 1 END) as approved_count,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'reward' THEN t.amount END), 0) as total_earnings
        FROM users u
        LEFT JOIN uid_submissions s ON s.user_id = u.id
        LEFT JOIN transactions t ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY approved_count DESC, total_earnings DESC, u.id ASC
    """)
    rows = cursor.fetchall()
    for index, row in enumerate(rows, start=1):
        cursor.execute("UPDATE users SET rank = %s WHERE id = %s", (index, int(row["id"])))
    conn.commit()
    cursor.close()
    conn.close()


def get_leaderboard() -> list:
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT u.id, u.full_name, u.username, u.telegram_id, u.rank,
               COUNT(CASE WHEN s.status = 'Approved' THEN 1 END) as approved_count,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'reward' THEN t.amount END), 0) as total_earnings
        FROM users u
        LEFT JOIN uid_submissions s ON s.user_id = u.id
        LEFT JOIN transactions t ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY approved_count DESC, total_earnings DESC, u.id ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows
