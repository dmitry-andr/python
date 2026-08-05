from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .models import new_id


class Service(BaseModel):
    id: str = Field(default_factory=new_id)
    business_id: str
    service_type: str
    service_sub_type: str
    name: str
    description: str
