
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# Store database inside the project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = PROJECT_ROOT / "data" / "tickets.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Unclassified',
                priority TEXT NOT NULL DEFAULT 'Unassigned',
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
        """)

        connection.commit()


def create_ticket(title, description):
    title = title.strip()
    description = description.strip()

    if not title or not description:
        raise ValueError(
            "Ticket title and description cannot be empty."
        )

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO tickets (
                title,
                description,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            title,
            description,
            created_at
        ))

        ticket_id = cursor.lastrowid
        connection.commit()

    return get_ticket(ticket_id)


def get_ticket(ticket_id):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

    if row is None:
        return None

    return dict(row)


def list_tickets():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM tickets
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]





def save_ticket_analysis(ticket_id, analysis):
    import json

    with get_connection() as connection:

        # Add AI analysis column if it doesn't exist yet
        columns = connection.execute(
            "PRAGMA table_info(tickets)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        if "ai_analysis" not in column_names:
            connection.execute("""
                ALTER TABLE tickets
                ADD COLUMN ai_analysis TEXT
            """)

        # Save AI analysis as JSON
        cursor = connection.execute("""
            UPDATE tickets
            SET ai_analysis = ?
            WHERE id = ?
        """, (
            json.dumps(analysis),
            ticket_id
        ))

        connection.commit()

        if cursor.rowcount == 0:
            return False

    return True



# -------------------------------------
# Engineer Review & Approval Storage
# -------------------------------------

def initialize_review_columns():
    """
    Add review fields to existing tickets safely.
    Existing ticket records are preserved.
    """

    with get_connection() as connection:
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(tickets)"
            ).fetchall()
        }

        new_columns = {
            "review_status": "TEXT NOT NULL DEFAULT 'Pending'",
            "reviewed_by": "TEXT",
            "review_notes": "TEXT",
            "reviewed_at": "TEXT",
        }

        for column_name, column_definition in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE tickets "
                    f"ADD COLUMN {column_name} {column_definition}"
                )

        connection.commit()


def save_engineer_review(
    ticket_id,
    decision,
    reviewed_by,
    notes
):
    """
    Store a human review decision.
    Does not execute any IT or cloud action.
    """

    valid_decisions = ("Approved", "Rejected")

    if decision not in valid_decisions:
        raise ValueError(
            "Decision must be Approved or Rejected."
        )

    reviewed_by = reviewed_by.strip()
    notes = notes.strip()

    if not reviewed_by:
        raise ValueError(
            "Engineer name is required."
        )

    if not notes:
        raise ValueError(
            "Review notes are required."
        )

    initialize_review_columns()

    reviewed_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE tickets
            SET
                review_status = ?,
                reviewed_by = ?,
                review_notes = ?,
                reviewed_at = ?
            WHERE id = ?
              AND ai_analysis IS NOT NULL
            """,
            (
                decision,
                reviewed_by,
                notes,
                reviewed_at,
                ticket_id,
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            raise ValueError(
                "Ticket not found or AI analysis missing."
            )

    return get_ticket(ticket_id)




# -------------------------------------
# Ticket Status Management
# -------------------------------------

def update_ticket_status(ticket_id, new_status):
    """
    Update ticket status without deleting ticket data.
    """

    valid_statuses = (
        "Open",
        "In Progress",
        "Resolved",
        "Closed",
    )

    if new_status not in valid_statuses:
        raise ValueError("Invalid ticket status.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE tickets
            SET status = ?
            WHERE id = ?
            """,
            (new_status, ticket_id),
        )

        connection.commit()

        if cursor.rowcount == 0:
            raise ValueError("Ticket not found.")

    return get_ticket(ticket_id)
