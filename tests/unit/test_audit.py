"""Independent signed vectors, hostile exports, and offline command contracts."""

import json
import os
import sys
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, utils

from hirz import cli
from hirz.audit import (
    AuditError,
    Verification,
    decode_event,
    event_json,
    export_document,
    fingerprint,
    public_key,
    public_pem,
    verify_file,
    write_export,
)
from hirz.pipeline.hashing import digest, timestamp
from hirz.pipeline.models import AuditEvent
from tests.unit.test_pipeline import AT, HOME


@pytest.fixture
def signed():
    key = ec.generate_private_key(ec.SECP256R1())
    rows = []
    previous = "0" * 64
    for seq in range(1, 4):
        envelope = dict(
            household_id=str(HOME),
            seq=seq,
            event_type="FUTURE_EVENT",
            payload={
                "nested": [1, 1.5, True, None, {"amount": "0.10", "name": "Mamá"}]
            },
            prev_hash=previous,
            key_fingerprint=fingerprint(key.public_key()),
            created_at=timestamp(AT + timedelta(seconds=seq)),
        )
        current = digest(envelope)
        rows.append(
            AuditEvent.model_validate(
                envelope
                | dict(
                    household_id=HOME,
                    created_at=AT + timedelta(seconds=seq),
                    curr_hash=current,
                    signature=key.sign(
                        bytes.fromhex(current),
                        ec.ECDSA(utils.Prehashed(hashes.SHA256())),
                    ),
                )
            )
        )
        previous = current
    return key, rows


def check_file(tmp_path, key, document):
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(document))
    return verify_file(path, HOME, key=key.public_key())


def test_roundtrip_full_partial_empty_and_independent_trust(tmp_path, signed):
    key, rows = signed
    for selection in (rows, rows[1:], []):
        doc = export_document(HOME, key.public_key(), selection)
        result = check_file(tmp_path, key, doc)
        assert result["checked_count"] == len(selection)
        assert result["status"] == ("valid" if selection else "empty")
        assert "completeness" in result["anchoring"]
        assert (
            verify_file(
                tmp_path / "audit.json",
                HOME,
                trusted_fingerprint=fingerprint(key.public_key()),
            )
            == result
        )
    assert decode_event(event_json(rows[0]))["payload"] == rows[0].payload
    with pytest.raises(AuditError, match="exactly one"):
        verify_file(tmp_path / "audit.json", HOME)
    with pytest.raises(AuditError, match="exactly one"):
        verify_file(
            tmp_path / "audit.json",
            HOME,
            key=key.public_key(),
            trusted_fingerprint="a" * 64,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("payload", {"changed": True}),
        ("event_type", "ALTERED"),
        ("household_id", str(uuid4())),
        ("seq", 2),
        ("seq", True),
        ("prev_hash", "1" * 64),
        ("curr_hash", "f" * 64),
        ("key_fingerprint", "f" * 64),
        ("signature", "AA=="),
        ("signature", "!bad"),
        ("created_at", "2026-09-18T17:00:00"),
        ("created_at", "2026-09-18T18:00:00.000000Z"),
        ("payload", []),
        ("seq", "1"),
        ("event_type", ""),
    ],
)
def test_modified_or_malformed_rows_fail(tmp_path, signed, field, value):
    key, rows = signed
    doc = export_document(HOME, key.public_key(), rows)
    doc["rows"][0][field] = value
    with pytest.raises(AuditError):
        check_file(tmp_path, key, doc)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "reorder",
        "metadata",
        "wrapper_home",
        "version",
        "bool_version",
        "extra",
        "bad_key",
        "backwards",
        "rehash",
        "bad_genesis",
        "float_seq",
        "nonfinite",
        "unknown_row_field",
    ],
)
def test_export_adversaries(tmp_path, signed, mutation):
    key, rows = signed
    doc = export_document(HOME, key.public_key(), rows)
    if mutation == "missing":
        del doc["rows"][1]
    elif mutation == "duplicate":
        doc["rows"].insert(1, deepcopy(doc["rows"][0]))
    elif mutation == "reorder":
        doc["rows"].reverse()
    elif mutation == "metadata":
        doc["end_seq"] = 4
    elif mutation == "wrapper_home":
        doc["household_id"] = str(uuid4())
    elif mutation in {"version", "bool_version"}:
        doc["format_version"] = True if mutation == "bool_version" else 2
    elif mutation == "extra":
        doc["unexpected"] = 1
    elif mutation == "bad_key":
        doc["public_key"] = public_pem(
            ec.generate_private_key(ec.SECP256R1()).public_key()
        )
    elif mutation == "backwards":
        doc["rows"][1]["created_at"] = timestamp(AT)
    elif mutation == "rehash":
        row = doc["rows"][0]
        row["payload"] = {"forged": True}
        row["curr_hash"] = digest(
            {k: v for k, v in row.items() if k not in {"curr_hash", "signature"}}
        )
    elif mutation == "bad_genesis":
        doc["rows"][0]["prev_hash"] = "a" * 64
    elif mutation == "float_seq":
        doc["rows"][0]["seq"] = 1.0
    elif mutation == "nonfinite":
        doc["rows"][0]["payload"] = {"v": float("inf")}
    else:
        doc["rows"][0]["unexpected"] = "ignored?"
    with pytest.raises(AuditError):
        check_file(tmp_path, key, doc)


def test_duplicate_keys_wrong_trust_and_failure_location(tmp_path, signed):
    key, rows = signed
    path = tmp_path / "audit.json"
    path.write_text('{"format_version":1,"format_version":1}')
    with pytest.raises(AuditError, match="Duplicate"):
        verify_file(path, HOME, key=key.public_key())
    path.write_text(json.dumps(export_document(HOME, key.public_key(), rows)))
    with pytest.raises(AuditError, match="Untrusted"):
        verify_file(path, HOME, trusted_fingerprint="a" * 64)
    check = Verification(HOME, key.public_key())
    check.feed(rows[0].model_dump())
    with pytest.raises(AuditError) as error:
        check.feed(rows[1].model_dump() | {"payload": {"tampered": True}})
    assert error.value.result["checked_count"] == 1
    assert error.value.result["failure_seq"] == 2
    assert "tampered" not in str(error.value)
    with pytest.raises(AuditError, match="canonical"):
        Verification(HOME, key.public_key()).feed(
            rows[0].model_dump() | {"payload": {"n": 2**60}}
        )


def test_public_keys_reject_private_wrong_curve_and_rsa(signed):
    key, _ = signed
    private = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    for value in (
        private,
        "invalid",
        "é",
        public_pem(ec.generate_private_key(ec.SECP384R1()).public_key()),
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        .public_key()
        .public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        .decode(),
    ):
        with pytest.raises(AuditError):
            public_key(value)


def test_exclusive_private_output_and_write_failure(tmp_path, signed, monkeypatch):
    key, rows = signed
    doc = export_document(HOME, key.public_key(), rows)
    path = tmp_path / "audit.json"
    write_export(path, doc)
    assert path.stat().st_mode & 0o777 == 0o600
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_export(path, doc)
    assert path.read_bytes() == original
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(FileExistsError):
        write_export(link, doc)
    missing = tmp_path / "incomplete.json"
    original_fdopen = os.fdopen

    class BrokenOutput:
        def __init__(self, fd, *args, **kwargs):
            self.file = original_fdopen(fd, *args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.file.close()

        def write(self, value):
            self.file.write(value[:5])
            raise OSError("injected private upstream detail")

    monkeypatch.setattr(os, "fdopen", BrokenOutput)
    with pytest.raises(OSError):
        write_export(missing, doc)
    assert not missing.exists()


def test_offline_cli_has_no_configuration_dependency(
    tmp_path, signed, monkeypatch, capsys
):
    key, rows = signed
    doc = export_document(HOME, key.public_key(), rows)
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(doc))
    monkeypatch.chdir(tmp_path)

    def no_configuration(*args, **kwargs):
        raise AssertionError(
            "Offline verification must not access configuration or PostgreSQL"
        )

    monkeypatch.setattr("hirz.audit.cli.read_env", no_configuration)
    monkeypatch.setattr("hirz.audit.cli.connect_database", no_configuration)
    args = [
        "hirz",
        "verify-audit",
        "--file",
        str(path),
        "--household",
        str(HOME),
        "--trusted-fingerprint",
        fingerprint(key.public_key()),
    ]
    monkeypatch.setattr(sys, "argv", args)
    assert cli.main() == 0
    assert json.loads(capsys.readouterr().out)["checked_count"] == 3
    doc["rows"][1]["payload"] = {"private": "do not print"}
    path.write_text(json.dumps(doc))
    assert cli.main() == 1
    output = capsys.readouterr().out
    assert "do not print" not in output
    assert json.loads(output)["failure_seq"] == 2
    path.unlink()
    assert cli.main() == 1
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"


@pytest.mark.parametrize(
    "args",
    [
        ["verify-audit"],
        ["verify-audit", "--file", "a"],
        ["verify-audit", "--trusted-fingerprint", "a" * 64],
        ["verify-audit", "--file", "a", "--trusted-fingerprint", "xyz"],
        ["verify-audit", "--anchors"],
        *[
            ["audit", "export", "--output", "a", "--range", r]
            for r in ("0:1", "2:1", "1", "1:x", "-1:1")
        ],
    ],
)
def test_cli_usage_errors(args, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["hirz", *args, "--household", str(HOME)]
        if args != ["verify-audit"]
        else ["hirz", *args],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
