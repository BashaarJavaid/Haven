"""Fail-closed local Dogwood subprocess adapter; no automatic engine fallback."""

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hirz.constitution.compiler import APPROVE, Compiled, action_name, literal
from hirz.local import REQUEST_TIMEOUT


class BoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class Event:
    timestamp: int  # Dogwood trace time is seconds, not milliseconds.
    action_class: str
    inputs: dict[str, Any]
    resource: str = "hirz-local"
    principal: str = "worker"
    approved: bool = True
    output_ttl: int | None = None

    def line(self, kind: str = "request") -> str:
        action = (
            APPROVE
            if self.action_class == "governance.approve_action"
            else action_name(self.action_class)
        )
        principal = f"AgentCore::Worker::{literal(self.principal)}"
        resource = f"AgentCore::Gateway::{literal(self.resource)}"
        inputs = literal(self.inputs, trace=True)
        output = ""
        if kind == "response":
            output = f", output: {{approved: {literal(self.approved)}, ttl_minutes: {self.output_ttl if self.output_ttl is not None else self.inputs['ttl_minutes']}}}"
        return f"@{self.timestamp} scope(principal: {principal}, resource: {resource}) request_context(input: {inputs}) {action}::{kind}(input: {inputs}{output}, callerPrincipal: {principal}, callerResource: {resource}, requestId: {literal(str(self.timestamp))})"


@dataclass(frozen=True)
class BoundaryResult:
    allowed: bool
    engine: str = "dogwood-local"
    diagnostic: str | None = None


class Dogwood:
    def __init__(self, executable: str | None = None, timeout: float = REQUEST_TIMEOUT):
        self.executable = executable or os.environ.get("HIRZ_DOGWOOD", "dogwood")
        self.timeout = timeout

    async def run(
        self, compiled: Compiled, command: str, trace: str | None = None
    ) -> dict[str, Any]:
        with TemporaryDirectory(prefix="hirz-policy-") as directory:
            root = Path(directory)
            policy, schema = root / "policy.dw", root / "schema.cedarschema"
            policy.write_text(compiled.policy)
            schema.write_text(compiled.schema)
            args = [
                self.executable,
                command,
                str(policy),
                "--format",
                "json",
            ]
            if command != "check-parse":
                args.extend(["--policy-schema", str(schema)])
            if trace is not None:
                trace_path = root / "trace.log"
                trace_path.write_text(trace)
                args.extend(["--trace", str(trace_path)])
            process = None
            try:
                async with asyncio.timeout(self.timeout):
                    process = await asyncio.create_subprocess_exec(
                        *args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _stderr = await process.communicate()
                if process.returncode != 0:
                    raise BoundaryError(
                        "Dogwood rejected input or crashed; no authorization"
                    )
                result = json.loads(stdout)
                if not isinstance(result, dict):
                    raise ValueError()
                return result
            except (OSError, TimeoutError, ValueError) as exc:
                if process is not None and process.returncode is None:
                    process.kill()
                    await process.wait()
                if isinstance(exc, BoundaryError):
                    raise
                raise BoundaryError(
                    "Dogwood unavailable, timed out, or returned invalid output; no authorization"
                ) from None
            except asyncio.CancelledError:
                if process is not None and process.returncode is None:
                    process.kill()
                    await process.wait()
                raise

    async def validate(self, compiled: Compiled) -> dict[str, Any]:
        result = await self.run(compiled, "validate")
        if (
            result.get("passed") is not True
            or result.get("errors") != []
            or not isinstance(result.get("warnings"), list)
        ):
            raise BoundaryError(
                "Dogwood validation failed or returned malformed findings"
            )
        return result

    async def replay(self, compiled: Compiled, trace: str) -> list[dict[str, Any]]:
        result = await self.run(compiled, "replay", trace)
        verdicts = result.get("verdicts")
        if not isinstance(verdicts, list) or not verdicts:
            raise BoundaryError("Dogwood returned no verdicts")
        for index, verdict in enumerate(verdicts):
            if (
                not isinstance(verdict, dict)
                or verdict.get("index") != index
                or type(verdict.get("timestamp")) is not int
                or verdict.get("verdict") not in ("allow", "deny")
                or verdict.get("errors") != []
                or not isinstance(verdict.get("determining_rules"), list)
            ):
                raise BoundaryError("Dogwood evaluation errors or malformed verdicts")
        return verdicts

    async def authorize(
        self, compiled: Compiled, action: Event, approvals: tuple[Event, ...] = ()
    ) -> BoundaryResult:
        trace: list[str] = []
        previous = -1
        try:
            # ponytail: replay prefixes for the small local history; use Rust bindings
            # if measured session size makes repeated subprocess replay too expensive.
            for approval in approvals:
                if (
                    approval.action_class != "governance.approve_action"
                    or not previous <= approval.timestamp <= action.timestamp
                ):
                    raise BoundaryError("Invalid approval history order")
                previous = approval.timestamp
                trace.append(approval.line())
                verdicts = await self.replay(compiled, "\n".join(trace))
                if verdicts[-1]["verdict"] == "allow":
                    trace.append(approval.line("response"))
                # A denied approval never becomes a response event.
            trace.append(action.line())
            verdicts = await self.replay(compiled, "\n".join(trace))
            if (
                len(verdicts) != len(approvals) + 1
                or verdicts[-1]["timestamp"] != action.timestamp
            ):
                raise BoundaryError("Dogwood returned incomplete verdicts")
            return BoundaryResult(verdicts[-1]["verdict"] == "allow")
        except BoundaryError:
            return BoundaryResult(False, diagnostic="DENY_BOUNDARY")
