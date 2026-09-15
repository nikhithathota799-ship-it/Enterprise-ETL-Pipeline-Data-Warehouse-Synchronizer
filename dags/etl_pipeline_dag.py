from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


def extract_salesforce():
    print("Extracting Salesforce data...")


def extract_stripe():
    print("Extracting Stripe data...")


def transform_salesforce():
    print("Transforming Salesforce data...")


def transform_stripe():
    print("Transforming Stripe data...")


def load_database():
    print("Loading data into PostgreSQL...")


def run_tests():
    print("Running ETL tests...")


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

    extract_sf >> transform_sf
    extract_st >> transform_st

    [transform_sf, transform_st] >> load_db >> tests
