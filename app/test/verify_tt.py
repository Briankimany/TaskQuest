"""Regression verifier for the Timetable "Add New Task" two-column layout.

Boots the Flask app, renders /timetable as user 1, hits the new
/api/timetable/suggestions endpoint, and checks the template/CSS/JS against
the spec: condensed two-column form + "Scheduled Today" (read-only) and
"Suggested" (click-to-prefill) lists, with the submission/overlap pipeline
untouched.

Run from the repo root with the project venv:
    venv\\Scripts\\python.exe app\\test\\verify_tt.py
Exit code is 0 when every check passes, 1 otherwise.
"""

import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

from app import create_app  # noqa: E402

TT_TPL = os.path.join(REPO, "app", "templates", "timetable.html")
TT_CSS = os.path.join(REPO, "app", "static", "css", "timetable.css")
TT_JS = os.path.join(REPO, "app", "static", "js", "tt_script.js")
TT_API = os.path.join(REPO, "app", "routes", "timetable_api.py")
TT_MGR = os.path.join(REPO, "app", "utils", "managers", "timetable_manager.py")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def fragment(src, selector, lim=500):
    idx = src.find(selector)
    return src[idx:idx + lim] if idx != -1 else ""


def main():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    resp = client.get("/timetable")
    html = resp.get_data(as_text=True)
    status = resp.status_code

    sug_resp = client.get("/api/timetable/suggestions")
    sug_json = sug_resp.get_json()

    tpl = read(TT_TPL)
    css = read(TT_CSS)
    js = read(TT_JS)
    api = read(TT_API)
    mgr = read(TT_MGR)

    checks = {}

    # ── Page render ──
    checks["page 200"] = status == 200

    # ── Two-column split markup ──
    checks["tt-split present"] = "tt-split" in tpl and "tt-split-form" in tpl and "tt-form-compact" in tpl
    checks["both suggestion lists present"] = (
        'id="scheduled-today-list"' in tpl and 'id="suggested-list"' in tpl)
    checks["headings labeled"] = "Scheduled Today" in tpl and "Suggested" in tpl
    checks["form keeps every field (id present exactly once)"] = all(
        html.count(f'id="{fid}"') == 1 for fid in (
            "activity-select", "sub-activity", "start-time", "duration",
            "is-cyclic", "weekday-group", "weekday", "add-buffer", "task-description"))

    # ── Field order preserved ──
    order = [tpl.find(f'id="{fid}"') for fid in (
        "activity-select", "sub-activity", "start-time", "duration", "is-cyclic",
        "add-buffer", "task-description")]
    checks["field order unchanged"] = all(a != -1 and a < b for a, b in zip(order, order[1:]))

    # ── CSS ──
    split_css = fragment(css, ".tt-split {", 260)
    checks["grid 1.7fr/1fr"] = "grid-template-columns: 1.7fr 1fr" in split_css
    checks["stack on 768px"] = (
        "@media (max-width: 768px)" in css and
        "grid-template-columns: 1fr" in fragment(css, "@media (max-width: 768px)", 800))
    checks["compact form styles"] = (
        ".tt-form-compact .form-control" in css and ".tt-form-compact .form-select" in css)
    checks["suggestion styles present"] = all(sel in css for sel in (
        ".tt-suggest-block", ".tt-suggest-heading", ".tt-suggest-list",
        ".tt-suggest-empty", ".tt-suggest-item", ".tt-suggest-time",
        ".tt-suggest-readonly", ".tt-suggest-clickable"))
    checks["hidden scrollbars in lists"] = (
        "scrollbar-width: none" in css and "-webkit-scrollbar { display: none; }" in css)
    checks["hover uses existing token"] = "var(--bg-hover" in css

    # ── JS ──
    checks["suggestion fns defined"] = (
        "loadRecurringSuggestions" in js and "renderSuggestionList" in js and "applySuggestion" in js)
    checks["fetches suggestions endpoint per date"] = (
        "fetch('/api/timetable/suggestions?date=' + dateStr)" in js)
    checks["read-only vs clickable classes"] = (
        "tt-suggest-readonly" in js and "tt-suggest-clickable" in js)
    checks["click prefill covers all fields"] = all(f"this.elements.{f}" in fragment(js, "async applySuggestion", 2400)
                                                    for f in ("activitySelect", "subActivitySelect", "startTime",
                                                              "duration", "isCyclic", "weekday", "description"))
    checks["applySuggestion goes through normal sub-select load"] = (
        "this.loadSubActivities(item.activity_id)" in js)
    checks["refresh after save"] = (
        "this.loadRecurringSuggestions();" in js and
        "showNotification('success', 'Saved', 'Task saved successfully');" in js)
    checks["refresh on date picker change"] = (
        "datePicker.addEventListener('change'" in js and "this.loadRecurringSuggestions();" in js)
    checks["empty states defined"] = (
        "No recurring tasks scheduled yet today." in js and
        "All recurring tasks are already scheduled for today." in js)

    # ── Backend ──
    checks["suggestions endpoint defined"] = "/timetable/suggestions" in api and "def recurring_suggestions" in api
    checks["endpoint is read-only (no commit/save)"] = "db.session.commit()" not in fragment(api, "def recurring_suggestions", 3000)
    checks["dedup by (sub_activity_id, start_time)"] = "entry.sub_activity_id, entry.start_time" in api
    checks["weekday filter"] = "TimetableEntry.weekday == weekday" in api and "WeekDay(date_obj.isocalendar().weekday)" in api
    checks["list A/B join is sub_activity_id"] = "today_by_sub" in api and "entry.sub_activity_id" in api
    checks["returns both lists"] = sug_resp.status_code == 200 and "scheduled_today" in sug_json and "suggested" in sug_json
    checks["overlap pipeline untouched"] = (
        "_has_time_conflict" in mgr and "schedule_task" in api and "/timetable/task" in api)

    # ── Payload shape ──
    time_re = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
    if sug_resp.status_code == 200:
        items = sug_json["suggested"] + sug_json["scheduled_today"]
        checks["suggestion fields well-formed"] = all(
            each["activity_id"] and each["sub_activity_id"] and each["activity_name"]
            and (each["weekday"] is None or 1 <= each["weekday"] <= 7)
            and isinstance(each["duration_min"], int) and each["duration_min"] >= 0
            and time_re.match(each["start"]) and time_re.match(each["end"])
            for each in items)
        keys = [(i["sub_activity_id"], i["start"]) for i in sug_json["suggested"]]
        checks["no duplicate suggestions"] = len(set(keys)) == len(keys)

    # ── Collapsible side panel (replaces the modal) ──
    checks["shell + main + panel present"] = all(cls in tpl for cls in (
        'class="tt-shell"', 'class="tt-main"', 'class="tt-panel"'))
    checks["no modal markup left"] = all(x not in tpl for x in (
        "id=\"task-modal\"", "modal-content", "modal-header", "modal-footer",
        "modal-title"))
    checks["panel header has title + close"] = (
        'id="panel-title"' in tpl and 'id="panel-close-btn"' in tpl and
        'id="cancel-btn"' in tpl and 'type="submit"' in tpl)
    checks["toggle button aria wiring"] = (
        'id="add-task-btn"' in tpl and 'aria-expanded="false"' in tpl and
        'aria-controls="task-panel"' in tpl)
    checks["panel panel aria-hidden"] = (
        'aria-hidden="true"' in tpl and 'id="task-panel"' in tpl)
    checks["shell flex layout"] = (
        ".tt-shell {" in css and "display: flex" in fragment(css, ".tt-shell {", 220))
    checks["panel width slide transition"] = (
        "width: 0;" in fragment(css, ".tt-panel {", 300) and
        "transition: width" in css and
        ".tt-shell.tt-panel-open .tt-panel" in css and
        "width: 560px" in css)
    checks["panel stacks below main on small screens"] = (
        "@media (max-width: 992px)" in css and
        ".tt-shell { flex-direction: column; }" in css)
    checks["panel open/close js"] = (
        "setPanelOpen" in js and
        "classList.toggle('tt-panel-open'" in js and
        "aria-expanded" in js and "aria-hidden" in js)
    checks["old modal display refs gone"] = (
        "taskModal" not in js and "modalTitle" not in js)
    checks["open on add, close on cancel/x"] = (
        "panel-close-btn" in js and "closeModal" in js and
        "addTaskBtn.addEventListener" in js)

    failed = [name for name, ok in checks.items() if not ok]
    for name in checks:
        tag = "PASS" if checks[name] else "FAIL"
        print(f"{tag}  {name}")
    print()
    if failed:
        print(f"{len(failed)} CHECKS FAILED: {failed}")
        return 1
    print(f"ALL {len(checks)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())