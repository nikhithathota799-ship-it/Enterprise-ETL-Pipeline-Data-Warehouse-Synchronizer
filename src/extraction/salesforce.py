import os
import requests
from dotenv import load_dotenv

load_dotenv()


class SalesforceExtractor:
    """
    Extracts Account data from Salesforce REST API.
    """

    def __init__(self):
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.access_token = os.getenv("SALESFORCE_ACCESS_TOKEN")
        self.instance_url = os.getenv("SALESFORCE_INSTANCE_URL")

    def extract_accounts(self):
        """
        Fetch Account records from Salesforce.
        """

        if not self.access_token or not self.instance_url:
            raise ValueError(
                "SALESFORCE_ACCESS_TOKEN and SALESFORCE_INSTANCE_URL "
                "must be configured in .env"
            )

        url = f"{self.instance_url}/services/data/v61.0/query"

        query = """
        SELECT Id, Name, Industry, Phone, Website
        FROM Account
        LIMIT 100
        """

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            params={"q": query},
            timeout=30,
        )

        response.raise_for_status()

        return response.json()


if __name__ == "__main__":
    extractor = SalesforceExtractor()
    accounts = extractor.extract_accounts()

    print("Salesforce extraction successful!")
    print(accounts)