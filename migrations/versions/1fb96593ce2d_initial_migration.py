"""Initial migration.

Revision ID: 1fb96593ce2d
Revises: 
Create Date: 2025-11-11 22:54:05.164083

"""
from alembic import op
import sqlalchemy as sa


revision = '1fb96593ce2d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))

    op.execute("UPDATE activity SET is_active = TRUE WHERE is_active IS NULL")
    

def downgrade():
    with op.batch_alter_table('activity', schema=None) as batch_op:
        batch_op.drop_column('is_active')

