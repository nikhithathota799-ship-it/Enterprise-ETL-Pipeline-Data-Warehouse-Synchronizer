from pydantic import BaseModel
from typing import Optional


class SalesforceAccount(BaseModel):
    id: str
    name: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None