from src.salesforce_cs_automation.auth import authenticate


def main():
    credentials = authenticate()

    print("Successfully authenticated with Salesforce!")
    print(f"Instance URL: {credentials['instance_url']}")
    print("Access token received successfully.")


if __name__ == "__main__":
    main()
