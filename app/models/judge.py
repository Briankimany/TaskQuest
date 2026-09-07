"""
JudgeReview model.

A review record issued by the System Judge for a penalized (missed, late, or
skipped) task. Metrics are 0-100 scores produced by the LLM evaluator, with a
deterministic fallback when the provider is unreachable.
"""
from datetime import datetime
from .base import db


class JudgeReview(db.Model):
    """System Judge verdict for one penalized completion log."""
    __tablename__ = 'judge_review'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    completion_log_id = db.Column(db.Integer, db.ForeignKey('completion_log.id'),
                                  nullable=False, unique=True)

    task_name = db.Column(db.String, nullable=False)
    task_status = db.Column(db.String(20), nullable=False)
    user_reason = db.Column(db.Text, nullable=True)
    penalty = db.Column(db.Integer, nullable=False, default=0)
    discipline = db.Column(db.Integer, nullable=False, default=0)

    validity = db.Column(db.Integer, nullable=False, default=0)
    responsibility = db.Column(db.Integer, nullable=False, default=0)
    consistency = db.Column(db.Integer, nullable=False, default=0)
    explanation = db.Column(db.Text, nullable=True)

    review_status = db.Column(db.String(20), nullable=False, default='PENDING')
    dispute_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('judge_reviews', lazy=True))
    completion_log = db.relationship('CompletionLog',
                                     backref=db.backref('judge_review', uselist=False, lazy=True))

    def __repr__(self):
        return f'<JudgeReview {self.id} | {self.task_status} | {self.review_status}>'