from __future__ import annotations

from pydantic import BaseModel, Field

from .models import new_id


class Provider(BaseModel):
    id: str = Field(default_factory=new_id)
    business_id: str
    name: str
