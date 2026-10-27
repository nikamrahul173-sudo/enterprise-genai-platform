


from ollama import chat


def generate_answer(question: str) -> str:
    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.message.content