
from pathlib import Path
import re

from backend.app.services.pdf_service import extract_text_from_pdf
from backend.app.services.vector_store import (
    collection,
    get_embedding,
)


# Project root and PDF location
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PDF_PATH = PROJECT_ROOT / "data" / "sample_policy.pdf"

# IDs used by the previous 500-character PDF loader
OLD_PDF_ID_PREFIX = "pdf_sample_"

# IDs used by the new smart PDF loader
NEW_PDF_ID_PREFIX = "pdf_policy_"


def split_text_into_chunks(text: str):
    """
    Split the sample PDF into numbered policy sections.

    Example headings:
    1. Software Installation Policy
    2. Password Reset Policy
    """

    # Match numbered headings at the beginning of a line
    heading_pattern = re.compile(
        r"(?m)^\s*(\d+)\.\s+([^\n]+)"
    )

    matches = list(heading_pattern.finditer(text))

    if not matches:
        raise ValueError(
            "No numbered policy headings found in the PDF. "
            "Please check the PDF format."
        )

    chunks = []

    for index, match in enumerate(matches):
        start = match.start()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        chunk = text[start:end].strip()

        # Remove the optional end-of-document footer
        chunk = re.split(
            r"(?m)^End of Document\s*$",
            chunk
        )[0].strip()

        if chunk:
            chunks.append(chunk)

    return chunks


def load_pdf_into_chromadb():
    # Step 1: Extract PDF text
    text = extract_text_from_pdf(str(PDF_PATH))

    if not text.strip():
        print("No readable text found in PDF.")
        return

    # Step 2: Split by policy headings
    chunks = split_text_into_chunks(text)

    print(f"\nTotal policy chunks: {len(chunks)}")

    # Step 3: Generate embeddings
    embeddings = [
        get_embedding(chunk) for chunk in chunks
    ]

    # Step 4: Remove previously indexed PDF chunks
    # Only IDs belonging to this sample PDF are affected
    existing_ids = collection.get()["ids"]

    old_pdf_ids = [
        document_id
        for document_id in existing_ids
        if document_id.startswith(OLD_PDF_ID_PREFIX)
        or document_id.startswith(NEW_PDF_ID_PREFIX)
    ]

    if old_pdf_ids:
        collection.delete(ids=old_pdf_ids)
        print(f"Removed {len(old_pdf_ids)} old PDF chunks.")

    # Step 5: Store new policy-based chunks
    collection.upsert(
        ids=[
            f"{NEW_PDF_ID_PREFIX}{index}"
            for index in range(len(chunks))
        ],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {
                "source": PDF_PATH.name,
                "chunk": index
            }
            for index in range(len(chunks))
        ]
    )

    print("Smart PDF chunks stored successfully!")

    # Show stored policy headings
    for index, chunk in enumerate(chunks):
        heading = chunk.splitlines()[0]
        print(f"Chunk {index + 1}: {heading}")


if __name__ == "__main__":
    load_pdf_into_chromadb()
