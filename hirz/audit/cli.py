"""Local audit commands; offline verification never reads local configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import UUID

from hirz.audit import (
    LIMITATION,
    AuditError,
    export_document,
    public_key,
    verify_database,
    verify_file,
    write_export,
)
from hirz.db import connect_database
from hirz.local import LocalError, read_env, signing_key


def sequence_range(value: str) -> tuple[int, int]:
    try:
        start, end = value.split(":")
        if (
            not start.isascii()
            or not end.isascii()
            or not start.isdecimal()
            or not end.isdecimal()
        ):
            raise ValueError
        first, last = int(start), int(end)
        if not 1 <= first <= last:
            raise ValueError
        return first, last
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Use an inclusive positive START:END range"
        ) from None


def add_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    verify = commands.add_parser(
        "verify-audit", help="Verify a household ledger or export"
    )
    verify.add_argument("--household", required=True, type=UUID)
    verify.add_argument("--file", type=Path)
    trust = verify.add_mutually_exclusive_group()
    trust.add_argument("--public-key", type=Path)
    trust.add_argument("--trusted-fingerprint")
    audit = commands.add_parser("audit", help="Export signed household evidence")
    operations = audit.add_subparsers(dest="operation", required=True)
    export = operations.add_parser("export")
    export.add_argument("--household", required=True, type=UUID)
    export.add_argument("--public-key", type=Path)
    export.add_argument("--range", type=sequence_range)
    export.add_argument("--output", required=True, type=Path)


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.command != "verify-audit":
        return
    if args.file and not (args.public_key or args.trusted_fingerprint):
        parser.error("--file requires --public-key or --trusted-fingerprint")
    if not args.file and args.trusted_fingerprint is not None:
        parser.error("--trusted-fingerprint requires --file")
    if args.trusted_fingerprint is not None and (
        len(args.trusted_fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in args.trusted_fingerprint)
    ):
        parser.error(
            "--trusted-fingerprint must be 64 lowercase hexadecimal characters"
        )


async def audit_command(args: argparse.Namespace) -> int:
    result = dict(
        status="invalid",
        household_id=str(args.household),
        start_seq=None,
        end_seq=None,
        checked_count=0,
        key_fingerprint=None,
        failure_seq=None,
        reason=None,
        anchoring=LIMITATION,
    )
    try:
        key = (
            public_key(args.public_key.read_text(encoding="ascii"))
            if args.public_key
            else None
        )
        if args.command == "verify-audit" and args.file is not None:
            result = verify_file(
                args.file,
                args.household,
                key=key,
                trusted_fingerprint=args.trusted_fingerprint,
            )
        else:
            values = read_env(Path(".env"))
            key = key or signing_key(values).public_key()
            exporting = args.command == "audit"
            async with connect_database(values) as connection:
                result, rows = await verify_database(
                    connection,
                    args.household,
                    key,
                    collect=exporting,
                    selected=args.range if exporting else None,
                )
            if exporting:
                write_export(args.output, export_document(args.household, key, rows))
                result.update(
                    exported_count=len(rows),
                    export_start_seq=rows[0].seq if rows else None,
                    export_end_seq=rows[-1].seq if rows else None,
                )
    except (AuditError, LocalError) as exc:
        if isinstance(exc, AuditError):
            result.update(exc.result)
        result.update(status="invalid", reason=str(exc))
    except Exception:
        result.update(
            status="invalid",
            reason=(
                "Audit operation failed; check input files, destination, PostgreSQL and migrations. "
                "Private values and upstream details withheld."
            ),
        )
    print(json.dumps(result))
    return int(result["status"] == "invalid")
