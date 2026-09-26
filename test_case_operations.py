from salesforce_cs_automation.auth import authenticate
from salesforce_cs_automation.client import SalesforceClient


def main() -> None:
    credentials = authenticate()

    client = SalesforceClient(
        access_token=credentials["access_token"],
        instance_url=credentials["instance_url"],
    )

    print("Creating a test case...")

    case_id = client.create_case(
        subject="Automated test: booking confirmation issue",
        description=(
            "A fictional salon reports that customers "
            "are not receiving booking confirmations."
        ),
        priority="Medium",
        origin="Web",
    )

    print(f"Case created successfully: {case_id}")

    client.update_case(
        case_id,
        priority="High",
    )

    print("Case priority updated to High.")

    cases = client.query(
        "SELECT Id, CaseNumber, Subject, Status, Priority "
        f"FROM Case WHERE Id = '{case_id}'"
    )

    for case in cases:
        print(f"Case number: {case['CaseNumber']}")
        print(f"Subject: {case['Subject']}")
        print(f"Status: {case['Status']}")
        print(f"Priority: {case['Priority']}")


if __name__ == "__main__":
    main()
