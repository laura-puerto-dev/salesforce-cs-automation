from unittest.mock import Mock, patch

import pytest
import requests

from salesforce_cs_automation.auth import authenticate_service


def test_authenticate_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SALESFORCE_CLIENT_ID", "test-client")
    monkeypatch.setenv("SALESFORCE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv(
        "SALESFORCE_INSTANCE_URL",
        "https://example.my.salesforce.com",
    )

    response = Mock()
    response.json.return_value = {
        "access_token": "fake-access-token",
        "instance_url": "https://example.my.salesforce.com",
    }

    with patch(
        "salesforce_cs_automation.auth.requests.post",
        return_value=response,
    ) as mock_post:
        credentials = authenticate_service()

    assert credentials["access_token"] == "fake-access-token"
    assert credentials["instance_url"] == ("https://example.my.salesforce.com")

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args

    assert kwargs["data"]["grant_type"] == "client_credentials"
    assert kwargs["data"]["client_id"] == "test-client"
    assert kwargs["data"]["client_secret"] == "test-secret"
    assert kwargs["timeout"] == 30
    assert mock_post.call_args.args[0] == (
        "https://example.my.salesforce.com/services/oauth2/token"
    )


def test_authenticate_service_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SALESFORCE_CLIENT_ID", "test-client")
    monkeypatch.setenv("SALESFORCE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv(
        "SALESFORCE_INSTANCE_URL",
        "https://example.my.salesforce.com",
    )

    response = Mock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "401 Unauthorized"
    )

    with (
        patch(
            "salesforce_cs_automation.auth.requests.post",
            return_value=response,
        ),
        pytest.raises(requests.exceptions.HTTPError),
    ):
        authenticate_service()
