
import os

# Must be set before importing the FastAPI application.
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_public_demo_blocks_ticket_creation():
    response = client.post(
        "/tickets",
        json={
            "title": "Automated Security Test",
            "description": "This must not create a ticket",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "This action is disabled in public demo mode."
    )
