"""Local diagnostics and key setup without services or household actions."""

import asyncio
import secrets
import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from hirz import cli, db, local
from scripts import init_dev as dev


def pem(key=None, encryption=None):
    key = key or ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        encryption or serialization.NoEncryption(),
    ).decode()


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.touch(mode=0o600)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dev, "ENV_FILE", path)
    return path


def test_env_permissions_symlinks_and_no_interpolation(env_file, monkeypatch):
    env_file.write_text("LITERAL='${SHELL_VALUE}'\n")
    monkeypatch.setenv("SHELL_VALUE", secrets.token_urlsafe())
    assert local.read_env(env_file) == {"LITERAL": "${SHELL_VALUE}"}
    env_file.chmod(0o644)
    with pytest.raises(local.LocalError, match="0600"):
        local.read_env(env_file)
    env_file.unlink()
    assert local.read_env(env_file) == {}
    env_file.symlink_to(env_file.parent / "missing")
    with pytest.raises(local.LocalError, match="symlink"):
        local.read_env(env_file)
    env_file.unlink()
    env_file.mkdir()
    with pytest.raises(local.LocalError, match="regular file"):
        local.read_env(env_file)


def test_key_validation_rejects_invalid_material():
    secret = secrets.token_urlsafe()
    invalid = [
        secret,
        pem(ec.generate_private_key(ec.SECP384R1())),
        pem(rsa.generate_private_key(public_exponent=65537, key_size=2048)),
        pem(encryption=serialization.BestAvailableEncryption(secret.encode())),
        ec.generate_private_key(ec.SECP256R1())
        .public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode(),
    ]
    with pytest.raises(local.LocalError, match="missing"):
        local.signing_key({})
    for value in invalid:
        with pytest.raises(local.LocalError, match="P-256") as error:
            local.signing_key({"AUDIT_SIGNING_KEY": value})
        assert secret not in str(error.value)
        assert value not in str(error.value)
    assert isinstance(
        local.signing_key({"AUDIT_SIGNING_KEY": pem()}).curve, ec.SECP256R1
    )


def fake_database(monkeypatch, target, error=None):
    connection = AsyncMock()
    connection.scalar.return_value = 1
    connection.run_sync.side_effect = error

    @asynccontextmanager
    async def connect(values):
        yield connection

    monkeypatch.setattr(target, "connect_database", connect)
    return connection


def test_key_creation_roundtrip_and_preservation(env_file, monkeypatch, capsys):
    env_file.write_text("UNRELATED='keep ${LITERAL}'\n")
    connection = fake_database(monkeypatch, dev)
    asyncio.run(dev.prepare_signing_key())
    connection.run_sync.assert_awaited_once_with(db.require_empty_audit)
    before = env_file.read_bytes()
    values = local.read_env(env_file)
    assert values["UNRELATED"] == "keep ${LITERAL}"
    assert values["AUDIT_SIGNING_KEY"].startswith("-----BEGIN PRIVATE KEY-----\n")
    assert env_file.stat().st_mode & 0o777 == 0o600
    local.signing_key(values)
    asyncio.run(dev.prepare_signing_key())
    assert env_file.read_bytes() == before
    connection.run_sync.assert_awaited_once()
    assert values["AUDIT_SIGNING_KEY"] not in capsys.readouterr().out


@pytest.mark.parametrize("known", [True, False])
def test_key_setup_fails_closed_without_changing_file(env_file, monkeypatch, known):
    secret = secrets.token_urlsafe()
    error = (
        local.LocalError("Audit rows exist; restore the original key.")
        if known
        else RuntimeError(secret)
    )
    fake_database(monkeypatch, dev, error)
    before = env_file.read_bytes()
    with pytest.raises(local.LocalError) as caught:
        asyncio.run(dev.prepare_signing_key())
    assert secret not in str(caught.value)
    assert env_file.read_bytes() == before


def test_invalid_existing_key_is_never_replaced(env_file, monkeypatch):
    env_file.write_text("AUDIT_SIGNING_KEY='invalid'\n")
    connection = fake_database(monkeypatch, dev)
    before = env_file.read_bytes()
    with pytest.raises(local.LocalError, match="restore the original"):
        asyncio.run(dev.prepare_signing_key())
    assert env_file.read_bytes() == before
    connection.run_sync.assert_not_awaited()


def test_database_url_escapes_password_and_ignores_shell(monkeypatch):
    secret = secrets.token_urlsafe() + "@:/%"
    monkeypatch.setenv("POSTGRES_PASSWORD", secrets.token_urlsafe())
    url = db.database_url({"POSTGRES_PASSWORD": secret})
    assert url.password == secret
    assert secret not in str(url)
    assert (url.host, url.port, url.database, url.username) == (
        "127.0.0.1",
        5432,
        "hirz",
        "hirz",
    )
    with pytest.raises(local.LocalError, match="missing"):
        db.database_url({})


@pytest.mark.parametrize(
    "status,body,valid",
    [
        (200, [{"entity_id": entity} for entity in local.DEMO_ENTITIES], True),
        (401, {}, False),
        (503, {}, False),
        (200, [], False),
        (200, {}, False),
        (200, [{"entity_id": 42}], False),
    ],
)
def test_ha_single_authenticated_read(monkeypatch, status, body, valid):
    token = secrets.token_urlsafe()
    requests = []
    client_type = httpx.AsyncClient

    def respond(request):
        requests.append(request)
        assert request.method == "GET"
        assert str(request.url) == local.HA_URL + "/api/states"
        assert request.headers["Authorization"] == f"Bearer {token}"
        return httpx.Response(status, json=body)

    monkeypatch.setattr(
        cli.httpx,
        "AsyncClient",
        lambda **kwargs: client_type(transport=httpx.MockTransport(respond), **kwargs),
    )
    if valid:
        assert "simulated" in asyncio.run(cli.check_ha({"HA_TOKEN": token}))
    else:
        with pytest.raises(local.LocalError):
            asyncio.run(cli.check_ha({"HA_TOKEN": token}))
    assert len(requests) == 1


def test_doctor_all_pass_and_cli_exit(env_file, monkeypatch, capsys):
    from dotenv import set_key

    set_key(env_file, "AUDIT_SIGNING_KEY", pem())
    fake_database(monkeypatch, cli)
    monkeypatch.setattr(cli, "check_ha", AsyncMock(return_value="simulated"))
    monkeypatch.setattr(sys, "argv", ["hirz", "doctor"])
    assert cli.main() == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4
    assert all(line.startswith("PASS ") for line in lines)
    assert [line.split(":")[0] for line in lines] == [
        "PASS Postgres",
        "PASS HA",
        "PASS Signing key",
        "PASS Migrations",
    ]


def test_doctor_missing_env_runs_all_checks(env_file, capsys):
    env_file.unlink()
    assert asyncio.run(cli.doctor()) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4 and all(line.startswith("FAIL ") for line in lines)


def test_doctor_timeout_and_upstream_errors_are_safe(env_file, monkeypatch, capsys):
    secret = secrets.token_urlsafe()
    monkeypatch.setattr(cli, "REQUEST_TIMEOUT", 0.01)

    async def stall(values):
        await asyncio.sleep(1)

    monkeypatch.setattr(cli, "check_postgres", stall)
    monkeypatch.setattr(cli, "check_ha", AsyncMock(side_effect=ValueError(secret)))
    monkeypatch.setattr(
        cli, "check_migrations", AsyncMock(side_effect=RuntimeError(secret))
    )
    assert asyncio.run(cli.doctor()) == 1
    output = capsys.readouterr().out
    assert secret not in output
    assert len(output.splitlines()) == 4
    assert "timed out" in output


def test_postgres_rejects_unexpected_result(monkeypatch):
    connection = fake_database(monkeypatch, cli)
    connection.scalar.return_value = None
    with pytest.raises(local.LocalError, match="unexpected"):
        asyncio.run(cli.check_postgres({}))
