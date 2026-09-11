"""Create chat room and message tables."""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_chat_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "room",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("author", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["room.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_room_id", "message", ["room_id"])
    op.create_index("ix_message_posted_at", "message", ["posted_at"])


def downgrade():
    op.drop_index("ix_message_posted_at", table_name="message")
    op.drop_index("ix_message_room_id", table_name="message")
    op.drop_table("message")
    op.drop_table("room")
