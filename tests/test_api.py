from unittest.mock import patch

import requests
from fastapi.testclient import TestClient

from salesforce_cs_automation.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_receive_case() -> None:
    credentials = {
        "access_token": "fake-token",
        "instance_url": "https://example.my.salesforce.com",
    }

    with (
        patch(
            "salesforce_cs_automation.api.authenticate_service",
            return_value=credentials,
        ),
        patch(
            "salesforce_cs_automation.api.SalesforceClient",
        ) as mock_client_class,
    ):
        mock_client_class.return_value.create_case.return_value = "500TEST123"

        response = client.post(
            "/cases",
            json={
                "subject": "Booking confirmation not received",
                "description": "Customer did not receive confirmation.",
                "priority": "High",
                "origin": "Web",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "status": "created",
        "case_id": "500TEST123",
        "subject": "Booking confirmation not received",
        "priority": "High",
        "origin": "Web",
    }

    mock_client_class.return_value.create_case.assert_called_once_with(
        subject="Booking confirmation not received",
        description="Customer did not receive confirmation.",
        priority="High",
        origin="Web",
    )


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


def test_receive_case_handles_authentication_error() -> None:
    with patch(
        "salesforce_cs_automation.api.authenticate_service",
        side_effect=requests.exceptions.HTTPError("401 Unauthorized"),
    ):
        response = client.post(
            "/cases",
            json={
                "subject": "Booking issue",
                "description": "Customer reports an issue.",
            },
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Salesforce integration failed."}


def test_receive_case_handles_creation_error() -> None:
    credentials = {
        "access_token": "fake-token",
        "instance_url": "https://example.my.salesforce.com",
    }

    with (
        patch(
            "salesforce_cs_automation.api.authenticate_service",
            return_value=credentials,
        ),
        patch(
            "salesforce_cs_automation.api.SalesforceClient",
        ) as mock_client_class,
    ):
        mock_client = mock_client_class.return_value

        mock_client.create_case.side_effect = requests.exceptions.HTTPError(
            "Salesforce error"
        )

        response = client.post(
            "/cases",
            json={
                "subject": "Booking issue",
                "description": "Customer reports an issue.",
            },
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Salesforce integration failed."}
    mock_client.create_case.assert_called_once()


def test_receive_case_handles_missing_token() -> None:
    with patch(
        "salesforce_cs_automation.api.authenticate_service",
        side_effect=RuntimeError("Salesforce did not return an access token."),
    ):
        response = client.post(
            "/cases",
            json={
                "subject": "Booking issue",
                "description": "Customer reports an issue.",
            },
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Salesforce integration failed."}
