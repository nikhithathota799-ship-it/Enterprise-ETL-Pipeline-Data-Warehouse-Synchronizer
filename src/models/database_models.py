"""
SQLAlchemy models for the data warehouse (Member 4).

Six tables total:
  - accounts, contacts, opportunities   (from Salesforce, Member 1)
  - stripe_customers, stripe_charges, stripe_invoices   (from Stripe, Member 2)

Each table keeps the original source id as its primary key (these ids are
already globally unique per source), plus _source and _processed_at columns
carried over from the processed JSON files.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from src.loading.database import Base


# ============================================================
# SALESFORCE TABLES
# ============================================================

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)

    _source = Column(String, nullable=False, default="salesforce")
    _processed_at = Column(DateTime(timezone=True), nullable=True)

    contacts = relationship("Contact", back_populates="account")
    opportunities = relationship("Opportunity", back_populates="account")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)

    _source = Column(String, nullable=False, default="salesforce")
    _processed_at = Column(DateTime(timezone=True), nullable=True)

    account = relationship("Account", back_populates="contacts")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    stage_name = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    close_date = Column(String, nullable=True)  # stored as-is (YYYY-MM-DD string)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)

    _source = Column(String, nullable=False, default="salesforce")
    _processed_at = Column(DateTime(timezone=True), nullable=True)

    account = relationship("Account", back_populates="opportunities")


# ============================================================
# STRIPE TABLES
# ============================================================

class StripeCustomer(Base):
    __tablename__ = "stripe_customers"

    id = Column(String, primary_key=True)
    object = Column(String, nullable=True)
    email = Column(String, nullable=True)
    name = Column(String, nullable=True)
    created = Column(Integer, nullable=True)  # unix timestamp, as Stripe sends it
    currency = Column(String, nullable=True)
    delinquent = Column(Boolean, nullable=True)
    livemode = Column(Boolean, nullable=True)

    _source = Column(String, nullable=False, default="stripe")
    _processed_at = Column(DateTime(timezone=True), nullable=True)


class StripeCharge(Base):
    __tablename__ = "stripe_charges"

    id = Column(String, primary_key=True)
    object = Column(String, nullable=True)
    amount = Column(Integer, nullable=True)  # smallest currency unit (e.g. cents)
    currency = Column(String, nullable=True)
    customer = Column(String, nullable=True)  # Stripe customer id (no FK: may not be loaded)
    status = Column(String, nullable=True)
    paid = Column(Boolean, nullable=True)
    refunded = Column(Boolean, nullable=True)
    created = Column(Integer, nullable=True)
    description = Column(String, nullable=True)

    _source = Column(String, nullable=False, default="stripe")
    _processed_at = Column(DateTime(timezone=True), nullable=True)


class StripeInvoice(Base):
    __tablename__ = "stripe_invoices"

    id = Column(String, primary_key=True)
    object = Column(String, nullable=True)
    customer = Column(String, nullable=True)
    status = Column(String, nullable=True)
    total = Column(Integer, nullable=True)
    currency = Column(String, nullable=True)
    created = Column(Integer, nullable=True)
    paid = Column(Boolean, nullable=True)

    _source = Column(String, nullable=False, default="stripe")
    _processed_at = Column(DateTime(timezone=True), nullable=True)
