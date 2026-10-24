from datetime import date, datetime
import shutil
import sqlite3

from db import DATABASE_PATH, hash_pin, initialize_database


event_date = date(2026, 10, 30)

if DATABASE_PATH.exists():
    backup_directory = DATABASE_PATH.parent / ".backups"
    backup_directory.mkdir(exist_ok=True)

    backup_name = f"sandwich_angels_{datetime.now():%Y%m%d_%H%M%S}.db"
    backup_path = backup_directory / backup_name
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"Previous database backed up to: {backup_path}")

initialize_database()

donations = [
    ("bread_slices", 60, date(2026, 10, 20)),
    ("bread_slices", 120, date(2026, 10, 31)),
    ("ham_slices", 40, date(2026, 10, 30)),
    ("cheese_slices", 30, date(2026, 10, 30)),
    ("lettuce_bags", 1, date(2026, 10, 31)),
    ("pickle_small_jars", 1, date(2026, 10, 31)),
    ("mustard_small_bottles", 1, date(2026, 10, 31)),
    ("mayonnaise_small_bottles", 1, date(2026, 10, 31)),
]

demo_signups = [
    ("Demo Volunteer 1", 3),
    ("Demo Volunteer 2", 3),
    ("Demo Volunteer 3", 3),
]

with sqlite3.connect(DATABASE_PATH) as connection:
    connection.execute("DELETE FROM kit_receipts")
    connection.execute("DELETE FROM event_completions")
    connection.execute("DELETE FROM signups")
    connection.execute("DELETE FROM donations")

    connection.executemany(
        """
        INSERT INTO donations (item, quantity, expiry)
        VALUES (?, ?, ?)
        """,
        [
            (item, quantity, expiry.isoformat())
            for item, quantity, expiry in donations
        ],
    )

    connection.executemany(
        """
        INSERT INTO signups (first_name, pin_hash, portions)
        VALUES (?, ?, ?)
        """,
        [
            (name, hash_pin("1234"), portions)
            for name, portions in demo_signups
        ],
    )

print("Demo data loaded for October 30, 2026.")
print("The three demo volunteers signed up for 3 portions each.")