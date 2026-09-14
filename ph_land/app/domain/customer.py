from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from .models import UTCTZ, new_id


class Customer(BaseModel):
    id: Optional[str] = None
    first_name: str = Field(..., min_length=1)
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTCTZ))

    @model_validator(mode="before")
    @classmethod
    def normalize_empty_fields(cls, data):
        if isinstance(data, dict):
            for field_name in ("id", "email", "phone"):
                value = data.get(field_name)
                if isinstance(value, str) and not value.strip():
                    data[field_name] = None
        return data

    @model_validator(mode="after")
    def validate_contact_method(self) -> "Customer":
        if self.id is None:
            self.id = new_id()

        email_present = bool(self.email)
        phone_present = bool(self.phone and self.phone.strip())

        if not email_present and not phone_present:
            raise ValueError("Customer requires either email or phone")

        if self.email is not None and "@" not in str(self.email):
            raise ValueError("Email must contain @")

        return self
