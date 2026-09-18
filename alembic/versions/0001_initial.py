"""Initial household identity and per-household audit schema.

Schema only. Downgrade destroys these tables and their data.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("timezone", sa.Text, nullable=False),
        sa.Column("locale", sa.Text, nullable=False),
        sa.CheckConstraint("length(name) > 0", name="households_name_nonempty"),
        sa.CheckConstraint("length(timezone) > 0", name="households_timezone_nonempty"),
        sa.CheckConstraint("length(locale) > 0", name="households_locale_nonempty"),
    )
    op.create_table(
        "members",
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
    op.create_table(
        "member_accounts",
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
    op.create_table(
        "audit_log",
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
        sa.CheckConstraint(
            "length(event_type) > 0", name="audit_log_event_type_nonempty"
        ),
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
    op.create_table(
        "audit_pointer",
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


def downgrade() -> None:
    op.drop_table("audit_pointer")
    op.drop_table("audit_log")
    op.drop_table("member_accounts")
    op.drop_table("members")
    op.drop_table("households")
