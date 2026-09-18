"""Pure item 8 scoring; trusted fact selection belongs to the item 9 pipeline."""

from collections.abc import Mapping
from typing import Annotated

from pydantic import Field, StrictBool, ValidationError

from hirz.constitution.conditions import FactError, number
from hirz.constitution.evaluator import guards
from hirz.constitution.schema import Numeric, Rule
from hirz.pipeline.models import Action, Model, RiskAssessment, RiskFactor
from hirz.risk import CLASSES, RiskBand

Age = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]


class RiskFacts(Model):
    observation_ages_seconds: tuple[Age, ...] | None = None
    sleeping_in_target_zone: StrictBool | None = None
    sleeping_any: StrictBool | None = None
    target_is_bedroom: StrictBool | None = None
    guest_present: StrictBool | None = None
    doorbell_online: StrictBool | None = None
    baseline_target_f: Numeric | None = None
    scam_pattern: StrictBool | None = None


def required[T](value: T | None, path: str) -> T:
    if value is None:
        raise FactError(path)
    return value


def score(
    action: Action, facts: RiskFacts | Mapping[str, object], rule: Rule
) -> RiskAssessment:
    """Return risk, never permission. Unknown required facts fail closed.

    The caller selects the rule and supplies complete, household-scoped facts.
    An empty observation tuple explicitly asserts no observations are required.
    Model-assisted Protect advice must not be supplied as a decision fact.
    """
    base = band = RiskBand.CRITICAL
    factors: list[RiskFactor] = []

    def add(factor: RiskFactor) -> None:
        nonlocal band
        factors.append(factor)
        bands = tuple(RiskBand)
        band = (
            RiskBand.CRITICAL
            if factor.effect == "→ CRITICAL"
            else bands[min(bands.index(band) + 1, len(bands) - 1)]
        )

    try:
        name = action.action_class
        profile = CLASSES[name]
        base = band = RiskBand[profile["band"]]
        # Revalidate model instances too: model_copy/model_construct bypass validation.
        facts = RiskFacts.model_validate(
            facts.model_dump(warnings=False) if isinstance(facts, RiskFacts) else facts
        )
        if action.requested_by.role == "unknown":
            add(
                RiskFactor(
                    factor="unknown_requester",
                    effect="+1 band",
                    evidence="Resolved requester role is unknown.",
                )
            )

        asleep = False
        if name == "energy.hvac_adjust":
            asleep = required(facts.sleeping_in_target_zone, "sleeping_in_target_zone")
        elif name == "energy.appliance_start":
            asleep = required(facts.sleeping_any, "sleeping_any")
        elif name == "environment.lights" and required(
            facts.target_is_bedroom, "target_is_bedroom"
        ):
            asleep = required(facts.sleeping_in_target_zone, "sleeping_in_target_zone")
        if asleep:
            add(
                RiskFactor(
                    factor="occupant_asleep",
                    effect="+1 band",
                    evidence="An occupant is asleep in the affected area.",
                )
            )

        if name in {
            "security.door_unlock",
            "security.camera_disable",
            "security.access_code_share",
        } and required(facts.guest_present, "guest_present"):
            add(
                RiskFactor(
                    factor="guest_present",
                    effect="+1 band",
                    evidence="A guest is present in the household.",
                )
            )

        ages = required(facts.observation_ages_seconds, "observation_ages_seconds")
        threshold = profile["freshness_seconds"]
        stale = [
            f"Observation age {age}s exceeds {threshold}s."
            for age in ages
            if age > threshold
        ]
        if name == "security.door_unlock" and not required(
            facts.doorbell_online, "doorbell_online"
        ):
            stale.append("The doorbell is offline.")
        if stale:
            add(
                RiskFactor(
                    factor="state_stale",
                    effect="+1 band",
                    evidence=" ".join(sorted(set(stale))),
                )
            )

        if name == "energy.hvac_adjust":
            target = number(
                required(action.params.get("target_f"), "action.params.target_f")
            )
            baseline = required(facts.baseline_target_f, "baseline_target_f")
            deviation = abs(target - baseline)
            if deviation > 6:
                add(
                    RiskFactor(
                        factor="deviation_from_baseline",
                        effect="+1 band",
                        evidence=f"Requested temperature differs from requester's preference by {deviation}°F (>6°F).",
                    )
                )

        if name in {
            "finance.transfer_money",
            "finance.change_payee",
            "security.access_code_share",
            "finance.verify_request",
        } and required(facts.scam_pattern, "scam_pattern"):
            add(
                RiskFactor(
                    factor="scam_pattern",
                    effect="→ CRITICAL",
                    evidence="Trusted code reports a scam pattern.",
                )
            )

        violations = []
        for path, op, bound in guards(rule):
            value = number(
                required(action.params.get(path.removeprefix("action.params.")), path)
            )
            if (op == ">=" and value < bound) or (op == "<=" and value > bound):
                violations.append(f"{path} violates {op} {bound}.")
        if violations:
            add(
                RiskFactor(
                    factor="outside_bounds",
                    effect="+1 band",
                    evidence=" ".join(violations),
                )
            )
    except Exception as exc:
        evidence = "Risk calculation failed."
        if isinstance(exc, FactError):
            evidence = "Missing required fact: " + ", ".join(exc.paths) + "."
        elif isinstance(exc, ValidationError):
            evidence = "Invalid risk facts."
        add(RiskFactor(factor="scoring_error", effect="→ CRITICAL", evidence=evidence))
    return RiskAssessment(band=band, base_band=base, factors=tuple(factors))
