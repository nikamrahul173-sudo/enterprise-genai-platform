import json
import os
import re
import sqlite3
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


DB_PATH = Path(os.getenv("CLOUD_RAG_DB", "data/cloud_rag.db"))
MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PAGES = 50
MAX_TEXT_CHARS = 200_000


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                pages INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)


def upload_pdf(filename, content):
    if len(content) > MAX_PDF_BYTES:
        raise ValueError("PDF exceeds 5 MB limit.")

    if not content.startswith(b"%PDF-"):
        raise ValueError("File is not a valid PDF.")

    try:
        reader = PdfReader(BytesIO(content), strict=False)
        page_count = len(reader.pages)
    except Exception:
        raise ValueError("Unable to read PDF.")

    if page_count < 1 or page_count > MAX_PAGES:
        raise ValueError("PDF must contain 1 to 50 pages.")

    extracted = []
    total_chars = 0

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            continue

        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        total_chars += len(text)

        if total_chars > MAX_TEXT_CHARS:
            raise ValueError("PDF text exceeds processing limit.")

        for start in range(0, len(text), 900):
            chunk = text[start:start + 900]
            if chunk.strip():
                extracted.append((page_number, chunk))

    if not extracted:
        raise ValueError("No readable text found in PDF.")

    initialize()

    with connect() as db:
        cursor = db.execute(
            "INSERT INTO documents(filename, pages) VALUES (?, ?)",
            (filename[:200], page_count),
        )
        document_id = cursor.lastrowid

        db.executemany(
            "INSERT INTO chunks(document_id, page, content) VALUES (?, ?, ?)",
            [(document_id, page, text) for page, text in extracted],
        )

    return {
        "document_id": document_id,
        "filename": filename[:200],
        "pages": page_count,
        "chunks": len(extracted),
    }


def list_documents():
    initialize()
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM documents ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_document(document_id):
    initialize()
    with connect() as db:
        row = db.execute(
            "SELECT id FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()

        if not row:
            return False

        db.execute(
            "DELETE FROM chunks WHERE document_id = ?",
            (document_id,),
        )
        db.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,),
        )

    return True


def search_documents(question, limit=4):
    initialize()

    terms = set(re.findall(r"[a-z0-9]{3,}", question.lower()))
    stopwords = {
        "the", "and", "for", "with", "what", "how",
        "from", "this", "that", "are", "can", "does",
        "about", "please", "tell", "give",
    }
    terms -= stopwords

    if not terms:
        return []

    with connect() as db:
        rows = db.execute("""
            SELECT c.document_id, c.page, c.content, d.filename
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
        """).fetchall()

    scored = []

    for row in rows:
        text = row["content"].lower()
        score = sum(text.count(term) for term in terms)

        if score > 0:
            item = dict(row)
            item["score"] = score
            scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:limit]
