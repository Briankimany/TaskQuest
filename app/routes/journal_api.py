"""Journal API — CRUD for the user's dated journal entries.

Ownership is enforced on every read/write via ``user_id`` from the session.
All routes require login (the general decorator also logs failures).
"""
from datetime import datetime, date

from flask import request, jsonify, session

from app.routes.api import api_bp, log_app_errors
from app.utils.exceptions.custom_errors import InvalidRequestData, RecordNotFoundError
from app.models.journal import JournalEntry
from app.models.base import db
from app.config import DATE_PARSING_STRING
from app.utils.timezones import today_for_id


def _serialize(entry: JournalEntry) -> dict:
    return {
        'id': entry.id,
        'entry_date': entry.entry_date.isoformat(),
        'title': entry.title or '',
        'content': entry.content or '',
        'created_at': entry.created_at.isoformat() + 'Z' if entry.created_at else None,
        'updated_at': entry.updated_at.isoformat() + 'Z' if entry.updated_at else None,
    }


def _get_entry(entry_id: int, user_id: int) -> JournalEntry:
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if not entry:
        raise RecordNotFoundError(f"No journal entry with id {entry_id}")
    return entry


def _parse_date(value, field_name="entry_date") -> date:
    if not value:
        raise InvalidRequestData(f"{field_name} is required (format {DATE_PARSING_STRING})")
    try:
        return datetime.strptime(str(value).strip(), DATE_PARSING_STRING).date()
    except ValueError:
        raise InvalidRequestData(f"{field_name} must match format {DATE_PARSING_STRING}")


def _parse_month(value) -> tuple:
    if not value:
        today = today_for_id(session['user_id'])
        return today.year, today.month
    try:
        year_s, month_s = str(value).strip().split('-')
        year = int(year_s)
        month = int(month_s)
        if not (1 <= month <= 12):
            raise ValueError
        return year, month
    except (ValueError, TypeError):
        raise InvalidRequestData("month must match format YYYY-MM")


@api_bp.route('/journal', methods=['GET', 'POST'])
@log_app_errors
def journal():
    """List entries for a month, or create a new entry."""
    user_id = session['user_id']

    if request.method == 'GET':
        year, month = _parse_month(request.args.get('month'))
        start = date(year, month, 1)
        end = date(year + (1 if month == 12 else 0), 1, 1) if month == 12 else date(year, month + 1, 1)
        entries = (
            JournalEntry.query
            .filter(JournalEntry.user_id == user_id,
                    JournalEntry.entry_date >= start,
                    JournalEntry.entry_date < end)
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())
            .all()
        )
        return jsonify({
            'month': f"{year:04d}-{month:02d}",
            'entries': [_serialize(e) for e in entries],
        }), 200

    data = request.get_json(silent=True) or {}
    entry_date = _parse_date(data.get('entry_date'))
    content = (data.get('content') or '').strip()
    if not content:
        raise InvalidRequestData("content cannot be empty")
    title = (data.get('title') or '').strip()[:200]

    entry = JournalEntry(user_id=user_id, entry_date=entry_date, title=title, content=content)
    db.session.add(entry)
    db.session.commit()
    return jsonify(_serialize(entry)), 201


@api_bp.route('/journal/<int:entry_id>', methods=['PUT', 'DELETE'])
@log_app_errors
def journal_entry(entry_id):
    """Update or delete one of the user's journal entries."""
    user_id = session['user_id']
    entry = _get_entry(entry_id, user_id)

    if request.method == 'DELETE':
        db.session.delete(entry)
        db.session.commit()
        return '', 204

    data = request.get_json(silent=True) or {}
    if 'entry_date' in data:
        entry.entry_date = _parse_date(data.get('entry_date'))
    if 'title' in data:
        entry.title = (data.get('title') or '').strip()[:200]
    if 'content' in data:
        content = (data.get('content') or '').strip()
        if not content:
            raise InvalidRequestData("content cannot be empty")
        entry.content = content
    db.session.commit()
    return jsonify(_serialize(entry)), 200