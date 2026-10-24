import sqlite3
import hashlib
import secrets
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
            CREATE TABLE IF NOT EXISTS kit_receipts (
                signup_id INTEGER PRIMARY KEY,
                received INTEGER NOT NULL DEFAULT 0 CHECK (received IN (0, 1))
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



def hash_pin(pin):
    salt = secrets.token_bytes(16)
    pin_hash = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        200_000,
    )
    return f"{salt.hex()}:{pin_hash.hex()}"

def add_signup(first_name, pin, portions, target_portions):
    first_name = first_name.strip()

    if not first_name:
        return False, "Enter a first name."

    if len(pin) != 4 or not pin.isdigit():
        return False, "PIN must contain exactly 4 digits."

    if portions < 1:
        return False, "Choose at least 1 portion."

    if target_portions < 1:
        return False, "The target must be at least 1 portion."

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        connection.execute("BEGIN IMMEDIATE")

        existing_signup = connection.execute(
            """
            SELECT signup_id
            FROM signups
            WHERE lower(first_name) = lower(?)
            """,
            (first_name,),
        ).fetchone()

        if existing_signup:
            connection.rollback()
            return False, "That name already has a signup."

        signed_portions = connection.execute(
            "SELECT COALESCE(SUM(portions), 0) FROM signups"
        ).fetchone()[0]

        if signed_portions + portions > target_portions:
            remaining = target_portions - signed_portions
            connection.rollback()
            return False, f"Only {remaining} portion(s) remain."

        connection.execute(
            """
            INSERT INTO signups (first_name, pin_hash, portions)
            VALUES (?, ?, ?)
            """,
            (first_name, hash_pin(pin), portions),
        )

    return True, "Signup saved."


def load_signups():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT signup_id, first_name, portions
            FROM signups
            ORDER BY signup_id
            """
        ).fetchall()

    return [
        {
            "signup_id": signup_id,
            "first_name": first_name,
            "portions": portions,
        }
        for signup_id, first_name, portions in rows
    ]


def load_received_signup_ids():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT signup_id FROM kit_receipts WHERE received = 1"
        ).fetchall()

    return {row[0] for row in rows}


def set_kit_received(signup_id, received):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO kit_receipts (signup_id, received)
            VALUES (?, ?)
            ON CONFLICT(signup_id)
            DO UPDATE SET received = excluded.received
            """,
            (signup_id, int(received)),
        )