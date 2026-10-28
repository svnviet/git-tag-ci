"""create tags table

Revision ID: 0001
Revises:
Create Date: 2026-10-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# columns added after the first (pre-Alembic) versions of the table
LATE_COLUMNS = {
    "params": sa.Column("params", sa.String(512), nullable=True),
    "prev_tag": sa.Column("prev_tag", sa.String(255), nullable=True),
    "output_dir": sa.Column("output_dir", sa.String(512), nullable=True),
    "notes_path": sa.Column("notes_path", sa.String(512), nullable=True),
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "tags" not in insp.get_table_names():
        op.create_table(
            "tags",
            sa.Column("name", sa.String(255), primary_key=True),
            sa.Column("commit", sa.String(64), nullable=False, server_default=""),
            sa.Column(
                "status", sa.String(16), nullable=False, server_default="pending"
            ),
            sa.Column("params", sa.String(512), nullable=False, server_default=""),
            sa.Column("prev_tag", sa.String(255)),
            sa.Column("output_dir", sa.String(512)),
            sa.Column("notes_path", sa.String(512)),
            sa.Column("exit_code", sa.Integer()),
            sa.Column("log_path", sa.String(512)),
            sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("finished_at", sa.DateTime(timezone=True)),
        )
        op.create_index("ix_tags_status", "tags", ["status"])
        return
    # database created before Alembic was introduced: only add what is missing
    have = {c["name"] for c in insp.get_columns("tags")}
    for name, col in LATE_COLUMNS.items():
        if name not in have:
            op.add_column("tags", col)
    if "ix_tags_status" not in {i["name"] for i in insp.get_indexes("tags")}:
        op.create_index("ix_tags_status", "tags", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tags_status", table_name="tags")
    op.drop_table("tags")
