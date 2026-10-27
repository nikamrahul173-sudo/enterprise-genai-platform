
from pathlib import Path

from backend.app.services.vector_store import collection, get_embedding


# Find project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Location of company policies file
FILE_PATH = PROJECT_ROOT / "data" / "company_policies.txt"


def load_company_documents():
    # Read the text file
    text = FILE_PATH.read_text(encoding="utf-8")

    # Separate policies using blank lines
    chunks = [
        chunk.strip()
        for chunk in text.split("\n\n")
        if chunk.strip()
    ]

    # Convert each chunk into an embedding
    embeddings = [
        get_embedding(chunk)
        for chunk in chunks
    ]

    # Save chunks in ChromaDB
    collection.upsert(
        ids=[f"policy_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"source": "company_policies.txt"}
            for _ in chunks
        ]
    )

    print(f"Successfully stored {len(chunks)} document chunks!")


if __name__ == "__main__":
    load_company_documents()