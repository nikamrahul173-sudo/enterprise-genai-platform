import json
import sqlite3

from backend.app.services.cloud_ticket_db import (
    DB_PATH,
    initialize_cloud_tickets,
)


def connection():
    initialize_cloud_tickets()
    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    return db


def ensure_columns():
    with connection() as db:
        existing = {
            row[1]
            for row in db.execute("PRAGMA table_info(cloud_tickets)")
        }

        additions = {
            "ai_analysis": "TEXT",
            "review_status": "TEXT DEFAULT 'Pending'",
            "reviewed_by": "TEXT",
            "review_notes": "TEXT",
        }

        for name, definition in additions.items():
            if name not in existing:
                db.execute(
                    f"ALTER TABLE cloud_tickets ADD COLUMN {name} {definition}"
                )


def serialize_ticket(row):
    if row is None:
        return None

    ticket = dict(row)

    if ticket.get("ai_analysis"):
        try:
            ticket["ai_analysis"] = json.loads(ticket["ai_analysis"])
        except (ValueError, TypeError):
            ticket["ai_analysis"] = None

    return ticket


def get_ticket(ticket_id):
    ensure_columns()

    with connection() as db:
        row = db.execute(
            "SELECT * FROM cloud_tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return serialize_ticket(row)


def get_tickets():
    ensure_columns()

    with connection() as db:
        rows = db.execute(
            "SELECT * FROM cloud_tickets ORDER BY id DESC"
        ).fetchall()

    return [serialize_ticket(row) for row in rows]


def save_analysis(ticket_id, analysis):
    ensure_columns()

    with connection() as db:
        cursor = db.execute(
            """
            UPDATE cloud_tickets
            SET ai_analysis = ?,
                review_status = 'Pending',
                reviewed_by = NULL,
                review_notes = NULL
            WHERE id = ?
            """,
            (json.dumps(analysis), ticket_id),
        )

        if cursor.rowcount == 0:
            return None

    return get_ticket(ticket_id)


def save_review(ticket_id, decision, reviewed_by, notes):
    ensure_columns()

    with connection() as db:
        row = db.execute(
            "SELECT ai_analysis FROM cloud_tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if row is None:
            return None

        if not row["ai_analysis"]:
            raise ValueError("Run AI analysis before engineer review.")

        db.execute(
            """
            UPDATE cloud_tickets
            SET review_status = ?,
                reviewed_by = ?,
                review_notes = ?
            WHERE id = ?
            """,
            (decision, reviewed_by, notes, ticket_id),
        )

    return get_ticket(ticket_id)
