"""Add journal entries, AI chat conversations/messages, and chat consent fields.

Revision ID: b2d3e4f5a6b7
Revises: a1c2e3f4b5d6
Create Date: 2026-09-23

Adds three tables (journal_entry, chat_conversation, chat_message) and two
columns on user (ai_chat_consented, ai_chat_consented_at). Consent controls
whether chat turns are sent to the LLM provider; revoking keeps history.

All user *instants* stay UTC-naive, matching the existing convention; chat
message timestamps are rendered server-side into the account timezone.

NOTE: The app factory runs ``db.create_all()`` at import time (also on the
``flask`` CLI process), so the new tables may already exist by the time this
migration runs. Every step is therefore guarded with existence checks so the
upgrade is idempotent.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2d3e4f5a6b7'
down_revision = 'a1c2e3f4b5d6'
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    return sa.inspect(bind).has_table(name)


def _has_column(bind, table: str, column: str) -> bool:
    return column in [c['name'] for c in sa.inspect(bind).get_columns(table)]


def _has_index(bind, table: str, column: str) -> bool:
    inspector = sa.inspect(bind)
    for index in inspector.get_indexes(table):
        cols = index.get('column_names') or []
        if cols == [column]:
            return True
    return False


def upgrade():
    bind = op.get_bind()

    if not _has_column(bind, 'user', 'ai_chat_consented'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.add_column(sa.Column(
                'ai_chat_consented', sa.Boolean(), nullable=False,
                server_default='0'))
    if not _has_column(bind, 'user', 'ai_chat_consented_at'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.add_column(sa.Column(
                'ai_chat_consented_at', sa.DateTime(), nullable=True))
    op.execute('UPDATE user SET ai_chat_consented = 0 WHERE ai_chat_consented IS NULL')

    if not _has_table(bind, 'journal_entry'):
        op.create_table(
            'journal_entry',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
            sa.Column('entry_date', sa.Date(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False, server_default=''),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    if not _has_index(bind, 'journal_entry', 'user_id'):
        op.create_index('ix_journal_entry_user_id', 'journal_entry', ['user_id'])
    if not _has_index(bind, 'journal_entry', 'entry_date'):
        op.create_index('ix_journal_entry_entry_date', 'journal_entry', ['entry_date'])

    if not _has_table(bind, 'chat_conversation'):
        op.create_table(
            'chat_conversation',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False, server_default=''),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    if not _has_index(bind, 'chat_conversation', 'user_id'):
        op.create_index('ix_chat_conversation_user_id', 'chat_conversation', ['user_id'])

    if not _has_table(bind, 'chat_message'):
        op.create_table(
            'chat_message',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('chat_conversation.id'),
                      nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
    if not _has_index(bind, 'chat_message', 'conversation_id'):
        op.create_index('ix_chat_message_conversation_id', 'chat_message', ['conversation_id'])


def downgrade():
    bind = op.get_bind()

    if _has_table(bind, 'chat_message'):
        op.drop_index('ix_chat_message_conversation_id', table_name='chat_message')
        op.drop_table('chat_message')
    if _has_table(bind, 'chat_conversation'):
        op.drop_index('ix_chat_conversation_user_id', table_name='chat_conversation')
        op.drop_table('chat_conversation')
    if _has_table(bind, 'journal_entry'):
        op.drop_index('ix_journal_entry_entry_date', table_name='journal_entry')
        op.drop_index('ix_journal_entry_user_id', table_name='journal_entry')
        op.drop_table('journal_entry')

    if _has_column(bind, 'user', 'ai_chat_consented_at'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.drop_column('ai_chat_consented_at')
    if _has_column(bind, 'user', 'ai_chat_consented'):
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.drop_column('ai_chat_consented')