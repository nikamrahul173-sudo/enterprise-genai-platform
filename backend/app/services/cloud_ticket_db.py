from contextlib import contextmanager
import os
import sqlite3
from pathlib import Path


DB_PATH = Path(
    os.getenv("CLOUD_TICKETS_DB", "data/cloud_tickets.db")
)


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_cloud_tickets():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS cloud_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_cloud_ticket(title, description):
    initialize_cloud_tickets()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO cloud_tickets (title, description)
            VALUES (?, ?)
            """,
            (title, description),
        )
        ticket_id = cursor.lastrowid

    return get_cloud_ticket(ticket_id)


def get_cloud_ticket(ticket_id):
    initialize_cloud_tickets()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM cloud_tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return dict(row) if row else None


def list_cloud_tickets():
    initialize_cloud_tickets()

    if os.getenv("PUBLIC_DEMO_MODE", "0") == "1":
        seed_demo_tickets()

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM cloud_tickets ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def update_cloud_ticket_status(ticket_id, status):
    allowed_statuses = {"Open", "In Progress", "Resolved", "Closed"}

    if status not in allowed_statuses:
        raise ValueError("Invalid ticket status")

    initialize_cloud_tickets()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE cloud_tickets
            SET status = ?
            WHERE id = ?
            """,
            (status, ticket_id),
        )

        if cursor.rowcount == 0:
            return None

    return get_cloud_ticket(ticket_id)


def seed_demo_tickets():
    """Populate an empty public-demo database with synthetic IT tickets."""
    demo_tickets = [
        (
            "VPN connection fails on Windows 11",
            "Demo: Employee cannot connect to the corporate VPN after a password reset.",
            "Open",
        ),
        (
            "Outlook emails not syncing",
            "Demo: Outlook desktop client is not receiving new Microsoft 365 emails.",
            "In Progress",
        ),
        (
            "Active Directory account locked",
            "Demo: User account locked after repeated unsuccessful sign-in attempts.",
            "Resolved",
        ),
        (
            "Laptop running slowly",
            "Demo: Windows laptop has high CPU usage and slow startup performance.",
            "Open",
        ),
        (
            "Microsoft 365 MFA enrollment issue",
            "Demo: Employee needs assistance registering a new authenticator device.",
            "Closed",
        ),
    ]

    initialize_cloud_tickets()

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT COUNT(*) FROM cloud_tickets"
        ).fetchone()[0]

        if existing > 0:
            return 0

        connection.executemany(
            """
            INSERT INTO cloud_tickets (title, description, status)
            VALUES (?, ?, ?)
            """,
            demo_tickets,
        )

    return len(demo_tickets)
