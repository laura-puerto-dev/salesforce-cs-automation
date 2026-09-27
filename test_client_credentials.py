import os

import requests
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    client_id = os.environ["SALESFORCE_CLIENT_ID"]
    client_secret = os.environ["SALESFORCE_CLIENT_SECRET"]
    instance_url = os.environ["SALESFORCE_INSTANCE_URL"].rstrip("/")

    response = requests.post(
        f"{instance_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    response.raise_for_status()
    credentials = response.json()

    if not credentials.get("access_token"):
        raise RuntimeError("Salesforce did not return an access token.")

    print("Client Credentials authentication successful!")
    print(f"Instance URL: {credentials.get('instance_url')}")


if __name__ == "__main__":
    main()
