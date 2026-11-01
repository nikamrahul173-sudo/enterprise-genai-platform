
import hashlib
import os
import re
import sqlite3
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DB_PATH = Path(os.getenv("CLOUD_RAG_DB", "data/cloud_rag.db"))

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PAGES = 50
MAX_TEXT_CHARS = 200_000
CHUNK_SIZE = 900

KNOWLEDGE_DIR = (
    Path(__file__).resolve().parents[3]
    / "knowledge"
    / "cloud"
)


# --------------------------------------------------
# Database
# --------------------------------------------------

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


# --------------------------------------------------
# PDF Upload and Indexing
# --------------------------------------------------

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

        for start in range(0, len(text), CHUNK_SIZE):
            chunk = text[start:start + CHUNK_SIZE]

            if chunk.strip():
                extracted.append((page_number, chunk))

    if not extracted:
        raise ValueError("No readable text found in PDF.")

    initialize()

    with connect() as db:
        cursor = db.execute(
            """
            INSERT INTO documents(filename, pages)
            VALUES (?, ?)
            """,
            (filename[:200], page_count),
        )

        document_id = cursor.lastrowid

        db.executemany(
            """
            INSERT INTO chunks(document_id, page, content)
            VALUES (?, ?, ?)
            """,
            [
                (document_id, page, text)
                for page, text in extracted
            ],
        )

    return {
        "document_id": document_id,
        "filename": filename[:200],
        "pages": page_count,
        "chunks": len(extracted),
    }


# --------------------------------------------------
# Document Listing
# --------------------------------------------------

def list_documents():
    initialize()

    with connect() as db:
        rows = db.execute(
            """
            SELECT *
            FROM documents
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# Document Deletion
# --------------------------------------------------

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


# --------------------------------------------------
# Keyword Retrieval
# --------------------------------------------------

def search_documents(question, limit=4):
    initialize()

    terms = set(
        re.findall(r"[a-z0-9]{3,}", question.lower())
    )

    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "what",
        "how",
        "from",
        "this",
        "that",
        "are",
        "can",
        "does",
        "about",
        "please",
        "tell",
        "give",
    }

    terms -= stopwords

    if not terms:
        return []

    with connect() as db:
        rows = db.execute("""
            SELECT
                c.document_id,
                c.page,
                c.content,
                d.filename
            FROM chunks c
            JOIN documents d
                ON d.id = c.document_id
        """).fetchall()

    scored = []

    for row in rows:
        text = row["content"].lower()

        score = sum(
            text.count(term)
            for term in terms
        )

        if score > 0:
            item = dict(row)
            item["score"] = score
            scored.append(item)

    scored.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored[:limit]


# --------------------------------------------------
# Bundled Cloud Knowledge Seeding
# --------------------------------------------------

def seed_cloud_knowledge():
    """
    Index bundled Markdown knowledge articles.

    Features:
    - Uses version-controlled Markdown files.
    - Prevents duplicate indexing.
    - Replaces outdated versions of an article.
    - Preserves separately uploaded PDF documents.
    - Rebuilds knowledge after an ephemeral DB reset.
    """

    if not KNOWLEDGE_DIR.is_dir():
        return 0

    initialize()
    seeded = 0

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            continue

        if len(content) > MAX_TEXT_CHARS:
            raise ValueError(
                f"Knowledge article too large: {path.name}"
            )

        digest = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()[:16]

        filename = f"{path.name}@{digest}"

        chunks = [
            content[start:start + CHUNK_SIZE]
            for start in range(0, len(content), CHUNK_SIZE)
        ]

        with connect() as db:
            existing = db.execute(
                """
                SELECT id
                FROM documents
                WHERE filename = ?
                """,
                (filename,),
            ).fetchone()

            if existing:
                continue

            # Remove outdated versions of this
            # bundled Markdown article only.
            older = db.execute(
                """
                SELECT id
                FROM documents
                WHERE filename LIKE ?
                """,
                (path.name + "@%",),
            ).fetchall()

            for old in older:
                db.execute(
                    """
                    DELETE FROM chunks
                    WHERE document_id = ?
                    """,
                    (old["id"],),
                )

                db.execute(
                    """
                    DELETE FROM documents
                    WHERE id = ?
                    """,
                    (old["id"],),
                )

            cursor = db.execute(
                """
                INSERT INTO documents(filename, pages)
                VALUES (?, ?)
                """,
                (filename, 1),
            )

            document_id = cursor.lastrowid

            db.executemany(
                """
                INSERT INTO chunks(
                    document_id,
                    page,
                    content
                )
                VALUES (?, ?, ?)
                """,
                [
                    (document_id, 1, chunk)
                    for chunk in chunks
                ],
            )

            seeded += 1

    return seeded
