
from pathlib import Path

import chromadb
from ollama import embed


# ==========================================
# 1. Project root and database location
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "chroma_db"

# Persistent database: data remains after restart
client = chromadb.PersistentClient(path=str(DB_PATH))

collection = client.get_or_create_collection(
    name="company_knowledge"
)


# ==========================================
# 2. Generate embeddings using Ollama
# ==========================================

def get_embedding(text: str):
    response = embed(
        model="nomic-embed-text",
        input=text
    )

    return response.embeddings[0]


# ==========================================
# 3. Add sample documents (optional)
# ==========================================

def add_documents():
    documents = [
        "Employees can reset their password using the IT helpdesk portal.",
        "To request a new laptop, submit a ticket to the IT support team.",
        "Employees can apply for leave through the HR management system."
    ]

    ids = ["doc1", "doc2", "doc3"]

    embeddings = [
        get_embedding(doc) for doc in documents
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings
    )

    print("Company documents stored successfully!")


# ==========================================
# 4. Basic document search
# ==========================================

def search_documents(question: str):
    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=1
    )

    return results["documents"][0]


# ==========================================
# 5. Document search with sources + distances
# ==========================================


def search_documents_with_sources(question: str):
    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    sources = []

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        # Filter out less relevant documents
        if distance > 0.6:
            continue

        sources.append({
            "file": (metadata or {}).get("source", "unknown"),
            "content": document,
            "distance": round(distance, 4)
        })

    return sources


# ==========================================
# 6. Test basic search
# ==========================================

if __name__ == "__main__":
    add_documents()

    question = "I forgot my login password. What should I do?"

    matches = search_documents(question)

    print("\nQuestion:", question)
    print("Relevant document:", matches[0])
