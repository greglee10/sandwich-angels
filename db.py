import sqlite3
from datetime import date
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("sandwich_angels.db")


def initialize_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                expiry TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS signups (
                signup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                portions INTEGER NOT NULL CHECK (portions >= 0)
            )
        """)


def replace_donations(donations):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DELETE FROM donations")

        for donation in donations:
            connection.execute(
                """
                INSERT INTO donations (item, quantity, expiry)
                VALUES (?, ?, ?)
                """,
                (
                    donation["item"],
                    donation["quantity"],
                    donation["expiry"].isoformat(),
                ),
            )


def load_donations():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT item, quantity, expiry
            FROM donations
            ORDER BY donation_id
            """
        ).fetchall()

    return [
        {
            "item": item,
            "quantity": quantity,
            "expiry": date.fromisoformat(expiry),
        }
        for item, quantity, expiry in rows
    ]