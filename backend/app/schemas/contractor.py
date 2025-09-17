from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ContractorBase(BaseModel):
    org_name: str = Field(..., min_length=1)
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    active: bool = True

class ContractorCreate(ContractorBase): pass
class ContractorUpdate(BaseModel):
    org_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    active: Optional[bool] = None

class ContractorRead(ContractorBase):
    id: str
    class Config:
        from_attributes = True

