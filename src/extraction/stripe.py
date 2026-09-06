import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models.external_models import (
    StripeCustomer,
    StripeCharge,
    StripeInvoice,
)


# ============================================================
# LOAD .ENV
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# RAW DATA FOLDER
# ============================================================

RAW_FOLDER = PROJECT_ROOT / "data" / "raw" / "stripe"
RAW_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# STRIPE EXTRACTOR
# ============================================================

class StripeExtractor:
    """
    Extracts Stripe data using API Key authentication.
    Handles retries, cursor-based pagination, validates records
    with Pydantic models, and saves raw JSON data.
    """

    BASE_URL = "https://api.stripe.com/v1"

    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "STRIPE_API_KEY is missing in .env"
            )

    # ========================================================
    # STRIPE REQUEST
    # ========================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def execute_request(self, endpoint, params=None):
        """Execute a Stripe REST API GET request."""

        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.get(
            url,
            auth=(self.api_key, ""),
            params=params or {},
            timeout=30,
        )

        if not response.ok:
            print("\n========== STRIPE API ERROR ==========")
            print("HTTP Status:", response.status_code)
            print("Response:", response.text)
            print("=======================================\n")

        response.raise_for_status()

        return response.json()

    # ========================================================
    # PAGINATED EXTRACTION
    # ========================================================

    def fetch_all_records(self, endpoint, extra_params=None):
        """
        Fetch all Stripe records for a given endpoint.
        Automatically follows cursor-based pagination
        using 'has_more' and 'starting_after'.
        """

        all_records = []
        page_number = 1
        starting_after = None

        while True:

            print(f"\nFetching Stripe page {page_number} for '{endpoint}'...")

            params = {"limit": 100}

            if extra_params:
                params.update(extra_params)

            if starting_after:
                params["starting_after"] = starting_after

            data = self.execute_request(endpoint, params)

            records = data.get("data", [])

            print(f"Records received on page {page_number}: {len(records)}")

            all_records.extend(records)

            print(f"Total records collected: {len(all_records)}")

            if data.get("has_more") and records:
                starting_after = records[-1]["id"]
                page_number += 1
            else:
                print("No more pages available.")
                break

        return all_records

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_records(self, records, model, label):
        """
        Validate raw records against a Pydantic model.
        Invalid records are logged and skipped, not silently dropped.
        """

        valid_records = []

        for record in records:
            try:
                validated = model.model_validate(record)
                valid_records.append(validated.model_dump(mode="json"))
            except Exception as error:
                print(
                    f"Skipping invalid {label} record "
                    f"(id={record.get('id', 'unknown')}): {error}"
                )

        print(f"Validated {len(valid_records)}/{len(records)} {label} records")

        return valid_records

    # ========================================================
    # CUSTOMERS
    # ========================================================

    def extract_customers(self):
        """Extract and validate Customer records."""

        raw_records = self.fetch_all_records("customers")
        return self.validate_records(raw_records, StripeCustomer, "customer")

    # ========================================================
    # CHARGES
    # ========================================================

    def extract_charges(self):
        """Extract and validate Charge records."""

        raw_records = self.fetch_all_records("charges")
        return self.validate_records(raw_records, StripeCharge, "charge")

    # ========================================================
    # INVOICES
    # ========================================================

    def extract_invoices(self):
        """Extract and validate Invoice records."""

        raw_records = self.fetch_all_records("invoices")
        return self.validate_records(raw_records, StripeInvoice, "invoice")


# ============================================================
# SAVE JSON
# ============================================================

def save_json(filename, records):
    """
    Save extracted records as JSON in raw Stripe folder.
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

    print(f"Saved {len(records)} records to:\n{file_path}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n==========================================")
    print("STARTING STRIPE EXTRACTION")
    print("==========================================")

    try:

        extractor = StripeExtractor()

        print("Authenticating with Stripe...")

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        customers = extractor.extract_customers()

        print(f"\nCustomers extracted: {len(customers)}")

        save_json("customers.json", customers)

        # ----------------------------------------------------
        # CHARGES
        # ----------------------------------------------------

        charges = extractor.extract_charges()

        print(f"\nCharges extracted: {len(charges)}")

        save_json("charges.json", charges)

        # ----------------------------------------------------
        # INVOICES
        # ----------------------------------------------------

        invoices = extractor.extract_invoices()

        print(f"\nInvoices extracted: {len(invoices)}")

        save_json("invoices.json", invoices)

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print("\n==========================================")
        print("STRIPE EXTRACTION COMPLETED")
        print("==========================================")

        print(f"Customers: {len(customers)}")
        print(f"Charges: {len(charges)}")
        print(f"Invoices: {len(invoices)}")

        print("==========================================")

        print("\nRaw files saved successfully!")
        print(f"Location: {RAW_FOLDER}")

    except Exception as error:

        print("\n==========================================")
        print("STRIPE EXTRACTION FAILED")
        print("==========================================")

        print(f"Error: {error}")

        print("==========================================")

        raise
