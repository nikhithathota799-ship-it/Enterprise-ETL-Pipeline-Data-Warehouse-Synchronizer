from src.transformation.salesforce_transform import (
    clean_value,
    remove_duplicates,
    validate_account,
    validate_contact,
    validate_opportunity,
)

from src.transformation.stripe_transform import (
    validate_customer,
    validate_charge,
    validate_invoice,
)


# ============================================================
# SALESFORCE TESTS
# ============================================================

def test_clean_value():
    assert clean_value("  Hello  ") == "Hello"
    assert clean_value("") is None
    assert clean_value("   ") is None
    assert clean_value(None) is None


def test_remove_salesforce_duplicates():

    records = [
        {"Id": "001", "Name": "Company A"},
        {"Id": "002", "Name": "Company B"},
        {"Id": "001", "Name": "Company A"},
    ]

    result = remove_duplicates(records)

    assert len(result) == 2
    assert result[0]["Id"] == "001"
    assert result[1]["Id"] == "002"


def test_validate_account():

    record = {
        "Id": "001TEST",
        "Name": "Test Company",
        "Industry": "Technology",
        "Phone": "1234567890",
        "Website": "www.test.com",
    }

    result = validate_account(record)

    assert result["id"] == "001TEST"
    assert result["name"] == "Test Company"
    assert result["industry"] == "Technology"


def test_validate_contact():

    record = {
        "Id": "003TEST",
        "FirstName": "John",
        "LastName": "Smith",
        "Email": "john@example.com",
        "Phone": "1234567890",
        "AccountId": "001TEST",
    }

    result = validate_contact(record)

    assert result["id"] == "003TEST"
    assert result["first_name"] == "John"
    assert result["last_name"] == "Smith"
    assert result["email"] == "john@example.com"


def test_validate_opportunity():

    record = {
        "Id": "006TEST",
        "Name": "Test Opportunity",
        "StageName": "Negotiation",
        "Amount": 50000.0,
        "CloseDate": "2026-12-31",
        "AccountId": "001TEST",
    }

    result = validate_opportunity(record)

    assert result["id"] == "006TEST"
    assert result["name"] == "Test Opportunity"
    assert result["stage_name"] == "Negotiation"
    assert result["amount"] == 50000.0


# ============================================================
# STRIPE TESTS
# ============================================================

def test_validate_stripe_customer():

    record = {
        "id": "cus_TEST001",
        "object": "customer",
        "email": "test@example.com",
        "name": "Test Customer",
        "created": 1700000000,
        "currency": "usd",
        "delinquent": False,
        "livemode": False,
    }

    result = validate_customer(record)

    assert result["id"] == "cus_TEST001"
    assert result["email"] == "test@example.com"
    assert result["name"] == "Test Customer"


def test_validate_stripe_charge():

    record = {
        "id": "ch_TEST001",
        "object": "charge",
        "amount": 5000,
        "currency": "usd",
        "customer": "cus_TEST001",
        "status": "succeeded",
        "paid": True,
        "refunded": False,
        "created": 1700000000,
        "description": "Test payment",
    }

    result = validate_charge(record)

    assert result["id"] == "ch_TEST001"
    assert result["amount"] == 5000
    assert result["currency"] == "usd"
    assert result["paid"] is True


def test_validate_stripe_invoice():

    record = {
        "id": "in_TEST001",
        "object": "invoice",
        "customer": "cus_TEST001",
        "status": "paid",
        "total": 10000,
        "currency": "usd",
        "created": 1700000000,
        "paid": True,
    }

    result = validate_invoice(record)

    assert result["id"] == "in_TEST001"
    assert result["total"] == 10000
    assert result["currency"] == "usd"
    assert result["paid"] is True