"""Canonical Action and risk assessment from ARCHITECTURE §4; no authority."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator

from hirz.risk import CLASSES, RiskBand

Role = Literal["owner", "adult", "caregiver", "teen", "child", "guest", "unknown"]
ROLES: tuple[Role, ...] = (
    "owner",
    "adult",
    "caregiver",
    "teen",
    "child",
    "guest",
    "unknown",
)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class RiskFactor(Model):
    factor: Literal[
        "unknown_requester",
        "occupant_asleep",
        "guest_present",
        "state_stale",
        "deviation_from_baseline",
        "scam_pattern",
        "outside_bounds",
        "scoring_error",
    ]
    effect: Literal["+1 band", "→ CRITICAL"]
    evidence: str


class RiskAssessment(Model):
    band: RiskBand
    base_band: RiskBand
    factors: tuple[RiskFactor, ...]


class Target(Model):
    adapter: str
    entity: str
    zone: str | None = None


class Requester(Model):
    member_id: str | None
    role: Role
    surface: Literal["alexa", "app", "scheduler"]
    speaker: str | None = None
    claimed_author: str | None = None


class ExpectedEffect(Model):
    entity: str
    attr: str
    value: JsonValue
    by: datetime


class Action(Model):
    action_id: str
    action_class: str = Field(alias="class")
    target: Target
    params: dict[str, JsonValue]
    requested_by: Requester
    reason: str
    plan_id: str | None = None
    scheduled_for: datetime | None = None
    expected_effect: ExpectedEffect | None = None
    content_hash: str

    @field_validator("action_class")
    @classmethod
    def known_class(cls, value: str) -> str:
        if value not in CLASSES:
            raise ValueError("Unknown action class")
        return value

    @field_validator("scheduled_for")
    @classmethod
    def aware_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("Action time must be timezone-aware")
        return value
