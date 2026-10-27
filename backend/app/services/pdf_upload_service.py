
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.app.services.pdf_service import extract_text_from_pdf
from backend.app.services.pdf_loader import split_text_into_chunks
from backend.app.services.vector_store import collection, get_embedding


PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def upload_pdf_to_chromadb(file: UploadFile) -> dict:
    filename = Path(file.filename or "").name

    if Path(filename).suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are allowed.")

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")

    # SHA-256 fingerprint of the uploaded PDF
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # Check whether this exact PDF was already uploaded
    existing = collection.get(
        where={"file_hash": file_hash},
        limit=1
    )

    if existing["ids"]:
        raise ValueError("This PDF is already uploaded.")

    # Also protect legacy records without a file_hash
    existing_by_filename = collection.get(
        where={"source": filename},
        include=["metadatas"]
    )

    if existing_by_filename["ids"]:
        raise ValueError(
            "A PDF with this filename is already indexed. "
            "Rename or remove the existing document before uploading."
        )

    document_id = uuid4().hex
    saved_path = UPLOAD_DIR / f"{document_id}.pdf"
    saved_path.write_bytes(pdf_bytes)

    try:
        text = extract_text_from_pdf(str(saved_path))

        if not text.strip():
            raise ValueError("No readable text found in PDF.")

        chunks = split_text_into_chunks(text)

        if not chunks:
            raise ValueError("No policy sections found in PDF.")

        embeddings = [get_embedding(chunk) for chunk in chunks]

        collection.upsert(
            ids=[
                f"{document_id}_{index}"
                for index in range(len(chunks))
            ],
            documents=chunks,
            embeddings=embeddings,
            metadatas=[
                {
                    "source": filename,
                    "document_id": document_id,
                    "file_hash": file_hash,
                    "chunk": index
                }
                for index in range(len(chunks))
            ]
        )

        return {
            "message": "PDF uploaded and indexed successfully!",
            "filename": filename,
            "document_id": document_id,
            "total_chunks": len(chunks)
        }

    except Exception:
        saved_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()
