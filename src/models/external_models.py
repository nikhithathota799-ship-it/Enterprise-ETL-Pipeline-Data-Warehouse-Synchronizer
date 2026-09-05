"""
Pydantic models for Stripe API extraction (Member 2).

These validate the shape of data pulled from Stripe's REST API before
it's written to raw JSON storage. Mirrors the pattern used in
salesforce_models.py (Member 1) for consistency across the pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class StripeCustomer(BaseModel):
    """A single Stripe Customer object."""

    model_config = ConfigDict(extra="allow")  # keep unmapped Stripe fields instead of dropping them

    id: str
    object: str = "customer"
    email: Optional[str] = None
    name: Optional[str] = None
    created: int  # unix timestamp, as returned by Stripe
    currency: Optional[str] = None
    delinquent: Optional[bool] = None
    livemode: bool = False

    @property
    def created_at(self) -> datetime:
        return datetime.utcfromtimestamp(self.created)


class StripeCharge(BaseModel):
    """A single Stripe Charge object."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "charge"
    amount: int  # smallest currency unit (e.g. cents)
    currency: str
    customer: Optional[str] = None  # customer id
    status: str
    paid: bool
    refunded: bool
    created: int
    description: Optional[str] = None

    @property
    def created_at(self) -> datetime:
        return datetime.utcfromtimestamp(self.created)


class StripeInvoice(BaseModel):
    """A single Stripe Invoice object."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "invoice"
    customer: Optional[str] = None
    status: Optional[str] = None
    total: int
    currency: str
    created: int
    paid: bool

    @property
    def created_at(self) -> datetime:
        return datetime.utcfromtimestamp(self.created)


class StripeListResponse(BaseModel):
    """
    Wrapper matching Stripe's list endpoint response shape:
    { "object": "list", "data": [...], "has_more": bool, "url": "..." }
    """

    object: str = "list"
    data: list[dict] = Field(default_factory=list)
    has_more: bool = False
    url: Optional[str] = None
