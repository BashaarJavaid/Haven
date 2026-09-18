"""Phase 0 schema and local async connections; no repositories or audit writer."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from hirz.local import LocalError

metadata = sa.MetaData()
households = sa.Table(
    "households",
    metadata,
    sa.Column("id", sa.UUID, primary_key=True),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("timezone", sa.Text, nullable=False),
    sa.Column("locale", sa.Text, nullable=False),
    sa.CheckConstraint("length(name) > 0", name="households_name_nonempty"),
    sa.CheckConstraint("length(timezone) > 0", name="households_timezone_nonempty"),
    sa.CheckConstraint("length(locale) > 0", name="households_locale_nonempty"),
)
members = sa.Table(
    "members",
    metadata,
    sa.Column(
        "household_id", sa.UUID, sa.ForeignKey("households.id"), primary_key=True
    ),
    sa.Column("id", sa.UUID, primary_key=True),
    sa.Column("display_name", sa.Text, nullable=False),
    sa.Column("role", sa.Text, nullable=False),
    sa.CheckConstraint(
        "length(display_name) > 0", name="members_display_name_nonempty"
    ),
    sa.CheckConstraint(
        "role IN ('owner', 'adult', 'teen', 'child', 'guest', 'caregiver')",
        name="members_role_allowed",
    ),
)
member_accounts = sa.Table(
    "member_accounts",
    metadata,
    sa.Column("household_id", sa.UUID, primary_key=True),
    sa.Column("provider", sa.Text, primary_key=True),
    sa.Column("sub", sa.Text, primary_key=True),
    sa.Column("member_id", sa.UUID, nullable=False),
    sa.ForeignKeyConstraint(
        ["household_id", "member_id"], ["members.household_id", "members.id"]
    ),
    sa.CheckConstraint(
        "length(provider) > 0", name="member_accounts_provider_nonempty"
    ),
    sa.CheckConstraint("length(sub) > 0", name="member_accounts_sub_nonempty"),
)
audit_log = sa.Table(
    "audit_log",
    metadata,
    sa.Column(
        "household_id", sa.UUID, sa.ForeignKey("households.id"), primary_key=True
    ),
    sa.Column("seq", sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column("event_type", sa.Text, nullable=False),
    sa.Column("payload", JSONB, nullable=False),
    sa.Column("prev_hash", sa.Text, nullable=False),
    sa.Column("curr_hash", sa.Text, nullable=False),
    sa.Column("key_fingerprint", sa.Text, nullable=False),
    sa.Column("signature", sa.LargeBinary, nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    sa.CheckConstraint("seq > 0", name="audit_log_seq_positive"),
    sa.CheckConstraint("length(event_type) > 0", name="audit_log_event_type_nonempty"),
    sa.CheckConstraint(
        "jsonb_typeof(payload) = 'object'", name="audit_log_payload_object"
    ),
    sa.CheckConstraint(
        "octet_length(signature) > 0", name="audit_log_signature_nonempty"
    ),
    *(
        sa.CheckConstraint(
            f"{column} ~ '^[0-9a-f]{{64}}$'", name=f"audit_log_{column}_hex"
        )
        for column in ("prev_hash", "curr_hash", "key_fingerprint")
    ),
)
audit_pointer = sa.Table(
    "audit_pointer",
    metadata,
    sa.Column(
        "household_id", sa.UUID, sa.ForeignKey("households.id"), primary_key=True
    ),
    sa.Column("seq", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("curr_hash", sa.Text, nullable=False, server_default="0" * 64),
    sa.CheckConstraint("seq >= 0", name="audit_pointer_seq_nonnegative"),
    sa.CheckConstraint(
        "curr_hash ~ '^[0-9a-f]{64}$'", name="audit_pointer_curr_hash_hex"
    ),
)


def database_url(values: dict[str, str]) -> sa.URL:
    password = values.get("POSTGRES_PASSWORD")
    if not password:
        raise LocalError("POSTGRES_PASSWORD is missing; restore .env.")
    return sa.URL.create(
        "postgresql+psycopg",
        username="hirz",
        password=password,
        host="127.0.0.1",
        port=5432,
        database="hirz",
    )


@asynccontextmanager
async def connect_database(values: dict[str, str]) -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(
        database_url(values),
        poolclass=sa.pool.NullPool,
        connect_args={"connect_timeout": 10},
        hide_parameters=True,
    )
    try:
        async with engine.connect() as connection:
            yield connection
    finally:
        await engine.dispose()


def migration_config() -> Config:
    return Config("alembic.ini")


def require_current(connection: sa.Connection) -> None:
    heads = ScriptDirectory.from_config(migration_config()).get_heads()
    current = MigrationContext.configure(connection).get_current_heads()
    tables = set(sa.inspect(connection).get_table_names())
    if (
        len(heads) != 1
        or set(current) != set(heads)
        or not metadata.tables.keys() <= tables
    ):
        raise LocalError(
            "Migrations are missing, inconsistent, or behind; "
            "run uv run alembic upgrade head from the checkout root."
        )


def require_empty_audit(connection: sa.Connection) -> None:
    tables = set(sa.inspect(connection).get_table_names())
    if not tables:
        return
    require_current(connection)
    context = MigrationContext.configure(
        connection, opts={"compare_server_default": True}
    )
    if compare_metadata(context, metadata):
        raise LocalError(
            "Schema is inconsistent; restore the database before key setup."
        )
    if connection.scalar(sa.select(sa.exists().select_from(audit_log))):
        raise LocalError("Audit rows exist; restore the original AUDIT_SIGNING_KEY.")
