from salesforce_cs_automation.auth import authenticate
from salesforce_cs_automation.client import SalesforceClient


def main() -> None:
    credentials = authenticate()

    print("Successfully authenticated with Salesforce!")

    client = SalesforceClient(
        access_token=credentials["access_token"],
        instance_url=credentials["instance_url"],
    )

    cases = client.get_recent_cases(limit=10)

    print(f"\nFound {len(cases)} cases:\n")

    for case in cases:
        print(f"Case number: {case['CaseNumber']}")
        print(f"Subject: {case['Subject']}")
        print(f"Status: {case['Status']}")
        print(f"Priority: {case['Priority']}")
        print(f"Origin: {case['Origin']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
