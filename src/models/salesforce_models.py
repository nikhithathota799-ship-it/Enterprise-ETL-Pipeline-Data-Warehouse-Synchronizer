from typing import Optional
from pydantic import BaseModel


class SalesforceAccount(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class SalesforceContact(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    account_id: Optional[str] = None


class SalesforceOpportunity(BaseModel):
    id: str
    name: str
    stage_name: Optional[str] = None
    amount: Optional[float] = None
    close_date: Optional[str] = None
    account_id: Optional[str] = None