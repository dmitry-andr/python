"""
Domain models for the small-business service-order ontology.

Requires: pip install pydantic --break-system-packages

Design choices:
- All models are Pydantic BaseModels: validation happens automatically
  whenever data crosses a boundary (loaded from JSON, received via API).
- All datetimes are timezone-aware and stored/compared in UTC. Convert
  to the business's local timezone only at display time.
- IDs are plain strings (uuid4 hex) so this maps cleanly onto JSON files
  today and onto DB primary keys later without changing calling code.
- `provider_id` is nullable everywhere from day one, so adding staff
  later is just "start populating a field", not a schema change.
"""

from __future__ import annotations

from datetime import datetime, time, date, timezone

UTCTZ = timezone.utc
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, EmailStr, model_validator


def new_id() -> str:
    return uuid4().hex


# ---------------------------------------------------------------
# Business
# ---------------------------------------------------------------
class Business(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    timezone: str  # IANA tz name, e.g. "America/New_York"


# ---------------------------------------------------------------
# Availability — belongs to a Provider if providers exist,
# otherwise to the Business directly. Exactly one of the two
# owner fields must be set.
# ---------------------------------------------------------------
class Weekday(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class AvailabilityRule(BaseModel):
    id: str = Field(default_factory=new_id)
    business_id: str
    provider_id: Optional[str] = None  # None => rule applies to the business as a whole
    weekday: Weekday
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def check_time_order(self) -> "AvailabilityRule":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AvailabilityException(BaseModel):
    """One-off override: a closure, holiday, or special extra hours."""
    id: str = Field(default_factory=new_id)
    business_id: str
    provider_id: Optional[str] = None
    date: date
    is_closed: bool = True
    override_start: Optional[time] = None
    override_end: Optional[time] = None

    @model_validator(mode="after")
    def check_override_consistency(self) -> "AvailabilityException":
        if not self.is_closed and (self.override_start is None or self.override_end is None):
            raise ValueError("override_start/override_end required when is_closed=False")
        return self


