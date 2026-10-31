import os
import sqlite3
from pathlib import Path


DB_PATH = Path(
    os.getenv("CLOUD_TICKETS_DB", "data/cloud_tickets.db")
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


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
