"""
System Judge API — accept / dispute reviews.

ACCEPT marks a pending review as accepted. DISPUTE re-runs the LLM evaluator
with the player's dispute reason and updates the verdict before marking it
DISPUTED (per the wiring decision: disputes are re-judged by the oracle).
"""
from flask import request, jsonify, session
from app.routes.api import api_bp, log_app_errors
from app.utils.exceptions.custom_errors import RecordNotFoundError, InvalidRequestData
from app.models.judge import JudgeReview
from app.utils.managers.judge_manager import JudgeManager


def _get_open_review(review_id):
    user_id = session['user_id']
    review = JudgeReview.query.filter_by(id=review_id, user_id=user_id).first()
    if not review:
        raise RecordNotFoundError(f"No review with id {review_id}", 404)
    return review


@api_bp.route('/judge/reviews', methods=['GET'])
@log_app_errors
def judge_reviews():
    """List the logged-in user's judge reviews."""
    user_id = session['user_id']
    reviews = JudgeReview.query.filter_by(user_id=user_id)\
        .order_by(JudgeReview.created_at.desc()).all()
    return jsonify({
        'reviews': [JudgeManager.to_api_dict(r) for r in reviews]
    }), 200


@api_bp.route('/judge/<int:review_id>/accept', methods=['POST'])
@log_app_errors
def accept_review(review_id):
    """Accept a pending review."""
    review = _get_open_review(review_id)
    try:
        resolved = JudgeManager.accept(review.id, session['user_id'])
    except ValueError as e:
        raise InvalidRequestData(str(e))
    return jsonify(JudgeManager.to_api_dict(resolved)), 200


@api_bp.route('/judge/<int:review_id>/dispute', methods=['POST'])
@log_app_errors
def dispute_review(review_id):
    """Dispute a pending review; re-runs the LLM with the dispute reason."""
    review = _get_open_review(review_id)
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()
    if not reason:
        raise InvalidRequestData("A dispute reason is required.")
    try:
        resolved = JudgeManager.dispute(review.id, session['user_id'], reason)
    except ValueError as e:
        raise InvalidRequestData(str(e))
    return jsonify(JudgeManager.to_api_dict(resolved)), 200