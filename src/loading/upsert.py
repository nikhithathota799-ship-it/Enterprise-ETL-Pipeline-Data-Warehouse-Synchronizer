"""
Upsert helper (Member 4).

Provides a single reusable function that inserts new rows, and updates
existing rows in place (matched by primary key) instead of erroring out
or creating duplicates. Uses PostgreSQL's native ON CONFLICT ... DO UPDATE,
wrapped in a transaction so a bad batch doesn't leave the table half-written.
"""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError


def upsert_records(session, model, records, conflict_column="id"):
    """
    Insert or update a batch of records into `model`'s table.

    - session: an open SQLAlchemy session (from database.get_session())
    - model: the ORM class (e.g. Account, StripeCustomer)
    - records: list of dicts, each matching the model's columns
    - conflict_column: the column used to detect an existing row (default "id")

    Returns (inserted_or_updated_count, skipped_count).
    """

    if not records:
        print(f"No records to upsert for {model.__tablename__}.")
        return 0, 0

    table = model.__table__
    valid_columns = {c.name for c in table.columns}

    clean_records = []
    skipped = 0

    for record in records:
        # Only keep keys that actually exist as columns on this table -
        # protects against stray extra fields in the JSON breaking the insert.
        filtered = {k: v for k, v in record.items() if k in valid_columns}

        if conflict_column not in filtered or filtered[conflict_column] is None:
            skipped += 1
            continue

        clean_records.append(filtered)

    if not clean_records:
        print(f"All {skipped} records for {model.__tablename__} were invalid, skipping.")
        return 0, skipped

    # Columns to overwrite on conflict = every column except the conflict key itself
    update_columns = {
        col: getattr(pg_insert(table).excluded, col)
        for col in valid_columns
        if col != conflict_column
    }

    try:
        stmt = pg_insert(table).values(clean_records)
        stmt = stmt.on_conflict_do_update(
            index_elements=[conflict_column],
            set_=update_columns,
        )

        session.execute(stmt)
        session.commit()

        print(
            f"Upserted {len(clean_records)} records into "
            f"{model.__tablename__} ({skipped} skipped as invalid)."
        )

        return len(clean_records), skipped

    except SQLAlchemyError as error:
        session.rollback()
        print(f"Upsert FAILED for {model.__tablename__}: {error}")
        raise
