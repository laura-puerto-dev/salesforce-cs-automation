from fastapi.testclient import TestClient

from salesforce_cs_automation.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_receive_case() -> None:
    response = client.post(
        "/cases",
        json={
            "subject": "Booking confirmation not received",
            "description": "Customer did not receive confirmation.",
            "priority": "High",
            "origin": "Web",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "received",
        "subject": "Booking confirmation not received",
        "priority": "High",
        "origin": "Web",
    }


def test_receive_case_requires_subject() -> None:
    response = client.post(
        "/cases",
        json={
            "description": "Customer did not receive confirmation.",
        },
    )

    assert response.status_code == 422


def test_receive_case_rejects_invalid_priority() -> None:
    response = client.post(
        "/cases",
        json={
            "subject": "Booking issue",
            "description": "Customer reports an issue.",
            "priority": "Urgent",
        },
    )

    assert response.status_code == 422
