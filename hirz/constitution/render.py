"""Deterministic English and lossless YAML, not natural-language parsing."""

import json
from typing import Any

from hirz.constitution.conditions import Node, parse
from hirz.constitution.schema import Constitution
from hirz.risk import CLASSES

MODES = {
    "auto": "may act on its own",
    "ask": "must ask for approval",
    "never": "must never act",
}


def phrase(value: Any) -> str:
    if isinstance(value, (tuple, list)):
        return ", ".join(phrase(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{phrase(k)}: {phrase(v)}" for k, v in sorted(value.items()))
    if not isinstance(value, str):
        return str(value)
    return value.replace("_", " ").replace(".", " ")


def condition(node: Node) -> str:
    if node.kind == "attr":
        return phrase(node.value)
    if node.kind == "literal":
        return (
            json.dumps(node.value)
            if isinstance(node.value, str)
            else str(node.value).lower()
        )
    args = [condition(c) for c in node.children]
    if node.kind == "call":
        return {
            "occupancy.present": f"member {args[0]} is present",
            "occupancy.sleeping_in": f"someone is sleeping in zone {args[0]}",
            "schedule.expected_within": f"member {args[0]} is expected within {args[-1]} minutes",
        }[node.value]
    if node.kind == "not":
        return f"it is not the case that ({args[0]})"
    if node.kind in ("set", "unset"):
        return f"{args[0]} is {'explicitly null' if node.kind == 'unset' else 'set'}"
    if node.kind in ("and", "or"):
        return f"({args[0]}) {node.kind} ({args[1]})"
    if node.kind == "in":
        return f"{args[0]} is one of {', '.join(args[1:])}"
    op = {
        "==": "equals",
        "!=": "does not equal",
        "<": "is less than",
        "<=": "is at most",
        ">": "is greater than",
        ">=": "is at least",
    }[node.kind]
    return f"{args[0]} {op} {args[1]}"


def render(policy: Constitution) -> list[str]:
    lines = [
        f"Household {policy.household}, constitution version {policy.version}.",
        "Unlisted actions ask for adult-derived roles and are never allowed for other roles.",
        f"Default approval expires after {policy.defaults.approval_ttl_minutes} minutes; channels: {phrase(policy.defaults.ask_channels)}.",
    ]
    for role, definition in sorted(policy.roles.items()):
        lines.append(
            f"Role {role}: "
            + (f"inherits {definition.inherits}; " if definition.inherits else "")
            + (
                f"limited to {phrase(definition.limited_to)}."
                if definition.limited_to is not None
                else "no domain restriction."
            )
        )
    for name in sorted(CLASSES):
        domain, key = name.split(".")
        if key not in policy.autonomy.get(domain, {}):
            continue
        rule = policy.autonomy[domain][key]
        lines.append(f"For {phrase(name)}, Hirz {MODES[rule.mode]}.")
        for text in rule.conditions:
            lines.append(
                f"Autonomy requires {condition(parse(text))}; a known-false condition requires approval and unresolved facts prevent authorization."
            )
        for index, override in enumerate(rule.overrides, 1):
            lines.append(
                f"Override {index} (first match wins): when {condition(parse(override.when))}, Hirz {MODES[override.mode]}."
            )
        lines.append(
            f"Approval: {phrase(rule.quorum)}; {phrase(rule.ask_channels or policy.defaults.ask_channels)}; expires after {rule.approval_ttl_minutes or policy.defaults.approval_ttl_minutes} minutes."
        )
        lines.append(
            f"Requesters: {phrase(rule.allowed_requesters) if rule.allowed_requesters is not None else 'roles whose effective rule is not never'}."
        )
        if rule.bounds:
            lines.append(
                f"Hard bounds, including after approval: {phrase(rule.bounds.model_dump(exclude_none=True))}."
            )
        if rule.budget:
            lines.append(
                f"Daily spending cap: {rule.budget.usd_per_day} USD; crossing it is DENY_BUDGET (runtime enforcement pending item 9)."
            )
        if rule.never_for:
            lines.append(f"Never for: {phrase(rule.never_for)}.")
        if rule.max_open_minutes is not None:
            lines.append(
                f"Hard maximum open duration: {rule.max_open_minutes} minutes."
            )
        if rule.max_minutes is not None:
            lines.append(f"Hard maximum duration: {rule.max_minutes} minutes.")
    for role, entries in sorted(policy.per_role.items()):
        for name, entry in sorted(entries.items()):
            lines.append(
                f"For {role}, {phrase(name) if name != '*' else 'otherwise-unlisted role actions'}: Hirz {MODES[entry.mode]}; inherited restrictions still apply."
            )
    for interval in policy.quiet_hours:
        lines.append(
            f"Quiet hours start on {phrase(interval.days)} at {interval.from_time}, end at {interval.to_time} in household local time, include the start and exclude the end, and carry overnight. {phrase(interval.affects)} escalate from auto to ask (runtime enforcement pending item 9)."
        )
    lines.extend(
        [
            f"Requester confirmation required for: {phrase(policy.verification.require_requester_confirmation) or 'none'} (later pipeline enforcement).",
            f"Trusted contact methods, in order: {phrase(policy.verification.trusted_contact_methods_order) or 'none'}.",
            f"Memory proposals: {policy.learning.accept_memory_proposals} (later learning enforcement).",
        ]
    )
    return lines
