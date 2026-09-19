"""Validated graph inputs. No adapter credentials or authority decisions live here."""

from datetime import UTC, datetime
from typing import Annotated, Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

Text = Annotated[str, Field(min_length=1)]
Source = Literal["real", "real API, demo devices", "twin"]
Role = Literal["owner", "adult", "teen", "child", "guest", "caregiver"]
RatePlan = Literal["comed_time_of_day", "comed_hourly", "twin"]
AssetKind = Literal[
    "ev",
    "home_battery",
    "solar",
    "appliance",
    "hvac_zone",
    "lock",
    "camera",
    "light",
    "doorbell",
    "shade",
]
Scope = Literal["all", "people", "member", "energy", "environment"]
SCOPES = ("all", "people", "member", "energy", "environment")


class GraphError(ValueError):
    """Safe, caller-facing graph failure; never include input payloads."""


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise GraphError("A timezone-aware timestamp is required.")
    return value.astimezone(UTC)


def now() -> datetime:
    return datetime.now(UTC)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Location(Model):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    source: Literal["declared", "twin"]
    street_address: Text | None = None


class Household(Model):
    autonomy_paused: bool = False
    id: UUID
    name: Text
    timezone: Text
    locale: Text
    rate_plan: RatePlan | None = None
    constitution_version: int | None = Field(default=None, gt=0)
    location: Location | None = None
    budgets: dict[str, Annotated[float, Field(ge=0)]] | None = None

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (KeyError, ValueError):
            raise ValueError("Unknown timezone") from None
        return value


class Entity(Model):
    household_id: UUID
    id: UUID


class Member(Entity):
    display_name: Text
    role: Role


class MemberAccount(Model):
    household_id: UUID
    provider: Text
    sub: Text
    member_id: UUID


class TrustedContact(Entity):
    display_name: Text
    relationship: Text
    member_id: UUID | None = None
    safe_word_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None


class ContactChannel(Entity):
    contact_id: UUID
    kind: Literal["phone", "email", "hirz_app"]
    value_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    verified_at: AwareDatetime | None = None
    source: Source


class PhysicalParameters(Model):
    capacity_kwh: float | None = Field(default=None, gt=0)
    charger_kw: float | None = Field(default=None, gt=0)
    power_kw: float | None = Field(default=None, gt=0)
    efficiency: float | None = Field(default=None, gt=0, le=1)
    reserve_soc: float | None = Field(default=None, ge=0, le=1)
    kw_peak: float | None = Field(default=None, gt=0)
    cycle_minutes: int | None = Field(default=None, gt=0)
    cycle_kwh: float | None = Field(default=None, gt=0)
    thermal_mass_kwh_per_f: float | None = Field(default=None, gt=0)
    resistance_f_per_kw: float | None = Field(default=None, gt=0)
    hvac_kw: float | None = Field(default=None, gt=0)
    tilt_degrees: float | None = Field(default=None, ge=0, le=90)
    orientation_degrees: float | None = Field(default=None, ge=0, lt=360)


class Asset(Entity):
    name: Text
    kind: AssetKind
    owner_member_id: UUID | None = None
    capabilities: tuple[Text, ...] | None = None
    physical: PhysicalParameters | None = None


class AssetBinding(Entity):
    asset_id: UUID
    adapter: Text
    entity_id: Text


class AssetPolicy(Entity):
    asset_id: UUID
    soc_min: float | None = Field(default=None, ge=0, le=1)
    needed_by: AwareDatetime | None = None


class Schedule(Entity):
    name: Text
    member_id: UUID | None = None


class ScheduleEvent(Entity):
    schedule_id: UUID
    member_id: UUID | None = None
    zone_id: UUID | None = None
    kind: Literal["arrival", "departure", "calendar", "quiet_hours"]
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    expected_at: AwareDatetime | None = None
    title: Text | None = None

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("Event must have positive duration")
        if self.expected_at is not None and not (
            self.starts_at <= self.expected_at < self.ends_at
        ):
            raise ValueError("Expected time must be inside the event window")
        return self


class Routine(Entity):
    name: Text
    member_id: UUID | None = None
    days: tuple[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"], ...]
    from_time: Annotated[str, Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]
    to_time: Annotated[str, Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]


class Preference(Entity):
    member_id: UUID
    scope: Literal["household", "member"]
    key: Text
    value: JsonValue
    source: Literal["declared", "learned_accepted"]
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def temperature(self) -> Self:
        if self.key == "temperature_target_f" and (
            isinstance(self.value, bool) or not isinstance(self.value, (int, float))
        ):
            raise ValueError("Temperature preference must be numeric")
        return self


class ObservationState(Model):
    soc: float | None = Field(default=None, ge=0, le=1)
    temp_f: float | None = None
    target_f: float | None = None
    power_kw: float | None = None
    present: bool | None = None
    sleeping: bool | None = None
    zone_id: UUID | None = None
    plugged_in: bool | None = None
    available: bool | None = None
    locked: bool | None = None
    on: bool | None = None
    recovery_score: int | None = Field(default=None, ge=0, le=100)


class Observation(Entity):
    member_id: UUID | None = None
    asset_id: UUID | None = None
    observed_at: AwareDatetime
    source: Source
    state: ObservationState

    @model_validator(mode="after")
    def one_subject(self) -> Self:
        if self.member_id is not None and self.asset_id is not None:
            raise ValueError("An observation has only one subject")
        return self


# Closed table/model mapping: callers cannot supply SQL identifiers or arbitrary models.
MODELS: dict[str, type[Model]] = {
    "households": Household,
    "members": Member,
    "member_accounts": MemberAccount,
    "trusted_contacts": TrustedContact,
    "contact_channels": ContactChannel,
    "assets": Asset,
    "asset_bindings": AssetBinding,
    "asset_policies": AssetPolicy,
    "schedules": Schedule,
    "schedule_events": ScheduleEvent,
    "routines": Routine,
    "preferences": Preference,
    "observations": Observation,
}
