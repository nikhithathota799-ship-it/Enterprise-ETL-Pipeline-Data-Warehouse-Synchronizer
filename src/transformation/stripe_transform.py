import json
from pathlib import Path
from datetime import datetime, timezone

from src.models.external_models import (
    StripeCustomer,
    StripeCharge,
    StripeInvoice,
)


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FOLDER = PROJECT_ROOT / "data" / "raw" / "stripe"

PROCESSED_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "stripe"
)

PROCESSED_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(filename):
    """Load JSON data from the Stripe raw-data folder."""

    file_path = RAW_FOLDER / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# GET RECORDS
# ============================================================

def get_records(data):
    """
    Get records from Stripe JSON.

    Supports:
    1. Stripe list response: {"data": [...]}
    2. Direct list: [...]
    """

    if isinstance(data, dict):

        records = data.get("data", [])

        if not isinstance(records, list):
            raise ValueError(
                "'data' must be a list"
            )

        return records

    if isinstance(data, list):
        return data

    raise ValueError(
        "Invalid JSON format."
    )


# ============================================================
# CLEAN VALUES
# ============================================================

def clean_value(value):
    """
    Clean string values.

    Empty strings are converted to None.
    """

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()

        if value == "":
            return None

    return value


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(records):
    """
    Remove duplicate Stripe records using their id.
    """

    unique_records = []
    seen_ids = set()
    duplicate_count = 0

    for record in records:

        if not isinstance(record, dict):
            continue

        record_id = record.get("id")

        # Keep records without ID for validation
        if not record_id:
            unique_records.append(record)
            continue

        if record_id in seen_ids:
            duplicate_count += 1
            continue

        seen_ids.add(record_id)

        unique_records.append(record)

    print(
        f"Duplicate records removed: "
        f"{duplicate_count}"
    )

    return unique_records


# ============================================================
# VALIDATE CUSTOMER
# ============================================================

def validate_customer(record):
    """Validate a Stripe Customer."""

    customer_data = {
        "id": clean_value(record.get("id")),
        "object": clean_value(
            record.get("object")
        ) or "customer",
        "email": clean_value(
            record.get("email")
        ),
        "name": clean_value(
            record.get("name")
        ),
        "created": record.get("created"),
        "currency": clean_value(
            record.get("currency")
        ),
        "delinquent": record.get(
            "delinquent"
        ),
        "livemode": record.get(
            "livemode",
            False
        ),
    }

    validated = StripeCustomer.model_validate(
        customer_data
    )

    return validated.model_dump(
        mode="json"
    )


# ============================================================
# VALIDATE CHARGE
# ============================================================

def validate_charge(record):
    """Validate a Stripe Charge."""

    charge_data = {
        "id": clean_value(
            record.get("id")
        ),
        "object": clean_value(
            record.get("object")
        ) or "charge",
        "amount": record.get(
            "amount"
        ),
        "currency": clean_value(
            record.get("currency")
        ),
        "customer": clean_value(
            record.get("customer")
        ),
        "status": clean_value(
            record.get("status")
        ),
        "paid": record.get(
            "paid"
        ),
        "refunded": record.get(
            "refunded"
        ),
        "created": record.get(
            "created"
        ),
        "description": clean_value(
            record.get("description")
        ),
    }

    validated = StripeCharge.model_validate(
        charge_data
    )

    return validated.model_dump(
        mode="json"
    )


# ============================================================
# VALIDATE INVOICE
# ============================================================

def validate_invoice(record):
    """Validate a Stripe Invoice."""

    invoice_data = {
        "id": clean_value(
            record.get("id")
        ),
        "object": clean_value(
            record.get("object")
        ) or "invoice",
        "customer": clean_value(
            record.get("customer")
        ),
        "status": clean_value(
            record.get("status")
        ),
        "total": record.get(
            "total"
        ),
        "currency": clean_value(
            record.get("currency")
        ),
        "created": record.get(
            "created"
        ),
        "paid": record.get(
            "paid"
        ),
    }

    validated = StripeInvoice.model_validate(
        invoice_data
    )

    return validated.model_dump(
        mode="json"
    )


# ============================================================
# TRANSFORM RECORDS
# ============================================================

def transform_records(
    data,
    object_name,
    validator
):
    """
    Clean, deduplicate and validate Stripe records.
    """

    records = get_records(data)

    print(
        f"Records before duplicate removal: "
        f"{len(records)}"
    )

    records = remove_duplicates(records)

    print(
        f"Records after duplicate removal: "
        f"{len(records)}"
    )

    transformed = []

    processed_time = datetime.now(
        timezone.utc
    ).isoformat()

    invalid_count = 0

    for record in records:

        if not isinstance(
            record,
            dict
        ):
            print(
                "Skipping invalid record: "
                "not a dictionary"
            )

            invalid_count += 1

            continue

        try:

            clean_record = validator(
                record
            )

            clean_record["_source"] = "stripe"

            clean_record["_object"] = object_name

            clean_record["_processed_at"] = (
                processed_time
            )

            transformed.append(
                clean_record
            )

        except Exception as error:

            invalid_count += 1

            print(
                f"Skipping invalid "
                f"{object_name} record: "
                f"{error}"
            )

    print(
        f"Invalid records skipped: "
        f"{invalid_count}"
    )

    return transformed


# ============================================================
# SAVE JSON
# ============================================================

def save_json(data, filename):

    output_file = (
        PROCESSED_FOLDER / filename
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Saved {len(data)} records to:"
    )

    print(output_file)


# ============================================================
# TRANSFORM CUSTOMERS
# ============================================================

def transform_customers():

    print("\nTransforming Customers...")

    data = load_json(
        "customers.json"
    )

    customers = transform_records(
        data,
        "Customer",
        validate_customer
    )

    save_json(
        customers,
        "customers.json"
    )

    return customers


# ============================================================
# TRANSFORM CHARGES
# ============================================================

def transform_charges():

    print("\nTransforming Charges...")

    data = load_json(
        "charges.json"
    )

    charges = transform_records(
        data,
        "Charge",
        validate_charge
    )

    save_json(
        charges,
        "charges.json"
    )

    return charges


# ============================================================
# TRANSFORM INVOICES
# ============================================================

def transform_invoices():

    print("\nTransforming Invoices...")

    data = load_json(
        "invoices.json"
    )

    invoices = transform_records(
        data,
        "Invoice",
        validate_invoice
    )

    save_json(
        invoices,
        "invoices.json"
    )

    return invoices


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=================================================="
    )

    print(
        "STARTING STRIPE TRANSFORMATION"
    )

    print(
        "=================================================="
    )

    try:

        customers = transform_customers()

        charges = transform_charges()

        invoices = transform_invoices()

        print(
            "\n=================================================="
        )

        print(
            "STRIPE TRANSFORMATION COMPLETED"
        )

        print(
            "=================================================="
        )

        print(
            f"Customers transformed: "
            f"{len(customers)}"
        )

        print(
            f"Charges transformed: "
            f"{len(charges)}"
        )

        print(
            f"Invoices transformed: "
            f"{len(invoices)}"
        )

        print(
            "=================================================="
        )

    except Exception as error:

        print(
            "\nSTRIPE TRANSFORMATION FAILED"
        )

        print(
            f"Error: {error}"
        )

        raise


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()