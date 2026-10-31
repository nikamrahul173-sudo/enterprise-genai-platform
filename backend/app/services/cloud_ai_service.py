import json
import os

import httpx


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


def generate_cloud_response(messages, json_mode=False):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_completion_tokens": 1200,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )

        if response.status_code == 400 and json_mode:
            try:
                error_code = response.json().get("error", {}).get("code")
            except ValueError:
                error_code = None

            if error_code == "json_validate_failed":
                print("Groq JSON validation failed. Retrying once.", flush=True)

                retry_payload = payload.copy()
                retry_payload.pop("response_format", None)
                retry_payload["messages"] = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Return exactly one valid JSON object. "
                            "No markdown, no code fences, no explanation."
                        ),
                    }
                ]

                response = client.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=retry_payload,
                )

        response.raise_for_status()
        result = response.json()

    answer = result["choices"][0]["message"]["content"]

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("AI returned an empty response.")

    if json_mode:
        json.loads(answer)

    return answer
