import requests


class SalesforceClient:
    """Minimal client for Salesforce REST API."""

    API_VERSION = "v60.0"

    def __init__(self, access_token: str, instance_url: str):
        self.instance_url = instance_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def query(self, soql: str) -> list[dict]:
        """Execute a SOQL query and retrieve all result pages."""

        url: str | None = f"{self.instance_url}/services/data/{self.API_VERSION}/query"

        params: dict[str, str] | None = {"q": soql}
        records: list[dict] = []

        while url is not None:
            response = self.session.get(
                url,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            records.extend(data["records"])

            next_url = data.get("nextRecordsUrl")

            url = f"{self.instance_url}{next_url}" if next_url else None

            params = None

        return records

    def get_recent_cases(self, limit: int = 10) -> list[dict]:
        """Retrieve the most recently created support cases."""
        if not 1 <= limit <= 200:
            raise ValueError("Limit must be between 1 and 200.")

        soql = f"""
            SELECT
                Id,
                CaseNumber,
                Subject,
                Status,
                Priority,
                Origin
            FROM Case
            ORDER BY CreatedDate DESC
            LIMIT {limit}
        """

        return self.query(soql)
