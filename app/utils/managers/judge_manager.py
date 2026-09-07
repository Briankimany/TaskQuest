"""
JudgeManager — persistence and LLM orchestration for System Judge reviews.

Each penalized CompletionLog gets exactly one JudgeReview. Reviews are created
lazily (get-or-create while rendering the dashboard), so no new hooks are
needed in the completion flow. All LLM calls are delegated to the assistant
layer (``PenaltyEvaluator.evaluate_judge_review``); persistent transport
failures fall back to discipline-derived metrics so the page always renders.
"""
from app.models import db
from app.models.judge import JudgeReview
from app.utils.logger import api_logger
from app.utils.exceptions import AssistantError
from .ai_assistant import AIAssistant
from .penalty_evaluator import PenaltyEvaluator


def _display_status(log):
    """Map a completion log to a UI status label (matches mission list)."""
    if log.status == "completed" and log.exp_impact is not None and log.exp_impact < 0:
        return "COMPLETED_LATE"
    if log.status == "skipped":
        return "MISSED"
    return log.status.upper()


class JudgeManager:
    evaluator = PenaltyEvaluator(AIAssistant())

    # ── creation ──
    @classmethod
    def get_or_create_for_log(cls, log, dcp):
        """Return the existing review for a log, creating one if needed."""
        existing = JudgeReview.query.filter_by(completion_log_id=log.id).first()
        if existing:
            return existing
        return cls.create_review(log=log, dcp=dcp)

    @classmethod
    def create_review(cls, log, dcp):
        review = JudgeReview(
            user_id=log.user_id,
            completion_log_id=log.id,
            task_name=log.sub_activity.name if log.sub_activity else "Unknown",
            task_status=_display_status(log),
            user_reason=log.reason or None,
            penalty=log.exp_impact or 0,
            discipline=round(dcp * 100),
            review_status="PENDING",
        )

        metrics = cls._fallback_metrics(review.discipline)
        try:
            result = cls.evaluator.evaluate_judge_review(
                task_name=review.task_name,
                task_status=review.task_status,
                reason=review.user_reason or "",
                penalty=review.penalty,
                discipline=review.discipline,
            )
            if result is not None:
                metrics = result
        except (AssistantError, ValueError) as e:
            api_logger.warning("Judge fallback for log %s: %s", log.id, e)

        review.validity = metrics["validity"]
        review.responsibility = metrics["responsibility"]
        review.consistency = metrics["consistency"]
        review.explanation = metrics.get("explanation", "")

        db.session.add(review)
        db.session.commit()
        api_logger.info("Judge review %s created for log %s", review.id, log.id)
        return review

    @staticmethod
    def _fallback_metrics(discipline):
        d = max(0, min(100, discipline)) / 100.0
        return {
            "validity": round(d * 100),
            "responsibility": round(d * 95),
            "consistency": min(100, round(d * 100 + 10)),
            "explanation": "The oracles were unavailable; a provisional verdict was recorded.",
        }

    # ── resolution ──
    @classmethod
    def resolve_review(cls, review, user_id=None):
        """Guard that a review belongs to the requesting user and is still open."""
        if review is None:
            return None
        if user_id is not None and review.user_id != user_id:
            return None
        if review.review_status != "PENDING":
            raise ValueError("This review has already been resolved.")
        return review

    @classmethod
    def accept(cls, review_id, user_id):
        review = cls.resolve_review(
            JudgeReview.query.filter_by(id=review_id, user_id=user_id).first(), user_id)
        if review is None:
            return None
        review.review_status = "ACCEPTED"
        db.session.commit()
        api_logger.info("Judge review %s accepted", review.id)
        return review

    @classmethod
    def dispute(cls, review_id, user_id, reason):
        review = cls.resolve_review(
            JudgeReview.query.filter_by(id=review_id, user_id=user_id).first(), user_id)
        if review is None:
            return None
        result = None
        try:
            result = cls.evaluator.evaluate_judge_review(
                task_name=review.task_name,
                task_status=review.task_status,
                reason=review.user_reason or "",
                penalty=review.penalty,
                discipline=review.discipline,
                dispute_reason=reason or "",
            )
        except (AssistantError, ValueError) as e:
            api_logger.warning("Judge dispute fallback for review %s: %s", review.id, e)
        if result is not None:
            review.validity = result["validity"]
            review.responsibility = result["responsibility"]
            review.consistency = result["consistency"]
            review.explanation = result.get("explanation", review.explanation)
        review.dispute_reason = reason or None
        review.review_status = "DISPUTED"
        db.session.commit()
        return review

    # ── serialization ──
    @classmethod
    def to_context_dict(cls, review):
        return {
            "id": review.id,
            "task": review.task_name,
            "status": review.task_status,
            "user_reason": review.user_reason or "",
            "metrics": {
                "validity": review.validity,
                "responsibility": review.responsibility,
                "consistency": review.consistency,
            },
            "penalty": review.penalty,
            "discipline_delta": 0,
            "review_status": review.review_status,
        }

    @classmethod
    def to_api_dict(cls, review):
        return {
            "id": review.id,
            "task": review.task_name,
            "status": review.task_status,
            "user_reason": review.user_reason or "",
            "penalty": review.penalty,
            "discipline": review.discipline,
            "metrics": {
                "validity": review.validity,
                "responsibility": review.responsibility,
                "consistency": review.consistency,
            },
            "explanation": review.explanation or "",
            "review_status": review.review_status,
            "dispute_reason": review.dispute_reason or "",
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }