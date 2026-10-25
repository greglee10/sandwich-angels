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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS volunteers (
                volunteer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                display_name TEXT NOT NULL,
                pin_hash TEXT NOT NULL
            )
        """)

        signup_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(signups)")
        }

        if "volunteer_id" not in signup_columns:
            connection.execute(
                """
                ALTER TABLE signups
                ADD COLUMN volunteer_id INTEGER
                REFERENCES volunteers(volunteer_id)
                """
            )



        if "event_date" not in signup_columns:
            connection.execute(
                """
                ALTER TABLE signups
                ADD COLUMN event_date TEXT NOT NULL DEFAULT '2026-10-30'
                """
            )

        if "attended" not in signup_columns:
            connection.execute(
                """
                ALTER TABLE signups
                ADD COLUMN attended INTEGER NOT NULL DEFAULT 0
                CHECK (attended IN (0, 1))
                """
            )


        connection.execute(
            "DROP INDEX IF EXISTS unique_signup_per_event"
        )

        connection.execute("""
            CREATE UNIQUE INDEX unique_signup_per_event
            ON signups(event_date, volunteer_id)
            WHERE volunteer_id IS NOT NULL
        """)


        connection.execute("""
            CREATE TABLE IF NOT EXISTS event_completions (
                event_date TEXT PRIMARY KEY,
                completed_count INTEGER NOT NULL CHECK (completed_count >= 0)
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


def add_signup(first_name, pin, portions, target_portions, event_date):
    first_name = first_name.strip()
    event_date_text = event_date.isoformat()

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
            WHERE event_date = ?
              AND lower(first_name) = lower(?)
            """,
            (event_date_text, first_name),
        ).fetchone()

        if existing_signup:
            connection.rollback()
            return False, "That name already has a signup for this event."

        signed_portions = connection.execute(
            """
            SELECT COALESCE(SUM(portions), 0)
            FROM signups
            WHERE event_date = ?
            """,
            (event_date_text,),
        ).fetchone()[0]

        if signed_portions + portions > target_portions:
            remaining = target_portions - signed_portions
            connection.rollback()
            return False, f"Only {remaining} portion(s) remain."

        connection.execute(
            """
            INSERT INTO signups (first_name, pin_hash, portions, event_date)
            VALUES (?, ?, ?, ?)
            """,
            (first_name, hash_pin(pin), portions, event_date_text),
        )

    return True, "Signup saved."


def load_signups(event_date=None):
    with sqlite3.connect(DATABASE_PATH) as connection:
        if event_date is None:
            rows = connection.execute(
                """
                SELECT signup_id, first_name, portions, event_date, attended
                FROM signups
                ORDER BY signup_id
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT signup_id, first_name, portions, event_date, attended
                FROM signups
                WHERE event_date = ?
                ORDER BY signup_id
                """,
                (event_date.isoformat(),),
            ).fetchall()

    return [
        {
            "signup_id": signup_id,
            "first_name": first_name,
            "portions": portions,
            "event_date": event_date_text,
            "attended": bool(attended),
        }
        for signup_id, first_name, portions, event_date_text, attended in rows
    ]

def verify_pin(pin, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        200_000,
    )

    return secrets.compare_digest(actual_hash, expected_hash)

def register_volunteer(username, display_name, pin):
    username = username.strip().lower()
    display_name = display_name.strip()

    if len(username) < 3 or not username.replace("_", "").isalnum():
        return False, "Username must be at least 3 characters and use only letters, numbers, or underscores."

    if not display_name:
        return False, "Enter your name."

    if len(pin) != 4 or not pin.isdigit():
        return False, "PIN must contain exactly 4 digits."

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(
                """
                INSERT INTO volunteers (username, display_name, pin_hash)
                VALUES (?, ?, ?)
                """,
                (username, display_name, hash_pin(pin)),
            )
    except sqlite3.IntegrityError:
        return False, "That username is already taken."

    return True, "Account created. You can now log in."


def login_volunteer(username, pin):
    username = username.strip()

    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT volunteer_id, username, display_name, pin_hash
            FROM volunteers
            WHERE username = ? COLLATE NOCASE
            """,
            (username,),
        ).fetchone()

    if row is None or not verify_pin(pin, row[3]):
        return None

    return {
        "volunteer_id": row[0],
        "username": row[1],
        "display_name": row[2],
    }

def add_signup_for_volunteer(volunteer_id, portions, target_portions, event_date):
    if portions < 1:
        return False, "Choose at least 1 portion."

    event_date_text = event_date.isoformat()

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        connection.execute("BEGIN IMMEDIATE")

        volunteer = connection.execute(
            """
            SELECT display_name, pin_hash
            FROM volunteers
            WHERE volunteer_id = ?
            """,
            (volunteer_id,),
        ).fetchone()

        if volunteer is None:
            connection.rollback()
            return False, "Please log in again."

        existing = connection.execute(
            """
            SELECT signup_id
            FROM signups
            WHERE volunteer_id = ? AND event_date = ?
            """,
            (volunteer_id, event_date_text),
        ).fetchone()

        if existing:
            connection.rollback()
            return False, "You already signed up for this event."

        signed_portions = connection.execute(
            """
            SELECT COALESCE(SUM(portions), 0)
            FROM signups
            WHERE event_date = ?
            """,
            (event_date_text,),
        ).fetchone()[0]

        if signed_portions + portions > target_portions:
            remaining = target_portions - signed_portions
            connection.rollback()
            return False, f"Only {remaining} portion(s) remain."

        connection.execute(
            """
            INSERT INTO signups
                (first_name, pin_hash, portions, event_date, volunteer_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                volunteer[0],
                volunteer[1],
                portions,
                event_date_text,
                volunteer_id,
            ),
        )

    return True, "Signup saved."


def get_volunteer_signup(volunteer_id, event_date):
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT signup_id, first_name, portions, attended
            FROM signups
            WHERE volunteer_id = ? AND event_date = ?
            """,
            (volunteer_id, event_date.isoformat()),
        ).fetchone()

    if row is None:
        return None

    return {
        "signup_id": row[0],
        "display_name": row[1],
        "portions": row[2],
        "attended": bool(row[3]),
    }


def load_volunteer_history(volunteer_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT event_date, portions, attended
            FROM signups
            WHERE volunteer_id = ?
            ORDER BY event_date DESC
            """,
            (volunteer_id,),
        ).fetchall()

    return [
        {
            "event_date": date.fromisoformat(event_date_text),
            "portions": portions,
            "attended": bool(attended),
        }
        for event_date_text, portions, attended in rows
    ]


def load_admin_signup_history():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT
                s.signup_id,
                COALESCE(v.display_name, s.first_name),
                COALESCE(v.username, ""),
                s.event_date,
                s.portions,
                s.attended
            FROM signups AS s
            LEFT JOIN volunteers AS v
                ON v.volunteer_id = s.volunteer_id
            ORDER BY s.event_date DESC, s.first_name COLLATE NOCASE
            """
        ).fetchall()

    return [
        {
            "signup_id": signup_id,
            "display_name": display_name,
            "username": username,
            "event_date": date.fromisoformat(event_date_text),
            "portions": portions,
            "attended": bool(attended),
        }
        for (
            signup_id,
            display_name,
            username,
            event_date_text,
            portions,
            attended,
        ) in rows
    ]


def set_signup_attendance(signup_id, attended):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            UPDATE signups
            SET attended = ?
            WHERE signup_id = ?
            """,
            (int(attended), signup_id),
        )


def update_volunteer_signup(volunteer_id, event_date, new_portions, target_portions):
    if new_portions < 1:
        return False, "Choose at least 1 portion."

    event_date_text = event_date.isoformat()

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        connection.execute("BEGIN IMMEDIATE")

        signup = connection.execute(
            """
            SELECT signup_id
            FROM signups
            WHERE volunteer_id = ? AND event_date = ?
            """,
            (volunteer_id, event_date_text),
        ).fetchone()

        if signup is None:
            connection.rollback()
            return False, "You do not have a signup for this event."

        other_portions = connection.execute(
            """
            SELECT COALESCE(SUM(portions), 0)
            FROM signups
            WHERE event_date = ? AND signup_id != ?
            """,
            (event_date_text, signup[0]),
        ).fetchone()[0]

        if other_portions + new_portions > target_portions:
            remaining = target_portions - other_portions
            connection.rollback()
            return False, f"Only {remaining} portion(s) are available."

        connection.execute(
            "UPDATE signups SET portions = ? WHERE signup_id = ?",
            (new_portions, signup[0]),
        )

    return True, "Signup updated."


def find_signup(first_name, pin, event_date):
    first_name = first_name.strip()

    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT signup_id, first_name, portions, pin_hash
            FROM signups
            WHERE event_date = ?
              AND lower(first_name) = lower(?)
            """,
            (event_date.isoformat(), first_name),
        ).fetchone()

    if row is None:
        return None

    signup_id, saved_name, portions, stored_hash = row

    if not verify_pin(pin, stored_hash):
        return None

    return {
        "signup_id": signup_id,
        "first_name": saved_name,
        "portions": portions,
    }



def update_signup_portions(first_name, pin, event_date, new_portions, target_portions):
    first_name = first_name.strip()

    if new_portions < 1:
        return False, "Choose at least 1 portion."

    with sqlite3.connect(DATABASE_PATH, timeout=10) as connection:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT signup_id, pin_hash
            FROM signups
            WHERE event_date = ?
              AND lower(first_name) = lower(?)
            """,
            (event_date.isoformat(), first_name),
        ).fetchone()

        if row is None or not verify_pin(pin, row[1]):
            connection.rollback()
            return False, "Name or PIN was not found."

        signup_id = row[0]

        other_portions = connection.execute(
            """
            SELECT COALESCE(SUM(portions), 0)
            FROM signups
            WHERE event_date = ? AND signup_id != ?
            """,
            (event_date.isoformat(), signup_id),
        ).fetchone()[0]

        if other_portions + new_portions > target_portions:
            remaining = target_portions - other_portions
            connection.rollback()
            return False, f"Only {remaining} portion(s) are available."

        connection.execute(
            "UPDATE signups SET portions = ? WHERE signup_id = ?",
            (new_portions, signup_id),
        )

    return True, "Signup updated."



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

def load_completed_count(event_date):
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT completed_count FROM event_completions WHERE event_date = ?",
            (event_date.isoformat(),),
        ).fetchone()

    return row[0] if row else 0


def save_completed_count(event_date, completed_count):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO event_completions (event_date, completed_count)
            VALUES (?, ?)
            ON CONFLICT(event_date)
            DO UPDATE SET completed_count = excluded.completed_count
            """,
            (event_date.isoformat(), completed_count),
        )