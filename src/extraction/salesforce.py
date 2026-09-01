import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential


# ============================================================
# LOAD .ENV
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# RAW DATA FOLDER
# ============================================================

RAW_FOLDER = PROJECT_ROOT / "data" / "raw" / "salesforce"
RAW_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# SALESFORCE EXTRACTOR
# ============================================================

class SalesforceExtractor:
    """
    Extracts Salesforce data using OAuth Client Credentials Flow.
    Handles retries, pagination and saves raw JSON data.
    """

    def __init__(self):
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.instance_url = os.getenv("SALESFORCE_INSTANCE_URL")

        if self.instance_url:
            self.instance_url = self.instance_url.rstrip("/")

            if not self.instance_url.startswith("http"):
                self.instance_url = "https://" + self.instance_url

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_access_token(self):
        """Get Salesforce access token."""

        if not self.client_id:
            raise ValueError(
                "SALESFORCE_CLIENT_ID is missing in .env"
            )

        if not self.client_secret:
            raise ValueError(
                "SALESFORCE_CLIENT_SECRET is missing in .env"
            )

        if not self.instance_url:
            raise ValueError(
                "SALESFORCE_INSTANCE_URL is missing in .env"
            )

        token_url = (
            f"{self.instance_url}/services/oauth2/token"
        )

        response = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )

        if not response.ok:
            print("\n========== SALESFORCE OAUTH ERROR ==========")
            print("HTTP Status:", response.status_code)
            print("Response:", response.text)
            print("============================================\n")

        response.raise_for_status()

        token_data = response.json()

        return token_data["access_token"]

    # ========================================================
    # SALESFORCE QUERY
    # ========================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def execute_query(self, url, access_token, query=None):
        """Execute Salesforce REST API query."""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        params = {}

        if query:
            params["q"] = query

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # PAGINATED EXTRACTION
    # ========================================================

    def fetch_all_records(self, query):
        """
        Fetch all Salesforce records.
        Automatically follows nextRecordsUrl pagination.
        """

        access_token = self.get_access_token()

        url = (
            f"{self.instance_url}"
            f"/services/data/v61.0/query"
        )

        all_records = []
        page_number = 1

        while url:

            print(
                f"\nFetching Salesforce page "
                f"{page_number}..."
            )

            if page_number == 1:
                data = self.execute_query(
                    url,
                    access_token,
                    query
                )
            else:
                data = self.execute_query(
                    f"{self.instance_url}{url}",
                    access_token
                )

            records = data.get("records", [])

            print(
                f"Records received on page "
                f"{page_number}: {len(records)}"
            )

            all_records.extend(records)

            print(
                f"Total records collected: "
                f"{len(all_records)}"
            )

            next_url = data.get("nextRecordsUrl")

            if next_url:
                url = next_url
                page_number += 1
            else:
                url = None
                print("No more pages available.")

        return all_records

    # ========================================================
    # ACCOUNTS
    # ========================================================

    def extract_accounts(self):
        """Extract Account records."""

        query = """
        SELECT Id, Name, Industry, Phone, Website
        FROM Account
        LIMIT 100
        """

        return self.fetch_all_records(query)

    # ========================================================
    # CONTACTS
    # ========================================================

    def extract_contacts(self):
        """Extract Contact records."""

        query = """
        SELECT Id, FirstName, LastName, Email, Phone, AccountId
        FROM Contact
        LIMIT 100
        """

        return self.fetch_all_records(query)

    # ========================================================
    # OPPORTUNITIES
    # ========================================================

    def extract_opportunities(self):
        """Extract Opportunity records."""

        query = """
        SELECT Id, Name, Amount, StageName, CloseDate, AccountId
        FROM Opportunity
        LIMIT 100
        """

        return self.fetch_all_records(query)


# ============================================================
# SAVE JSON
# ============================================================

def save_json(filename, records):
    """
    Save extracted records as JSON in raw Salesforce folder.
    """

    file_path = RAW_FOLDER / filename

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Saved {len(records)} records to:"
        f"\n{file_path}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n==========================================")
    print("STARTING SALESFORCE EXTRACTION")
    print("==========================================")

    try:

        extractor = SalesforceExtractor()

        print(
            f"Instance URL: "
            f"{extractor.instance_url}"
        )

        print(
            "Authenticating with Salesforce..."
        )

        # Test authentication first
        extractor.get_access_token()

        print(
            "Salesforce authentication successful!"
        )

        # ----------------------------------------------------
        # ACCOUNTS
        # ----------------------------------------------------

        accounts = extractor.extract_accounts()

        print(
            f"\nAccounts extracted: "
            f"{len(accounts)}"
        )

        save_json(
            "accounts.json",
            accounts
        )

        # ----------------------------------------------------
        # CONTACTS
        # ----------------------------------------------------

        contacts = extractor.extract_contacts()

        print(
            f"\nContacts extracted: "
            f"{len(contacts)}"
        )

        save_json(
            "contacts.json",
            contacts
        )

        # ----------------------------------------------------
        # OPPORTUNITIES
        # ----------------------------------------------------

        opportunities = (
            extractor.extract_opportunities()
        )

        print(
            f"\nOpportunities extracted: "
            f"{len(opportunities)}"
        )

        save_json(
            "opportunities.json",
            opportunities
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print("\n==========================================")
        print("SALESFORCE EXTRACTION COMPLETED")
        print("==========================================")

        print(
            f"Accounts: {len(accounts)}"
        )

        print(
            f"Contacts: {len(contacts)}"
        )

        print(
            f"Opportunities: {len(opportunities)}"
        )

        print("==========================================")

        print(
            "\nRaw files saved successfully!"
        )

        print(
            f"Location: {RAW_FOLDER}"
        )

    except Exception as error:

        print("\n==========================================")
        print("SALESFORCE EXTRACTION FAILED")
        print("==========================================")

        print(
            f"Error: {error}"
        )

        print("==========================================")

        raise