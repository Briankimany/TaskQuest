"""JournalEntry model.

One dated entry per user. ``entry_date`` is the user's *local* calendar day
(same semantics as ``CompletionLog.completed_on``); instants (created_at /
updated_at) are stored in UTC.
"""
from .base import db


def _utc_now():
    from app.utils.timezones import utc_now_naive
    return utc_now_naive()


class JournalEntry(db.Model):
    """A single dated journal entry with a title and free-form text."""
    __tablename__ = 'journal_entry'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False, default='')
    content = db.Column(db.Text, nullable=False, default='')

    created_at = db.Column(db.DateTime, default=_utc_now)
    updated_at = db.Column(db.DateTime, default=_utc_now, onupdate=_utc_now)

    user = db.relationship('User', backref=db.backref('journal_entries', lazy=True))

    def __repr__(self):
        return f'<JournalEntry {self.id} | {self.entry_date} | {self.title!r}>'