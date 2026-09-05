"""
Member 2 — External API Extraction: Stripe

Connects to the Stripe API, paginates through Customers, Charges, and
Invoices, retries transient failures, validates records with Pydantic,
and writes raw JSON to data/raw/external/.

Auth: Stripe secret API key, read from the STRIPE_API_KEY environment
variable (never hardcode keys).

Run:
    export STRIPE_API_KEY="sk_test_..."
    python -m src.extraction.external_api
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.models.external_models import (
    StripeCustomer,
    StripeCharge,
    StripeInvoice,
)

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

STRIPE_API_BASE = "https://api.stripe.com/v1"
RAW_OUTPUT_DIR = Path("data/raw/external")
PAGE_LIMIT = 100  # Stripe's max per page

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stripe_extraction")


class StripeAuthError(Exception):
    """Raised when the Stripe API key is missing or invalid."""


class StripeAPIError(Exception):
    """Raised for non-retryable Stripe API errors (4xx other than 429)."""


def get_stripe_session() -> requests.Session:
    """Build an authenticated requests session for Stripe."""
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise StripeAuthError(
            "STRIPE_API_KEY environment variable is not set. "
            "Export it before running extraction."
        )
    session = requests.Session()
    session.auth = (api_key, "")  # Stripe uses HTTP Basic auth: key as username, blank password
    return session


# --------------------------------------------------------------------------
# Retry-wrapped HTTP call
# --------------------------------------------------------------------------

def _is_retryable(exc: BaseException) -> bool:
    """Retry on connection errors, timeouts, and 429/5xx responses."""
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        return status == 429 or (status is not None and status >= 500)
    return False


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout, requests.HTTPError)),
)
def _get_page(session: requests.Session, endpoint: str, params: dict[str, Any]) -> dict:
    """Fetch a single page from a Stripe list endpoint, with retry on transient errors."""
    url = f"{STRIPE_API_BASE}/{endpoint}"
    logger.info("GET %s params=%s", url, params)
    resp = session.get(url, params=params, timeout=15)

    if resp.status_code == 401:
        raise StripeAuthError("Stripe rejected the API key (401 Unauthorized).")
    if resp.status_code == 429:
        logger.warning("Rate limited by Stripe (429). Backing off and retrying.")
        resp.raise_for_status()  # triggers retry
    if 400 <= resp.status_code < 500:
        # Non-retryable client error (bad request, not found, etc.)
        logger.error("Stripe API error %s: %s", resp.status_code, resp.text)
        raise StripeAPIError(f"Stripe API error {resp.status_code}: {resp.text}")
    resp.raise_for_status()  # 5xx -> retry via tenacity

    return resp.json()


# --------------------------------------------------------------------------
# Pagination
# --------------------------------------------------------------------------

def fetch_all(session: requests.Session, endpoint: str, extra_params: dict | None = None) -> list[dict]:
    """
    Paginate through a Stripe list endpoint using cursor-based pagination
    (Stripe uses `starting_after` with object IDs).
    """
    records: list[dict] = []
    params: dict[str, Any] = {"limit": PAGE_LIMIT, **(extra_params or {})}
    starting_after: str | None = None
    page_num = 1

    while True:
        if starting_after:
            params["starting_after"] = starting_after

        page = _get_page(session, endpoint, params)
        batch = page.get("data", [])
        records.extend(batch)
        logger.info("Fetched page %d for '%s': %d records (total so far: %d)",
                    page_num, endpoint, len(batch), len(records))

        if not page.get("has_more") or not batch:
            break

        starting_after = batch[-1]["id"]
        page_num += 1

    return records


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_records(records: list[dict], model) -> list[dict]:
    """Validate raw records against a Pydantic model; log and skip bad ones."""
    valid: list[dict] = []
    for rec in records:
        try:
            validated = model.model_validate(rec)
            valid.append(validated.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001 - log and continue, don't kill the whole run
            logger.warning("Skipping invalid %s record id=%s: %s",
                            model.__name__, rec.get("id", "unknown"), exc)
    return valid


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

def save_raw_json(records: list[dict], filename: str) -> Path:
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_OUTPUT_DIR / filename
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)
    logger.info("Saved %d records to %s", len(records), out_path)
    return out_path


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def extract_customers(session: requests.Session) -> list[dict]:
    raw = fetch_all(session, "customers")
    return validate_records(raw, StripeCustomer)


def extract_charges(session: requests.Session) -> list[dict]:
    raw = fetch_all(session, "charges")
    return validate_records(raw, StripeCharge)


def extract_invoices(session: requests.Session) -> list[dict]:
    raw = fetch_all(session, "invoices")
    return validate_records(raw, StripeInvoice)


def run_extraction() -> None:
    logger.info("Starting Stripe extraction (Member 2)")
    session = get_stripe_session()

    customers = extract_customers(session)
    save_raw_json(customers, "customers.json")

    charges = extract_charges(session)
    save_raw_json(charges, "charges.json")

    invoices = extract_invoices(session)
    save_raw_json(invoices, "invoices.json")

    logger.info(
        "Extraction complete: %d customers, %d charges, %d invoices",
        len(customers), len(charges), len(invoices),
    )


if __name__ == "__main__":
    run_extraction()
