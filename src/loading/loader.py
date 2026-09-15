"""
Loader (Member 4).

Reads processed JSON files (output of Member 3's transformation step)
and loads them into PostgreSQL, table by table, using upsert so the
loader can be re-run safely without creating duplicates.
"""

import json
from datetime import datetime
from pathlib import Path

from src.loading.database import get_session, create_all_tables, test_connection
from src.loading.upsert import upsert_records
from src.models.database_models import (
    Account,
    Contact,
    Opportunity,
    StripeCustomer,
    StripeCharge,
    StripeInvoice,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FOLDER = PROJECT_ROOT / "data" / "processed"


# ============================================================
# HELPERS
# ============================================================

def read_json_file(path):
    """Read a processed JSON file. Returns an empty list if it doesn't exist."""

    if not path.exists():
        print(f"File not found, skipping: {path}")
        return []

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, list) else []


def parse_processed_at(records):
    """
    Convert the '_processed_at' ISO string on each record into a real
    datetime object, since the DB column is DateTime(timezone=True).
    """

    for record in records:
        raw = record.get("_processed_at")

        if raw:
            try:
                record["_processed_at"] = datetime.fromisoformat(raw)
            except ValueError:
                record["_processed_at"] = None

    return records


# ============================================================
# LOAD FUNCTIONS (one per table)
# ============================================================

def load_accounts(session):
    records = read_json_file(PROCESSED_FOLDER / "salesforce" / "accounts.json")
    records = parse_processed_at(records)
    return upsert_records(session, Account, records)


def load_contacts(session):
    records = read_json_file(PROCESSED_FOLDER / "salesforce" / "contacts.json")
    records = parse_processed_at(records)
    return upsert_records(session, Contact, records)


def load_opportunities(session):
    records = read_json_file(PROCESSED_FOLDER / "salesforce" / "opportunities.json")
    records = parse_processed_at(records)
    return upsert_records(session, Opportunity, records)


def load_stripe_customers(session):
    records = read_json_file(PROCESSED_FOLDER / "stripe" / "customers.json")
    records = parse_processed_at(records)
    return upsert_records(session, StripeCustomer, records)


def load_stripe_charges(session):
    records = read_json_file(PROCESSED_FOLDER / "stripe" / "charges.json")
    records = parse_processed_at(records)
    return upsert_records(session, StripeCharge, records)


def load_stripe_invoices(session):
    records = read_json_file(PROCESSED_FOLDER / "stripe" / "invoices.json")
    records = parse_processed_at(records)
    return upsert_records(session, StripeInvoice, records)


# ============================================================
# VERIFY
# ============================================================

def verify_loaded_counts(session):
    """Print how many rows ended up in each table, as a sanity check."""

    print("\n========== VERIFICATION ==========")

    for model in [Account, Contact, Opportunity, StripeCustomer, StripeCharge, StripeInvoice]:
        count = session.query(model).count()
        print(f"{model.__tablename__}: {count} rows")

    print("===================================")


# ============================================================
# MAIN
# ============================================================

def run_loader():
    print("\n==========================================")
    print("STARTING DATABASE LOAD")
    print("==========================================")

    if not test_connection():
        print("Aborting: could not connect to the database.")
        return

    create_all_tables()

    session = get_session()

    try:
        # Load Salesforce tables first (accounts before contacts/opportunities,
        # since those have a foreign key pointing at accounts.id)
        load_accounts(session)
        load_contacts(session)
        load_opportunities(session)

        # Then Stripe tables (independent of Salesforce)
        load_stripe_customers(session)
        load_stripe_charges(session)
        load_stripe_invoices(session)

        verify_loaded_counts(session)

        print("\nDatabase load completed successfully.")

    except Exception as error:
        print(f"\nDatabase load FAILED: {error}")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    run_loader()
