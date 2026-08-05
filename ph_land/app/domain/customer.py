from __future__ import annotations

from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator

from .models import new_id


class Customer(BaseModel):
    id: str = Field(default_factory=new_id)
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @model_validator(mode="after")
    def require_contact_method(self) -> "Customer":
        if not self.email and not self.phone:
            raise ValueError("Customer requires at least an email or a phone number")
        return self
