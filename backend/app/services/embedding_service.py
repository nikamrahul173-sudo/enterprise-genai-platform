
from ollama import embed

def generate_embedding(text: str):
    response = embed(
        model="nomic-embed-text",
        input=text
    )
    return response.embeddings[0]


if __name__ == "__main__":
    text = "How do I reset my company password?"

    vector = generate_embedding(text)

    print("Original text:", text)
    print("Embedding dimensions:", len(vector))
    print("First 5 vector values:", vector[:5])