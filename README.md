# Enterprise ETL Pipeline

An automated data engineering pipeline that extracts business data from third-party APIs, transforms and validates the data, and loads it into a centralized data warehouse.

## Data Sources

- Salesforce
- Stripe

## Technologies

- Python
- Pandas
- Polars
- Pydantic
- Requests
- Tenacity
- AWS S3
- PostgreSQL
- SQLAlchemy
- Apache Airflow
- Docker
- Pytest

## Pipeline

Salesforce + Stripe
        ↓
Python Extraction
        ↓
AWS S3
        ↓
Data Transformation
        ↓
Data Validation
        ↓
PostgreSQL
        ↓
Apache Airflow