"""
LLM evaluation harness for the system assistant.

Drives the live AI assistant through the real app pipeline - skip penalty,
judge review creation, and dispute re-runs - and prints the model response,
timing, and whether the deterministic fallback was used.

Runs inside the Flask app context directly; it never starts the dev server.

Usage:
    python app\\test\\llm_eval.py --probe
    python app\\test\\llm_eval.py --skip 58 --uid 1 --reason "An emergency came up."
    python app\\test\\llm_eval.py --judge 57 --uid 1
    python app\\test\\llm_eval.py --dispute 3 --uid 1 --reason "That penalty was too harsh."

Set OMNIROUTE_MODEL (e.g. free-coders) or pass --model to target a model.
"""
from pathlib import Path
import sys
import os
import time
import argparse

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app import app
from app.models import CompletionLog, TimetableEntry
from app.utils.managers.completion_manager import CompletionLogManager
from app.utils.managers.judge_manager import JudgeManager
from app.utils.managers.db.user_manger import UserManager
from app.utils.managers.ai_assistant import AIAssistant
from app.utils.exceptions import RecordDuplicationError, InvalidRequestData

FALLBACK_EXPLANATION = "The oracles were unavailable; a provisional verdict was recorded."


def _print_review(review):
    data = JudgeManager.to_api_dict(review)
    used_fallback = data["explanation"] == FALLBACK_EXPLANATION
    print("review_id       :", data["id"])
    print("task            :", data["task"])
    print("status          :", data["status"])
    print("user_reason     :", data["user_reason"])
    print("penalty (exp)   :", data["penalty"])
    print("discipline      :", data["discipline"])
    print("metrics         :", data["metrics"])
    print("review_status   :", data["review_status"])
    print("dispute_reason  :", data["dispute_reason"])
    print("explanation     :", data["explanation"])
    print("fallback_used   :", used_fallback)
    return used_fallback


def probe(model):
    assistant = AIAssistant()
    print("model           :", os.getenv("OMNIROUTE_MODEL") or assistant.config.get("default_model"))
    print("base_url        :", assistant.client.base_url)
    t0 = time.time()
    result = assistant.complete(
        system_prompt="You are a strict but fair system judge. Reply with JSON only.",
        user_prompt='Classify this skip reason quality. Return JSON {"validity": 0-100, "notes": "..."}.\nReason: An unexpected family emergency came up.',
        model=model,
    )
    elapsed = round(time.time() - t0, 2)
    print("elapsed_s       :", elapsed)
    print("response        :", result if result is not None else None)
    return 0 if result is not None else 2


def skip(entry_id, uid, reason):
    with app.app_context():
        entry = TimetableEntry.query.get(entry_id)
        if entry is None:
            print("No timetable entry with id", entry_id)
            return 2
        day = entry.timetable.date
        existing = CompletionLog.query.filter_by(
            user_id=uid, timetable_entry_id=entry_id, completed_on=day).first()
        if existing:
            print("Entry already logged as completion log", existing.id, existing.status)
            return 1

        base = entry.sub_activity.base_exp
        diff = entry.sub_activity.difficulty_multiplier
        fallback_mult = CompletionLogManager.exp_manager._get_skip_penalty_multiplier(reason)
        fallback_exp = -int(base * diff * fallback_mult)

        t0 = time.time()
        try:
            log = CompletionLogManager.create_completion_log(
                user_id=uid,
                timetable_entry_id=entry_id,
                status="skipped",
                completion_time=None,
                reason=reason,
            )
        except InvalidRequestData as e:
            print("create_completion_log rejected:", str(e))
            return 2
        elapsed = round(time.time() - t0, 2)

        print("completion log  :", log.id)
        print("task            :", log.sub_activity.name)
        print("status          :", log.status)
        print("date            :", log.completed_on)
        print("reason          :", log.reason)
        print("exp_impact      :", log.exp_impact)
        print("elapsed_s       :", elapsed)
        print("fallback_used   :", log.exp_impact == fallback_exp)
        print("(deterministic fallback exp would be", fallback_exp, ")")

        dcp = UserManager.get_dcp(uid, day)
        print("dcp             :", round(dcp, 3))
        time.sleep(1)
        print("--- judge review for this log ---")
        review = JudgeManager.get_or_create_for_log(log, dcp)
        _print_review(review)
        return 0


def judge(log_id, uid):
    with app.app_context():
        log = CompletionLog.query.get(log_id)
        if log is None:
            print("No completion log with id", log_id)
            return 2
        dcp = UserManager.get_dcp(uid, log.completed_on)
        review = JudgeManager.get_or_create_for_log(log, dcp)
        _print_review(review)
        return 0


def dispute(review_id, uid, reason):
    with app.app_context():
        review = JudgeManager.dispute(review_id, uid, reason)
        if review is None:
            print("Review not found or not yours:", review_id)
            return 2
        _print_review(review)
        return 0


def main():
    parser = argparse.ArgumentParser(description="Live LLM evaluation harness")
    parser.add_argument("--model", default=None, help="model id override (also settable via OMNIROUTE_MODEL)")
    parser.add_argument("--uid", type=int, default=1)
    parser.add_argument("--probe", action="store_true", help="bare assistant call")
    parser.add_argument("--skip", type=int, metavar="ENTRY_ID", help="skip a scheduled task and judge it")
    parser.add_argument("--judge", type=int, metavar="LOG_ID", help="create/get the judge review for a completion log")
    parser.add_argument("--dispute", type=int, metavar="REVIEW_ID", help="re-run the LLM through the dispute path")
    parser.add_argument("--reason", default="", help="skip/dispute reason")
    args = parser.parse_args()

    if args.model:
        os.environ["OMNIROUTE_MODEL"] = args.model

    if args.probe:
        return probe(args.model)
    if args.skip:
        if not args.reason.strip():
            print("--reason is required for --skip")
            return 2
        return skip(args.skip, args.uid, args.reason)
    if args.judge:
        return judge(args.judge, args.uid)
    if args.dispute:
        if not args.reason.strip():
            print("--reason is required for --dispute")
            return 2
        return dispute(args.dispute, args.uid, args.reason)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())