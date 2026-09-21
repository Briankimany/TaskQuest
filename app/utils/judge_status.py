"""
Judge availability status for the UI pill.

Reachability is probed with a bounded TCP connection to the configured
OmniRoute endpoint (see ``AIAssistant.health_check``). The pill states:
    LIVE        - provider reachable, latest review used real oracle metrics
    PROVISIONAL - provider reachable but the latest review recorded fallback metrics
    OFF         - provider unreachable
"""
from app.models.judge import JudgeReview
from app.utils.managers.ai_assistant import AIAssistant

PROVISIONAL_MARKER = "oracles were unavailable"

_status_cache = {}


def _latest_review(user_id):
    return JudgeReview.query.filter_by(user_id=user_id)\
        .order_by(JudgeReview.created_at.desc()).first()


def _is_provisional(review):
    if review is None:
        return False
    return bool(review.explanation) and PROVISIONAL_MARKER in review.explanation


def get_judge_status(user, probe=True):
    """Return the status dict for ``user``.

    ``probe=False`` skips the network call and only inspects persisted reviews
    (used for cheap badge rendering where reachability is irrelevant).
    """
    review = _latest_review(user.id) if user is not None else None
    provisional = _is_provisional(review)

    if not probe:
        state = "PROVISIONAL" if provisional else "LIVE"
        return {
            "state": state,
            "provisional": provisional,
            "latency_ms": None,
            "detail": "",
            "reached_at": None,
        }

    reached = False
    latency = None
    detail = ""
    try:
        reached, latency, detail = AIAssistant().health_check()
    except Exception as exc:  # pragma: no cover - defensive
        detail = str(exc)

    if reached:
        state = "PROVISIONAL" if provisional else "LIVE"
    else:
        state = "OFF"

    return {
        "state": state,
        "provisional": provisional,
        "latency_ms": latency,
        "detail": detail,
        "reached_at": review.created_at if review else None,
    }