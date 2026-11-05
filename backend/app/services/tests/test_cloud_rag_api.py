
from fastapi.testclient import TestClient

from backend.app import cloud_main


def test_rag_chat_returns_grounded_answer_and_sources(
    monkeypatch,
):
    sample_sources = [
        {
            "document_id": 1,
            "filename": "vpn_troubleshooting.md@test",
            "page": 1,
            "content": (
                "Check the VPN client and MFA prompts. "
                "Never share MFA codes."
            ),
        }
    ]

    monkeypatch.setattr(
        cloud_main,
        "search_documents",
        lambda question: sample_sources,
    )

    captured = {}

    def fake_groq(messages, json_mode=False):
        captured["messages"] = messages
        return "Check the VPN client and MFA prompts."

    monkeypatch.setattr(
        cloud_main,
        "generate_cloud_response",
        fake_groq,
    )

    client = TestClient(cloud_main.app)

    response = client.post(
        "/rag/chat",
        json={"question": "How do I troubleshoot VPN MFA?"},
    )

    assert response.status_code == 200

    body = response.json()

    assert "VPN client" in body["answer"]
    assert len(body["sources"]) == 1
    assert body["sources"][0]["filename"] == (
        "vpn_troubleshooting.md@test"
    )
    assert body["sources"][0]["page"] == 1

    assert "Never share MFA codes" in (
        captured["messages"][1]["content"]
    )


def test_rag_chat_without_sources_skips_groq(monkeypatch):
    monkeypatch.setattr(
        cloud_main,
        "search_documents",
        lambda question: [],
    )

    def should_not_call_groq(*args, **kwargs):
        raise AssertionError("Groq must not be called")

    monkeypatch.setattr(
        cloud_main,
        "generate_cloud_response",
        should_not_call_groq,
    )

    client = TestClient(cloud_main.app)

    response = client.post(
        "/rag/chat",
        json={"question": "Unknown internal procedure"},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert "couldn't find" in response.json()["answer"]




def test_public_demo_blocks_pdf_upload(monkeypatch):
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "1")
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)

    client = TestClient(cloud_main.app)

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.pdf",
                b"%PDF-1.4\n",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Admin authorization required."
    )



def test_cloud_knowledge_seeds_on_api_startup(
    tmp_path,
    monkeypatch,
):
    from backend.app.services import cloud_rag_service

    monkeypatch.setattr(
        cloud_rag_service,
        "DB_PATH",
        tmp_path / "startup_test.db",
    )

    # Context manager triggers FastAPI startup events.
    with TestClient(cloud_main.app) as client:
        response = client.get("/documents")

        assert response.status_code == 200

        documents = response.json()

        # Support an API response containing a list
        # or a dictionary with a "documents" field.
        if isinstance(documents, dict):
            documents = documents["documents"]

        assert any(
            item["filename"].startswith(
                "vpn_troubleshooting.md@"
            )
            for item in documents
        )


def test_dashboard_returns_review_counts(monkeypatch):
    monkeypatch.setattr(
        cloud_main,
        "list_cloud_tickets",
        lambda: [
            {"status": "Open"},
            {"status": "Resolved"},
        ],
    )

    monkeypatch.setattr(
        cloud_main,
        "get_review_stats",
        lambda: {
            "pending_reviews": 1,
            "approved_reviews": 1,
            "rejected_reviews": 0,
        },
    )

    client = TestClient(cloud_main.app)
    response = client.get("/dashboard/stats")

    assert response.status_code == 200

    stats = response.json()

    assert stats["total_tickets"] == 2
    assert stats["open_tickets"] == 1
    assert stats["resolved_tickets"] == 1
    assert stats["pending_reviews"] == 1
    assert stats["approved_reviews"] == 1
    assert stats["rejected_reviews"] == 0



def test_dashboard_with_zero_tickets(monkeypatch):
    monkeypatch.setattr(
        cloud_main,
        "list_cloud_tickets",
        lambda: [],
    )

    monkeypatch.setattr(
        cloud_main,
        "get_review_stats",
        lambda: {
            "pending_reviews": 0,
            "approved_reviews": 0,
            "rejected_reviews": 0,
        },
    )

    client = TestClient(cloud_main.app)
    response = client.get("/dashboard/stats")

    assert response.status_code == 200

    stats = response.json()

    assert stats["total_tickets"] == 0
    assert stats["open_tickets"] == 0
    assert stats["pending_reviews"] == 0
    assert stats["approved_reviews"] == 0
    assert stats["rejected_reviews"] == 0