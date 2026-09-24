"""Chat models: named conversation threads and their message transcripts.

Only user/assistant turns are persisted. The context block (recent activity,
journal entries, today's summary) is rebuilt per request and is never stored in
these tables — keep the transcript lean and truthful.
"""
from .base import db


def _utc_now():
    from app.utils.timezones import utc_now_naive
    return utc_now_naive()


class ChatConversation(db.Model):
    """A named, user-scoped chat conversation (thread)."""
    __tablename__ = 'chat_conversation'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False, default='')

    created_at = db.Column(db.DateTime, default=_utc_now)
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)

    user = db.relationship('User', backref=db.backref('chat_conversations', lazy=True))
    messages = db.relationship(
        'ChatMessage',
        backref='conversation',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='ChatMessage.created_at',
    )

    def __repr__(self):
        return f'<ChatConversation {self.id} | {self.title!r}>'


class ChatMessage(db.Model):
    """One persisted turn in a conversation."""
    __tablename__ = 'chat_message'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey('chat_conversation.id'), nullable=False, index=True)

    role = db.Column(db.String(20), nullable=False)  # user | assistant
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=_utc_now)

    def __repr__(self):
        return f'<ChatMessage {self.id} | {self.role} | {self.content[:30]!r}>'