import json
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

# Project root:
# enterprise-etl-pipeline
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Raw Salesforce data
RAW_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "salesforce"
)

# Processed Salesforce data
PROCESSED_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "salesforce"
)

# Create processed folder automatically
PROCESSED_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(filename):
    """
    Load a JSON file from the raw Salesforce folder.
    """

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
        data = json.load(file)

    return data


# ============================================================
# GET RECORDS
# ============================================================

def get_records(data):
    """
    Get Salesforce records from JSON.

    Supports both formats:

    Format 1:
    {
        "records": [...]
    }

    Format 2:
    [
        {...},
        {...}
    ]
    """

    # If JSON is a dictionary
    if isinstance(data, dict):

        records = data.get(
            "records",
            []
        )

        if not isinstance(records, list):
            raise ValueError(
                "'records' must be a list"
            )

        return records

    # If JSON is already a list
    if isinstance(data, list):

        return data

    raise ValueError(
        "Invalid JSON format. "
        "Expected a list or dictionary."
    )


# ============================================================
# CLEAN VALUES
# ============================================================

def clean_value(value):
    """
    Clean individual values.
    """

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()

        if value == "":
            return None

    return value


# ============================================================
# TRANSFORM RECORDS
# ============================================================

def transform_records(
    data,
    object_name
):
    """
    Clean Salesforce records and add ETL metadata.
    """

    records = get_records(data)

    transformed = []

    processed_time = datetime.now(
        timezone.utc
    ).isoformat()

    for record in records:

        if not isinstance(
            record,
            dict
        ):
            continue

        clean_record = {}

        for key, value in record.items():

            # Salesforce API metadata
            # is not required for our data
            if key == "attributes":
                continue

            clean_record[key] = clean_value(
                value
            )

        # ETL metadata
        clean_record["_source"] = (
            "salesforce"
        )

        clean_record["_object"] = (
            object_name
        )

        clean_record["_processed_at"] = (
            processed_time
        )

        transformed.append(
            clean_record
        )

    return transformed


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    data,
    filename
):
    """
    Save transformed records as JSON.
    """

    output_file = (
        PROCESSED_FOLDER
        / filename
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

    print(
        output_file
    )


# ============================================================
# TRANSFORM ACCOUNTS
# ============================================================

def transform_accounts():

    print(
        "\nTransforming Accounts..."
    )

    data = load_json(
        "accounts.json"
    )

    accounts = transform_records(
        data,
        "Account"
    )

    save_json(
        accounts,
        "accounts.json"
    )

    return accounts


# ============================================================
# TRANSFORM CONTACTS
# ============================================================

def transform_contacts():

    print(
        "\nTransforming Contacts..."
    )

    data = load_json(
        "contacts.json"
    )

    contacts = transform_records(
        data,
        "Contact"
    )

    save_json(
        contacts,
        "contacts.json"
    )

    return contacts


# ============================================================
# TRANSFORM OPPORTUNITIES
# ============================================================

def transform_opportunities():

    print(
        "\nTransforming Opportunities..."
    )

    data = load_json(
        "opportunities.json"
    )

    opportunities = transform_records(
        data,
        "Opportunity"
    )

    save_json(
        opportunities,
        "opportunities.json"
    )

    return opportunities


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=================================================="
    )

    print(
        "STARTING SALESFORCE TRANSFORMATION"
    )

    print(
        "=================================================="
    )

    print(
        f"\nRaw data folder:"
    )

    print(
        RAW_FOLDER
    )

    print(
        f"\nProcessed data folder:"
    )

    print(
        PROCESSED_FOLDER
    )

    try:

        # ------------------------------------------------
        # Accounts
        # ------------------------------------------------

        accounts = transform_accounts()

        # ------------------------------------------------
        # Contacts
        # ------------------------------------------------

        contacts = transform_contacts()

        # ------------------------------------------------
        # Opportunities
        # ------------------------------------------------

        opportunities = (
            transform_opportunities()
        )

        # ------------------------------------------------
        # Final summary
        # ------------------------------------------------

        print(
            "\n=================================================="
        )

        print(
            "SALESFORCE TRANSFORMATION COMPLETED"
        )

        print(
            "=================================================="
        )

        print(
            f"Accounts transformed: "
            f"{len(accounts)}"
        )

        print(
            f"Contacts transformed: "
            f"{len(contacts)}"
        )

        print(
            f"Opportunities transformed: "
            f"{len(opportunities)}"
        )

        print(
            "\nProcessed files:"
        )

        print(
            "1. accounts.json"
        )

        print(
            "2. contacts.json"
        )

        print(
            "3. opportunities.json"
        )

        print(
            "\n=================================================="
        )

    except Exception as error:

        print(
            "\n=================================================="
        )

        print(
            "SALESFORCE TRANSFORMATION FAILED"
        )

        print(
            "=================================================="
        )

        print(
            f"Error: {error}"
        )

        print(
            "=================================================="
        )

        raise


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()