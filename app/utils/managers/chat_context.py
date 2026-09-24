"""AI chat context builder.

Assembles the ``<context>`` block sent to the LLM on every chat turn. Reads the
user's recent discipline history (completions + judge verdicts), journal
entries, and today's summary. The block is rebuilt per request — it is never
persisted into the chat transcript tables.

All queries are user-scoped and truncated so a request stays bounded.
"""
from datetime import timedelta

from app.models import CompletionLog, JudgeReview, JournalEntry, db
from app.models.user import User
from app.utils.managers import UserManager
from app.utils.timezones import today_for_id, utc_now_naive, format_user_dt

RECENT_DAYS = 14
MAX_COMPLETIONS = 30
MAX_JUDGE_REVIEWS = 15
MAX_JOURNAL_ENTRIES = 20
MAX_BLOCK_CHARS = 6000


def _header(title: str) -> str:
    return f"[{title}]"


def _recent_completions(user_id: int, today) -> list:
    cutoff = today - timedelta(days=RECENT_DAYS)
    rows = (
        CompletionLog.query
        .filter(CompletionLog.user_id == user_id, CompletionLog.completed_on >= cutoff)
        .order_by(CompletionLog.completed_on.desc(), CompletionLog.id.desc())
        .limit(MAX_COMPLETIONS)
        .all()
    )
    lines = []
    for r in rows:
        name = r.sub_activity.name if r.sub_activity else f"task#{r.sub_activity_id}"
        lines.append(
            f"- {r.completed_on.isoformat()} | {name} | {r.status}"
            f"{'; reason: ' + (r.reason or '') if r.reason else ''}"
            f"{'; exp: ' + str(r.exp_impact) if r.exp_impact else ''}"
        )
    return lines


def _judge_reviews(user_id: int, tz_name) -> list:
    cutoff = utc_now_naive() - timedelta(days=RECENT_DAYS)
    rows = (
        JudgeReview.query
        .filter(JudgeReview.user_id == user_id, JudgeReview.created_at >= cutoff)
        .order_by(JudgeReview.created_at.desc())
        .limit(MAX_JUDGE_REVIEWS)
        .all()
    )
    lines = []
    for r in rows:
        when = format_user_dt(r.created_at, tz_name, "%Y-%m-%d")
        lines.append(
            f"- {when} | {r.task_name} ({r.task_status})"
            f" | penalty {r.penalty} | discipline {r.discipline}"
            f" | verdict {r.review_status}"
            f"{'; ' + (r.explanation or '') if r.explanation else ''}"
        )
    return lines


def _journal_entries(user_id: int) -> list:
    rows = (
        JournalEntry.query
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc())
        .limit(MAX_JOURNAL_ENTRIES)
        .all()
    )
    lines = []
    for e in reversed(rows):
        body = (e.content or '').replace('\n', ' ').strip()
        if len(body) > 500:
            body = body[:500] + '…'
        lines.append(f"- {e.entry_date.isoformat()} | {e.title or 'Untitled'} | {body}")
    return lines


def _today_schedule(user_id: int, today) -> list:
    """Today's scheduled tasks, matching the dashboard's missions list.

    Reuses the same fetch path as ``/missions/today`` (TaskScheduler +
    today's completion logs + build_missions) so the assistant and the Today
    page can never drift apart. Buffer entries (0 XP) are skipped, and a
    scheduling failure degrades to an empty schedule instead of breaking the
    whole context block.
    """
    try:
        from app.utils.schedulers import TaskScheduler
        from app.utils.timezones import now_for
        from app.utils.assets.dashboard_payloads import build_missions

        now = now_for(user_id)
        scheduled = TaskScheduler(user_id=user_id, date=now).get_daily_schedule(
            user_id=user_id, date_obj=today,
        )
        logs = CompletionLog.query.filter(
            CompletionLog.user_id == user_id,
            CompletionLog.completed_on == today,
        ).all()
        missions = build_missions(scheduled, logs, today, now=now)
    except Exception:
        return []

    lines = []
    for m in missions:
        title = (m.get("title") or "task").strip()
        xp = m.get("xp") or 0
        line = (
            f"- {m.get('start') or '--:--'} | {title} | +{int(xp)} XP "
            f"| {m.get('status') or 'ACTIVE'}"
        )
        if m.get("countdown"):
            line += f" | {m['countdown']}"
        lines.append(line)
    return lines


def _today_summary(user_id: int, today) -> str:
    rows = CompletionLog.query.filter(
        CompletionLog.user_id == user_id, CompletionLog.completed_on == today
    ).all()
    counts = {'completed': 0, 'partial': 0, 'skipped': 0}
    exp = 0
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.exp_impact:
            exp += r.exp_impact
    parts = []
    for status in ('completed', 'partial', 'skipped'):
        if counts[status]:
            parts.append(f"{status} {counts[status]}")
    summary = "none logged" if not parts else "; ".join(parts)
    return f"Tasks today ({today.isoformat()}): {summary}; net XP today: {exp:+d}"


def build_chat_context(user: User) -> str:
    """Return the plain-text context block for the user's chat system message."""
    user_id = user.id
    today = today_for_id(user_id)
    tz_name = user.timezone

    blocks = []
    blocks.append(_header("Player"))
    blocks.append(f"- {user.username}, level {user.level}, total XP {user.total_exp}")

    try:
        streak = UserManager.get_streak(user_id, today=today)
    except Exception:
        streak = 0
    blocks.append(f"- Current streak: {streak} day(s)")
    blocks.append(_today_summary(user_id, today))

    schedule = _today_schedule(user_id, today)
    if schedule:
        blocks.append("")
        blocks.append(_header(f"Today's schedule ({today.isoformat()})"))
        blocks.extend(schedule)

    completions = _recent_completions(user_id, today)
    if completions:
        blocks.append("")
        blocks.append(_header(f"Recent task activity (last {RECENT_DAYS} days)"))
        blocks.extend(completions)
    else:
        blocks.append("")
        blocks.append(_header("Recent task activity"))
        blocks.append("- None in the last 14 days")

    reviews = _judge_reviews(user_id, tz_name)
    if reviews:
        blocks.append("")
        blocks.append(_header("Judge verdicts"))
        blocks.extend(reviews)

    journal = _journal_entries(user_id)
    if journal:
        blocks.append("")
        blocks.append(_header("Journal entries"))
        blocks.extend(journal)

    text = "\n".join(blocks)
    if len(text) > MAX_BLOCK_CHARS:
        text = text[:MAX_BLOCK_CHARS].rsplit("\n", 1)[0] + "\n…"
    return text