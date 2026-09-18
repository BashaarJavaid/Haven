"""Fixed, labeled synthetic situations evaluated against both versions."""

from datetime import UTC, datetime
from importlib.resources import files
from typing import Any

import yaml

from hirz.constitution.conditions import PolicyFacts
from hirz.constitution.evaluator import RuleOutcome, resolve
from hirz.constitution.schema import Constitution
from hirz.pipeline.models import ROLES, Action, Role

SITUATIONS: dict[str, Any] = yaml.safe_load(
    files(__package__).joinpath("situations.yaml").read_text()
)


def situation(
    policy: Constitution,
    name: str,
    role: Role = "owner",
    case: dict[str, Any] | None = None,
) -> tuple[Action, PolicyFacts]:
    case = case or {}
    values: dict[str, Any] = {
        "context": {
            "hour": 17,
            "time": "17:35",
            "weekday": "tue",
            "unexpected_visitor": False,
            "is_quiet_hours": False,
        },
        "occupancy": {"members": [], "present_members": [], "sleeping_any": False},
        "schedule": {"arrivals": []},
        "asset": {"policy": {"needed_by": "2026-10-14T08:00:00-05:00"}},
    }
    values.update(case.get("values", {}))
    action = Action.model_validate(
        {
            "action_id": "simulated-preview",
            "class": name,
            "target": {
                "adapter": "twin",
                "entity": "simulated-preview",
                "zone": "living_room",
            },
            "params": case.get("params", SITUATIONS[name]["params"]),
            "requested_by": {"member_id": "resident", "role": role, "surface": "app"},
            "reason": "Simulated constitution preview",
            "content_hash": "sha256:simulated-preview",
        }
    )
    facts = PolicyFacts(
        policy.household,
        datetime(2026, 10, 13, 22, 35, tzinfo=UTC),
        values,
        ("resident",),
        ("living_room", "guest_room"),
    )
    return action, facts


def wording(outcome: RuleOutcome) -> str:
    if outcome.effective_mode == "ask" and outcome.approval.channels == ("app_push",):
        return "ask on phone"
    return outcome.effective_mode


def preview(old: Constitution, new: Constitution) -> dict[str, Any]:
    if old.household != new.household:
        raise ValueError("Preview requires the same household")
    rows: list[dict[str, Any]] = []
    lines: list[str] = []
    touched: set[str] = set()
    for name, spec in SITUATIONS.items():
        cases = [
            (
                r,
                {
                    "label": spec.get("owner_label", f"{name}: owner")
                    if r == "owner"
                    else f"{name}: {r}"
                },
            )
            for r in ROLES
        ]
        cases.extend(("owner", case) for case in spec.get("cases", []))
        for role, case in cases:
            action, facts = situation(old, name, role, case)
            before, after = resolve(old, action, facts), resolve(new, action, facts)
            changed = before.model_dump(
                exclude={"constitution_version"}
            ) != after.model_dump(exclude={"constitution_version"})
            if changed:
                touched.add(name)
            rows.append(
                {
                    "class": name,
                    "label": case["label"],
                    "role": role,
                    "changed": changed,
                    "before": before.model_dump(mode="json"),
                    "after": after.model_dump(mode="json"),
                }
            )
            if (
                changed
                and wording(before) != wording(after)
                and not any(d.code == "POLICY_ERROR" for d in after.diagnostics)
            ):
                lines.append(f"{case['label']}: {wording(before)} → {wording(after)}")
    rows = [r for r in rows if r["changed"] or r["class"] in touched]
    for name in sorted(touched):
        for row in rows:
            if (
                row["class"] == name
                and row["label"] == "Expected arrival"
                and not row["changed"]
            ):
                outcome = RuleOutcome.model_validate(row["after"])
                if wording(outcome) == "ask on phone":
                    lines.append("Expected arrival: still asks on your phone")
        if "caveat" in SITUATIONS[name]:
            lines.append(SITUATIONS[name]["caveat"])
    configuration = []
    for key in ("quiet_hours", "verification", "learning"):
        before = old.model_dump(mode="json", by_alias=True)[key]
        after = new.model_dump(mode="json", by_alias=True)[key]
        if before != after:
            configuration.append(
                {
                    "field": key,
                    "before": before,
                    "after": after,
                    "status": "awaiting later-stage enforcement",
                }
            )
    return {
        "source": "twin",
        "lines": lines,
        "situations": rows,
        "configuration_changes": configuration,
        "deferred_enforcement": [
            "budgets",
            "quiet_hours",
            "risk",
            "approval authentication",
            "audit",
            "device actions",
        ],
    }
