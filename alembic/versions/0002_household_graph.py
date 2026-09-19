"""Household graph and history. Downgrade destroys item 6 data/history."""

from alembic import op

revision: str = "0002_household_graph"
down_revision: str = "0001_initial"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE households ADD COLUMN rate_plan TEXT")
    op.execute("ALTER TABLE households ADD COLUMN constitution_version INTEGER")
    op.execute(
        "ALTER TABLE households ADD COLUMN attributes JSONB DEFAULT '{}'::jsonb NOT NULL"
    )
    op.execute(
        "ALTER TABLE households ADD COLUMN valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )
    op.execute("ALTER TABLE households ADD COLUMN valid_to TIMESTAMP WITH TIME ZONE")
    op.execute(
        "ALTER TABLE households ADD CONSTRAINT households_rate_plan_allowed CHECK (rate_plan IS NULL OR rate_plan IN ('comed_time_of_day', 'comed_hourly', 'twin'))"
    )
    op.execute(
        "ALTER TABLE households ADD CONSTRAINT households_attributes_object CHECK (jsonb_typeof(attributes) = 'object')"
    )
    op.execute(
        "ALTER TABLE households ADD CONSTRAINT households_current_open CHECK (valid_to IS NULL)"
    )
    op.execute(
        "ALTER TABLE members ADD COLUMN attributes JSONB DEFAULT '{}'::jsonb NOT NULL"
    )
    op.execute(
        "ALTER TABLE members ADD COLUMN valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )
    op.execute("ALTER TABLE members ADD COLUMN valid_to TIMESTAMP WITH TIME ZONE")
    op.execute(
        "ALTER TABLE members ADD CONSTRAINT members_current_open CHECK (valid_to IS NULL)"
    )
    op.execute(
        "ALTER TABLE members ADD CONSTRAINT members_attributes_object CHECK (jsonb_typeof(attributes) = 'object')"
    )
    op.execute(
        "ALTER TABLE member_accounts ADD COLUMN attributes JSONB DEFAULT '{}'::jsonb NOT NULL"
    )
    op.execute(
        "ALTER TABLE member_accounts ADD COLUMN valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL"
    )
    op.execute(
        "ALTER TABLE member_accounts ADD COLUMN valid_to TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE member_accounts ADD CONSTRAINT member_accounts_current_open CHECK (valid_to IS NULL)"
    )
    op.execute(
        "ALTER TABLE member_accounts ADD CONSTRAINT member_accounts_attributes_object CHECK (jsonb_typeof(attributes) = 'object')"
    )
    op.execute("""
        CREATE TABLE asset_bindings_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            asset_id UUID NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT asset_bindings_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE asset_policies_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            asset_id UUID NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT asset_policies_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE assets_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            owner_member_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT assets_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE contact_channels_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            contact_id UUID NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT contact_channels_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE households_history (
            id UUID NOT NULL,
            name TEXT NOT NULL,
            timezone TEXT NOT NULL,
            locale TEXT NOT NULL,
            rate_plan TEXT,
            constitution_version INTEGER,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id, valid_from),
            CONSTRAINT households_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE member_accounts_history (
            household_id UUID NOT NULL,
            provider TEXT NOT NULL,
            sub TEXT NOT NULL,
            member_id UUID NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, provider, sub, valid_from),
            CONSTRAINT member_accounts_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE members_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT members_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE observation_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            asset_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT observation_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE preferences_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID NOT NULL,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT preferences_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE routines_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT routines_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE schedule_events_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            schedule_id UUID NOT NULL,
            member_id UUID,
            zone_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT schedule_events_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE schedules_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT schedules_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE trusted_contacts_history (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (household_id, id, valid_from),
            CONSTRAINT trusted_contacts_history_interval CHECK (valid_to > valid_from)
        )
    """)
    op.execute("""
        CREATE TABLE constitution_versions (
            household_id UUID NOT NULL,
            version INTEGER NOT NULL,
            yaml TEXT NOT NULL,
            hash TEXT NOT NULL,
            status TEXT DEFAULT 'unvalidated' NOT NULL,
            compiled_cedar TEXT,
            analysis_report JSONB,
            activated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, version),
            CONSTRAINT constitution_version_positive CHECK (version > 0),
            CONSTRAINT constitution_hash_hex CHECK (hash ~ '^[0-9a-f]{64}$'),
            CONSTRAINT constitution_unvalidated_only CHECK (status = 'unvalidated' AND compiled_cedar IS NULL AND activated_at IS NULL),
            FOREIGN KEY(household_id) REFERENCES households (id)
        )
    """)
    op.execute("""
        CREATE TABLE assets (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            owner_member_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, owner_member_id) REFERENCES members (household_id, id),
            CONSTRAINT assets_current_open CHECK (valid_to IS NULL),
            CONSTRAINT assets_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE preferences (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID NOT NULL,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            CONSTRAINT preferences_current_open CHECK (valid_to IS NULL),
            CONSTRAINT preferences_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE routines (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            CONSTRAINT routines_current_open CHECK (valid_to IS NULL),
            CONSTRAINT routines_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE schedules (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            CONSTRAINT schedules_current_open CHECK (valid_to IS NULL),
            CONSTRAINT schedules_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE trusted_contacts (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            CONSTRAINT trusted_contacts_current_open CHECK (valid_to IS NULL),
            CONSTRAINT trusted_contacts_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE asset_bindings (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            asset_id UUID NOT NULL,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, asset_id) REFERENCES assets (household_id, id),
            UNIQUE (household_id, asset_id),
            CONSTRAINT asset_bindings_current_open CHECK (valid_to IS NULL),
            CONSTRAINT asset_bindings_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE asset_policies (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            asset_id UUID NOT NULL,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, asset_id) REFERENCES assets (household_id, id),
            UNIQUE (household_id, asset_id),
            CONSTRAINT asset_policies_current_open CHECK (valid_to IS NULL),
            CONSTRAINT asset_policies_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE contact_channels (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            contact_id UUID NOT NULL,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, contact_id) REFERENCES trusted_contacts (household_id, id),
            CONSTRAINT contact_channels_current_open CHECK (valid_to IS NULL),
            CONSTRAINT contact_channels_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute("""
        CREATE TABLE observations (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            member_id UUID,
            asset_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            FOREIGN KEY(household_id, asset_id) REFERENCES assets (household_id, id),
            CONSTRAINT observations_one_subject CHECK (member_id IS NULL OR asset_id IS NULL),
            CONSTRAINT observations_current_open CHECK (valid_to IS NULL),
            CONSTRAINT observations_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX observations_asset_unique ON observations (household_id, asset_id) WHERE asset_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX observations_household_unique ON observations (household_id) WHERE member_id IS NULL AND asset_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX observations_member_unique ON observations (household_id, member_id) WHERE member_id IS NOT NULL"
    )
    op.execute("""
        CREATE TABLE schedule_events (
            household_id UUID NOT NULL,
            id UUID NOT NULL,
            schedule_id UUID NOT NULL,
            member_id UUID,
            zone_id UUID,
            attributes JSONB DEFAULT '{}'::jsonb NOT NULL,
            valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            valid_to TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (household_id, id),
            FOREIGN KEY(household_id) REFERENCES households (id),
            FOREIGN KEY(household_id, schedule_id) REFERENCES schedules (household_id, id),
            FOREIGN KEY(household_id, member_id) REFERENCES members (household_id, id),
            FOREIGN KEY(household_id, zone_id) REFERENCES assets (household_id, id),
            CONSTRAINT schedule_events_current_open CHECK (valid_to IS NULL),
            CONSTRAINT schedule_events_attributes_object CHECK (jsonb_typeof(attributes) = 'object')
        )
    """)
    op.execute(
        "ALTER TABLE households ADD CONSTRAINT households_constitution_version_fk FOREIGN KEY(id, constitution_version) REFERENCES constitution_versions (household_id, version) DEFERRABLE INITIALLY DEFERRED"
    )
    op.execute("""
        CREATE MATERIALIZED VIEW household_context AS  SELECT h.id AS household_id, jsonb_build_object('households', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.id)
                    FROM households x WHERE x.id = h.id), '[]'::jsonb), 'members', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM members x WHERE x.household_id = h.id), '[]'::jsonb), 'trusted_contacts', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM trusted_contacts x WHERE x.household_id = h.id), '[]'::jsonb), 'contact_channels', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM contact_channels x WHERE x.household_id = h.id), '[]'::jsonb), 'assets', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM assets x WHERE x.household_id = h.id), '[]'::jsonb), 'asset_bindings', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM asset_bindings x WHERE x.household_id = h.id), '[]'::jsonb), 'asset_policies', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM asset_policies x WHERE x.household_id = h.id), '[]'::jsonb), 'schedules', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM schedules x WHERE x.household_id = h.id), '[]'::jsonb), 'schedule_events', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM schedule_events x WHERE x.household_id = h.id), '[]'::jsonb), 'routines', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM routines x WHERE x.household_id = h.id), '[]'::jsonb), 'preferences', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM preferences x WHERE x.household_id = h.id), '[]'::jsonb), 'observations', COALESCE((SELECT jsonb_agg(((to_jsonb(x) - 'attributes') || x.attributes) - 'safe_word_hash' - 'value_hash' ORDER BY x.household_id, x.id)
                    FROM observations x WHERE x.household_id = h.id), '[]'::jsonb)) AS data FROM households h
    """)
    op.execute(
        "CREATE UNIQUE INDEX household_context_household_idx ON household_context(household_id)"
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW household_context")
    op.execute(
        "ALTER TABLE households DROP CONSTRAINT households_constitution_version_fk"
    )
    op.execute("DROP TABLE schedule_events")
    op.execute("DROP TABLE observations")
    op.execute("DROP TABLE contact_channels")
    op.execute("DROP TABLE asset_policies")
    op.execute("DROP TABLE asset_bindings")
    op.execute("DROP TABLE trusted_contacts")
    op.execute("DROP TABLE schedules")
    op.execute("DROP TABLE routines")
    op.execute("DROP TABLE preferences")
    op.execute("DROP TABLE assets")
    op.execute("DROP TABLE constitution_versions")
    op.execute("DROP TABLE trusted_contacts_history")
    op.execute("DROP TABLE schedules_history")
    op.execute("DROP TABLE schedule_events_history")
    op.execute("DROP TABLE routines_history")
    op.execute("DROP TABLE preferences_history")
    op.execute("DROP TABLE observation_history")
    op.execute("DROP TABLE members_history")
    op.execute("DROP TABLE member_accounts_history")
    op.execute("DROP TABLE households_history")
    op.execute("DROP TABLE contact_channels_history")
    op.execute("DROP TABLE assets_history")
    op.execute("DROP TABLE asset_policies_history")
    op.execute("DROP TABLE asset_bindings_history")
    op.execute("ALTER TABLE member_accounts DROP COLUMN attributes")
    op.execute("ALTER TABLE member_accounts DROP COLUMN valid_from")
    op.execute("ALTER TABLE member_accounts DROP COLUMN valid_to")
    op.execute("ALTER TABLE members DROP COLUMN attributes")
    op.execute("ALTER TABLE members DROP COLUMN valid_from")
    op.execute("ALTER TABLE members DROP COLUMN valid_to")
    op.execute("ALTER TABLE households DROP COLUMN attributes")
    op.execute("ALTER TABLE households DROP COLUMN valid_from")
    op.execute("ALTER TABLE households DROP COLUMN valid_to")
    op.execute("ALTER TABLE households DROP COLUMN rate_plan")
    op.execute("ALTER TABLE households DROP COLUMN constitution_version")
