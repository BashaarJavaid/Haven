"""Persist immutable proposals and single-use approvals.

Revision ID: 0003_pipeline
Revises: 0002_household_graph
"""

from alembic import op

revision = "0003_pipeline"
down_revision = "0002_household_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE actions (
    household_id UUID NOT NULL,
    action_id TEXT NOT NULL,
    proposal JSONB NOT NULL,
    principal JSONB NOT NULL,
    cost TEXT,
    grant_seq BIGINT,
    PRIMARY KEY (household_id, action_id),
    FOREIGN KEY(household_id, grant_seq) REFERENCES audit_log (household_id, seq),
    CONSTRAINT actions_id_nonempty CHECK (length(action_id) > 0),
    CONSTRAINT actions_objects CHECK (jsonb_typeof(proposal) = 'object' AND jsonb_typeof(principal) = 'object'),
    CONSTRAINT actions_cost_nonnegative CHECK (cost IS NULL OR cost ~ '^[0-9]+([.][0-9]+)?$'),
    FOREIGN KEY(household_id) REFERENCES households (id)
)
    """)
    op.execute("""
CREATE TABLE approvals (
    household_id UUID NOT NULL,
    approval_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    status TEXT NOT NULL,
    binding JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (household_id, approval_id),
    FOREIGN KEY(household_id, action_id) REFERENCES actions (household_id, action_id),
    CONSTRAINT approvals_id_format CHECK (approval_id ~ '^apr_[0-9a-f]{32}$'),
    CONSTRAINT approvals_status CHECK (status IN ('pending','approved','rejected','expired','redeemed')),
    CONSTRAINT approvals_ttl CHECK (expires_at > created_at)
)
    """)
    op.execute(
        """CREATE UNIQUE INDEX approvals_one_pending ON approvals (household_id, action_id) WHERE status IN ('pending', 'approved')"""
    )
    op.execute("""
CREATE TABLE approval_votes (
    household_id UUID NOT NULL,
    approval_id TEXT NOT NULL,
    member_id UUID NOT NULL,
    approved BOOLEAN NOT NULL,
    principal JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (household_id, approval_id, member_id),
    FOREIGN KEY(household_id, approval_id) REFERENCES approvals (household_id, approval_id),
    FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id)
)
    """)


def downgrade() -> None:
    op.drop_table("approval_votes")
    op.drop_table("approvals")
    op.drop_table("actions")
