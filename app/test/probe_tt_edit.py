"""Playwright probe for the Timetable Edit prefill behaviour.

The bug: clicking Edit on a task opened the panel with an EMPTY Activity and
Sub-Activity dropdown and no description, because /api/timetable/info returned
entries via TimetableEntry.to_dict() which lacked sub_activity_id, activity_id
and description, and openEditModal never pinned/reloaded the parent activity.

This probe drives the real flow (schedule via the API, then Edit in the UI) and
asserts the panel is fully pre-populated. Reusable as a deploy-pipeline gate.

Usage (local dev DB / live server, no ORM needed — goes entirely over HTTP):
    venv\\Scripts\\python app\\test\\probe_tt_edit.py
    venv\\Scripts\\python app\\test\\probe_tt_edit.py --base http://127.0.0.1:5000 --user kim
"""
import argparse
import datetime
import json
import sys
import uuid

BASE = "http://127.0.0.1:5000"
DEFAULT_USER = "kim"
DEFAULT_PASSWORD = "TestPass123!"
START_TIME = "02:30"
DESCRIPTION = "probe-edit-desc-" + uuid.uuid4().hex[:8]


def login(base, user, password):
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + "/login", wait_until="networkidle")
    page.fill("#username", user)
    page.fill("#password", password)
    page.click("button[type=submit]")
    page.wait_for_url("**/dashboard", timeout=15000)
    return p, browser, ctx, page, errors


def find_free_slot(info_payload):
    """Pick a 30-minute start slot free of existing tasks for the day.

    Repeated probe runs must not collide with entries left behind by earlier
    runs, so the slot is derived from the live schedule instead of a constant.
    """
    def minutes(s):
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    busy = []
    for entries in (info_payload or {}).get("schedule", {}).values():
        for e in entries:
            busy.append((minutes(e["start_time"][:5]), minutes(e["end_time"][:5])))
    busy.sort()
    for start in range(0, 24 * 60 - 30, 30):
        take = True
        for s, e in busy:
            if start < e and start + 30 > s:
                take = False
                break
        if take:
            return f"{start // 60:02d}:{start % 60:02d}"
    return "02:30"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    p, browser, ctx, page, errors = login(args.base, args.user, args.password)

    checks = {}

    def api(method, path, payload=None):
        url = args.base + path
        response = page.request.fetch(
            url, method=method,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload) if payload else None)
        return response

    # 1. Discover a real (activity, sub-activity) owned by the user.
    sched = api("GET", "/api/timetable/scheduling/tasks").json()
    activities = sched.get("suggested_activities", []) + sched.get("new_activities", [])
    checks["scheduling/tasks returns activities"] = len(activities) > 0
    activity = next((a for a in activities if a.get("id")), activities[0])
    acts_resp = api("GET", f"/api/activities?id={activity['id']}")
    acts = acts_resp.json().get("activities", [])
    subs = [s for a in acts for s in a.get("sub_activities", [])]
    checks["activities endpoint returns sub-activities"] = len(subs) > 0
    sub = subs[0]

    # 2. Ensure a timetable exists for today, then schedule a task with a description.
    today = datetime.date.today().isoformat()
    tt = api("POST", "/api/timetable/create", {"date": today})
    if tt.status not in (200, 201, 409):
        # Some instances reuse an existing timetable; try creating fresh only once.
        tt = api("POST", "/api/timetable/create", {"date": today})
    info_payload = api("GET", f"/api/timetable/info/{today}?days=1").json()
    start_time = find_free_slot(info_payload)
    print(f"scheduling at {start_time} (auto-picked free slot)")
    created = api("POST", "/api/timetable/task", {
        "sub_activity_id": sub["id"],
        "date": today,
        "start_time": start_time,
        "time_zone": "Asia/Kolkata",
        "task_duration": 30,
        "cyclic": False,
        "weekday": None,
        "create_buffer": False,
        "description": DESCRIPTION,
    })
    checks["schedule task created"] = created.status == 201
    created_main = (created.json() or {}).get("main_task", created.json() or {})
    checks["schedule payload echoes sub_activity_id"] = (
        created_main.get("sub_activity_id") == sub["id"])
    checks["schedule payload echoes description"] = (
        created_main.get("description") == DESCRIPTION)

    # 3. Open /timetable, click Edit on our task, assert prefill.
    page.goto(args.base + "/timetable", wait_until="domcontentloaded")
    page.wait_for_selector(".task-card", timeout=15000)
    page.wait_for_timeout(600)

    cards = page.locator(".task-card")
    found = False
    for i in range(cards.count()):
        text = cards.nth(i).inner_text()
        if DESCRIPTION in text or start_time in text:
            cards.nth(i).locator(".edit-btn").click()
            found = True
            break
    checks["edit button clickable"] = found

    if found:
        # openEditModal is async (it awaits loadSubActivities before filling the
        # description/start inputs), so poll until the prefill settles instead of
        # sampling at a fixed delay.
        try:
            page.wait_for_function(
                "args => document.getElementById('task-description').value === args.desc",
                arg={"desc": DESCRIPTION}, timeout=15000)
        except Exception as exc:
            print("prefill wait error:", exc)
        page.wait_for_timeout(200)
        panel = page.locator("#task-panel")
        checks["edit panel opens"] = panel.evaluate("el => el.dataset.open === 'true'")
        checks["panel title = Edit Task"] = (
            page.locator("#panel-title").inner_text().strip() == "Edit Task")
        checks["activity pre-populated"] = (
            page.locator("#activity-select").input_value() == str(activity["id"]))
        checks["sub-activity pre-populated"] = (
            page.locator("#sub-activity").input_value() == str(sub["id"]))
        checks["description pre-populated"] = (
            page.locator("#task-description").input_value() == DESCRIPTION)
        checks["start time pre-populated"] = (
            page.locator("#start-time").input_value() == start_time)
        checks["duration pre-populated (30 min)"] = (
            page.locator("#duration").input_value() in ("30", "0.5"))

    checks["no page js errors"] = len(errors) == 0
    if errors:
        print("PAGE ERRORS:", errors[:5])

    # Cleanup: drop the probe row so repeated runs stay idempotent.
    if created_main.get("id"):
        api("DELETE", f"/api/timetable/task/{created_main['id']}")

    page.close()
    browser.close()
    p.stop()

    failed = [k for k, v in checks.items() if not v]
    for k, v in checks.items():
        print(("PASS" if v else "FAIL") + "  " + k)
    print()
    if failed:
        print("PROBE FAILURES: " + ", ".join(failed))
        sys.exit(1)
    print("ALL %d PROBE CHECKS PASSED" % len(checks))


if __name__ == "__main__":
    main()