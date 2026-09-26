from unittest.mock import Mock, patch

import pytest

from salesforce_cs_automation.client import SalesforceClient


@pytest.fixture
def client() -> SalesforceClient:
    return SalesforceClient(
        access_token="fake-test-token",
        instance_url="https://example.my.salesforce.com",
    )


def test_create_case(client: SalesforceClient) -> None:
    response = Mock()
    response.json.return_value = {"id": "500TEST123"}

    with patch.object(
        client.session,
        "post",
        return_value=response,
    ) as mock_post:
        case_id = client.create_case(
            subject="Test booking issue",
            description="A fictional customer reports an issue.",
        )

    assert case_id == "500TEST123"

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args

    assert kwargs["json"]["Subject"] == "Test booking issue"
    assert kwargs["json"]["Status"] == "New"
    assert kwargs["json"]["Priority"] == "Medium"


def test_update_case(client: SalesforceClient) -> None:
    response = Mock()

    with patch.object(
        client.session,
        "patch",
        return_value=response,
    ) as mock_patch:
        client.update_case(
            "500TEST123",
            priority="High",
        )

    mock_patch.assert_called_once()
    _, kwargs = mock_patch.call_args

    assert kwargs["json"] == {"Priority": "High"}


def test_update_case_requires_fields(
    client: SalesforceClient,
) -> None:
    with pytest.raises(ValueError):
        client.update_case("500TEST123")
