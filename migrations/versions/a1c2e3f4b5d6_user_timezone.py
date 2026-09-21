"""Add per-user timezone column.

Revision ID: a1c2e3f4b5d6
Revises: 1fb96593ce2d
Create Date: 2026-09-21

Timezone semantics:
- user.timezone stores an IANA name ("Africa/Nairobi" default). All *instants*
  (created_at / updated_at / exported_at) are stored in UTC; the account
  timezone determines the *calendar day* used for timetable dates, completed_on,
  streaks and "today".
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c2e3f4b5d6'
down_revision = '1fb96593ce2d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'timezone', sa.String(length=64), nullable=False,
            server_default='Africa/Nairobi'))
    op.execute("UPDATE user SET timezone = 'Africa/Nairobi' WHERE timezone IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('timezone')