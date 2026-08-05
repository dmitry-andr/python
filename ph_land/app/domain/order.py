from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from .models import UTCTZ, new_id


class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Order(BaseModel):
    id: str = Field(default_factory=new_id)    
    customer_id: str
    service_id: str
    provider_id: str
    start_time: datetime  # must be tz-aware (UTC)
    end_time: datetime
    details: str = ""
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTCTZ))

    @model_validator(mode="after")
    def check_time_range(self) -> "Order":
        if self.start_time.tzinfo is None or self.end_time.tzinfo is None:
            raise ValueError("start_time and end_time must be timezone-aware")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self

    def overlaps(self, other: "Order") -> bool:
        """True if this order's time range overlaps another's.
        Only meaningful when comparing orders for the same provider."""
        return self.start_time < other.end_time and other.start_time < self.end_time
