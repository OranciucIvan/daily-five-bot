import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "daily_five.db"))
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "20"))  # 8pm local server time
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
      chat_id INTEGER PRIMARY KEY,
      name TEXT,
      friend_id INTEGER,
      last_reminder TEXT,
      created_at TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id INTEGER,
      entry_date TEXT,
      text TEXT,
      skipped INTEGER DEFAULT 0,
      created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


def upsert_user(chat_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO users(chat_id,name,created_at) VALUES (?,?,?)",
                 (chat_id, name, datetime.utcnow().isoformat()))
    conn.execute("UPDATE users SET name=? WHERE chat_id=?", (name, chat_id))
    conn.commit()
    conn.close()


def set_friend(chat_id: int, friend_id: int) -> bool:
    if chat_id == friend_id:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT friend_id FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    if row and row[0] is not None:
        conn.close()
        return False
    conn.execute("UPDATE users SET friend_id=? WHERE chat_id=?", (friend_id, chat_id))
    conn.commit()
    conn.close()
    return True


def save_entry(chat_id: int, text: str = "", skipped: bool = False):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO entries(chat_id,entry_date,text,skipped,created_at) VALUES (?,?,?,?,?)",
                 (chat_id, date.today().isoformat(), text, 1 if skipped else 0, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def weekly_entries(chat_id: int, days: int = 7):
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT entry_date,text,skipped FROM entries WHERE chat_id=? AND entry_date>=? ORDER BY entry_date",
        (chat_id, since)
    ).fetchall()
    conn.close()
    return rows


def cleanup_old():
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM entries WHERE entry_date<?", (cutoff,))
    conn.commit()
    conn.close()


def get_friend_id(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT friend_id FROM users WHERE chat_id=?", (chat_id,)).fetchone()
    conn.close()
    return row[0] if row else None


def users_with_reminder_due():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chat_id,name,last_reminder FROM users").fetchall()
    conn.close()
    today = date.today().isoformat()
    due = []
    now = datetime.now()
    if now.hour >= REMINDER_HOUR and (now.hour > REMINDER_HOUR or now.minute >= REMINDER_MINUTE):
        for chat_id, name, last in rows:
            if last != today:
                due.append((chat_id, name))
    return due


def mark_reminded(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET last_reminder=? WHERE chat_id=?", (date.today().isoformat(), chat_id))
    conn.commit()
    conn.close()
