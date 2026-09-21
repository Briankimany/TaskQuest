"""Name/path matching helpers for merge import.

Matching rules (locked):
- Normalization: trim + lowercase + collapse interior whitespace, then EXACT match.
- A near match (``difflib.SequenceMatcher.ratio() >= threshold``) is ADVISORY only;
  it never triggers a merge, it only feeds the "near duplicate" notes on the
  preview page.
"""
import re
from difflib import SequenceMatcher

_WS = re.compile(r"\s+")

NEAR_DUPLICATE_THRESHOLD = 0.80


def normalize_name(name):
    """Return the canonical comparison key for a human-facing name."""
    if name is None:
        return ""
    return _WS.sub(" ", str(name).strip().lower())


def same_name(a, b):
    """Exact-match after normalization (the ONLY match that counts)."""
    return normalize_name(a) == normalize_name(b)


def _ratio(a, b):
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def near_duplicate(imported, existing, threshold=NEAR_DUPLICATE_THRESHOLD):
    """Higher-ratio lookalike among ``existing`` to show as an advisory note."""
    imp = normalize_name(imported)
    if not imp:
        return None
    best = None
    for candidate in existing:
        cand = normalize_name(candidate)
        if not cand or cand == imp:
            continue
        ratio = _ratio(imp, cand)
        if ratio >= threshold and (best is None or ratio > best[1]):
            best = (candidate, ratio)
    return best


def norm_time(value):
    """Canonical 'HH:MM' key for a wall-clock time."""
    if value is None:
        return None
    text_value = str(value).strip()
    if ":" not in text_value:
        return text_value.zfill(2) + ":00"
    hour, minute = text_value.split(":")
    return f"{int(hour):02d}:{int(minute):02d}"


def sub_path_key(activity_name, sub_name):
    """(normalized activity, normalized sub) — the canonical sub-activity path."""
    return (normalize_name(activity_name), normalize_name(sub_name))


def entry_key(activity_name, sub_name, start_time):
    """(sub path, HH:MM) — identifies a timetable entry within a day."""
    return (normalize_name(activity_name), normalize_name(sub_name), norm_time(start_time))


def log_key(activity_name, sub_name, completed_on, start_time=None, timetable_date=None):
    """(day, sub path, start_time-if-present[, timetable_date-if-present]).

    Day is the completion day (``completed_on``); a present timetable date and a
    present start time act as extra discriminators per the locked spec.
    """
    return (
        str(completed_on) if completed_on else None,
        normalize_name(activity_name),
        normalize_name(sub_name),
        norm_time(start_time),
        str(timetable_date) if timetable_date else None,
    )