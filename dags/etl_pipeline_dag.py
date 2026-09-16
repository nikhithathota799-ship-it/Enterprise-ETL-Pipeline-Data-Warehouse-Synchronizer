import sys
import subprocess
from datetime import datetime
from pathlib import Path

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ----------------------------------------------------
# SALESFORCE EXTRACTION
# ----------------------------------------------------

def extract_salesforce():
    from src.extraction.salesforce import SalesforceExtractor, save_json

    extractor = SalesforceExtractor()

    accounts = extractor.extract_accounts()
    save_json("accounts.json", accounts)

    contacts = extractor.extract_contacts()
    save_json("contacts.json", contacts)

    opportunities = extractor.extract_opportunities()
    save_json("opportunities.json", opportunities)

    print(f"Salesforce Accounts: {len(accounts)}")
    print(f"Salesforce Contacts: {len(contacts)}")
    print(f"Salesforce Opportunities: {len(opportunities)}")


# ----------------------------------------------------
# STRIPE EXTRACTION
# ----------------------------------------------------

def extract_stripe():
    from src.extraction.stripe import StripeExtractor, save_json

    extractor = StripeExtractor()

    customers = extractor.extract_customers()
    save_json("customers.json", customers)

    charges = extractor.extract_charges()
    save_json("charges.json", charges)

    invoices = extractor.extract_invoices()
    save_json("invoices.json", invoices)

    print(f"Stripe Customers: {len(customers)}")
    print(f"Stripe Charges: {len(charges)}")
    print(f"Stripe Invoices: {len(invoices)}")


# ----------------------------------------------------
# SALESFORCE TRANSFORMATION
# ----------------------------------------------------

def transform_salesforce():
    from src.transformation.salesforce_transform import (
        transform_accounts,
        transform_contacts,
        transform_opportunities,
    )

    transform_accounts()
    transform_contacts()
    transform_opportunities()

    print("Salesforce transformation completed.")


# ----------------------------------------------------
# STRIPE TRANSFORMATION
# ----------------------------------------------------

def transform_stripe():
    from src.transformation.stripe_transform import (
        transform_customers,
        transform_charges,
        transform_invoices,
    )

    transform_customers()
    transform_charges()
    transform_invoices()

    print("Stripe transformation completed.")


# ----------------------------------------------------
# DATABASE LOADING
# ----------------------------------------------------

def load_database():
    from src.loading.loader import run_loader

    run_loader()

    print("Database loading completed.")


# ----------------------------------------------------
# TESTING
# ----------------------------------------------------

def run_tests():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=PROJECT_ROOT,
        check=True,
    )

    print("All ETL tests completed successfully.")


# ----------------------------------------------------
# AIRFLOW DAG
# ----------------------------------------------------

with DAG(
    dag_id="enterprise_etl_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["ETL", "Salesforce", "Stripe", "PostgreSQL"],
) as dag:

    extract_sf = PythonOperator(
        task_id="extract_salesforce",
        python_callable=extract_salesforce,
    )

    extract_st = PythonOperator(
        task_id="extract_stripe",
        python_callable=extract_stripe,
    )

    transform_sf = PythonOperator(
        task_id="transform_salesforce",
        python_callable=transform_salesforce,
    )

    transform_st = PythonOperator(
        task_id="transform_stripe",
        python_callable=transform_stripe,
    )

    load_db = PythonOperator(
        task_id="load_database",
        python_callable=load_database,
    )

    tests = PythonOperator(
        task_id="run_tests",
        python_callable=run_tests,
    )

    # Dependencies
    extract_sf >> transform_sf
    extract_st >> transform_st

    [transform_sf, transform_st] >> load_db >> tests
