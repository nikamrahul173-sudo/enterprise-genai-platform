
from ollama import chat

from backend.app.services.vector_store import search_documents_with_sources


def generate_rag_answer(question: str) -> dict:
    # Step 1: Retrieve relevant company policies
    sources = search_documents_with_sources(question)

    # Step 2: Handle questions with no relevant policies
    if not sources:
        return {
            "answer": (
                "I couldn't find this information "
                "in the available company policies."
            ),
            "sources": []
        }

    # Step 3: Combine retrieved documents
    context = "\n\n".join(
        source["content"] for source in sources
    )

    # Step 4: Send context + question to Ollama
    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful company IT support assistant. "
                    "Answer using only the provided company policies. "
                    "Use rules relevant to the question. "
                    "Do not invent information or mix unrelated policies. "
                    "If the answer is not in the policies, "
                    "say 'I don't have enough information.' "
                    "Keep your answer short and clear."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Company Policies:\n{context}\n\n"
                    f"Employee Question:\n{question}\n\n"
                    "Answer the question based on the company policies."
                )
            }
        ],
        options={"temperature": 0}
    )

    # Step 5: Return answer with sources
    return {
        "answer": response.message.content,
        "sources": sources
    }
