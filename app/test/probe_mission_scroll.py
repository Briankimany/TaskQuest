"""
Playwright probe for the garden-RPG dashboard missions card scroll behaviour.

Reproduces the reported bug: with many tasks (default 15) scheduled for the
current day, mission rows overflow the missions card and the inner list must
scroll so the user can reach lower rows to (un)mark completion.

Reusable as a deploy-pipeline gate: run it against a live server/browser.

Usage (local, uses the repo's instance DB for seeding):
    venv\\Scripts\\python app\\test\\probe_mission_scroll.py
    venv\\Scripts\\python app\\test\\probe_mission_scroll.py --base http://127.0.0.1:5000 --user kim --tasks 15
"""
import argparse
import datetime
import os
import sys

BASE = "http://127.0.0.1:5000"
DEFAULT_USER = "kim"
DEFAULT_PASSWORD = "TestPass123!"
DEFAULT_TASKS = 15


def seed_today_entries(user_name, count, password=DEFAULT_PASSWORD):
    """Insert `count` plain timetable entries for `user_name` today (returns count).

    Also resets the user's password to `password` so the probe can log in cleanly
    against a local dev DB. Pass --no-seed when probing a remote instance that is
    already populated (the password is not touched then).
    """
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, REPO)
    os.chdir(REPO)

    from app import create_app
    from app.models import SubActivity, Timetable, TimetableEntry, User, db
    from app.utils.timezones import now_for

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=user_name).first()
        if user is None:
            raise SystemExit(f"user {user_name!r} not in the local DB")
        user.password = password
        db.session.commit()
        today = now_for(user).date()

        tt = Timetable.query.filter_by(user_id=user.id, date=today).first()
        if tt is None:
            tt = Timetable(user_id=user.id, date=today)
            db.session.add(tt)
            db.session.flush()

        TimetableEntry.query.filter_by(timetable_id=tt.id).delete()

        subs = [s for s in SubActivity.query.all() if s.activity and s.activity.user_id == user.id]
        if not subs:
            raise SystemExit(f"user {user_name!r} has no sub-activities to schedule")
        base = subs[0]
        anchor = datetime.datetime(2020, 1, 1, 8, 0)
        for i in range(count):
            start = (anchor + datetime.timedelta(minutes=15 * i)).time()
            end = (anchor + datetime.timedelta(minutes=15 * (i + 1))).time()
            db.session.add(TimetableEntry(
                timetable_id=tt.id,
                sub_activity_id=base.id,
                start_time=start,
                end_time=end,
                cyclic=False,
                weekday=None,
            ))
        db.session.commit()
        return TimetableEntry.query.filter_by(timetable_id=tt.id).count()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--tasks", type=int, default=DEFAULT_TASKS)
    parser.add_argument("--no-seed", action="store_true",
                        help="skip ORM seeding (for pre-populated remote instances)")
    args = parser.parse_args()

    if not args.no_seed:
        count = seed_today_entries(args.user, args.tasks, args.password)
        print(f"seeded {count} timetable entries today for {args.user}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 900})
        page = ctx.new_page()
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(args.base + "/login", wait_until="networkidle")
        page.fill("#username", args.user)
        page.fill("#password", args.password)
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard", timeout=15000)
        # Server picks the garden template via the cookie, the browser applies the
        # garden CSS via localStorage.theme — set both before rendering the panel.
        ctx.add_cookies([{"name": "app_theme", "value": "garden-rpg", "url": args.base}])
        page.evaluate("localStorage.setItem('theme', 'garden-rpg'); localStorage.setItem('scheme', 'dark');")
        page.goto(args.base + "/dashboard", wait_until="domcontentloaded")
        page.wait_for_selector(".grpg-mission-row", timeout=15000)
        page.wait_for_timeout(800)

        checks = {}

        info = page.evaluate("""() => {
            const list = document.getElementById('grpg-missions-list');
            const rows = list.querySelectorAll('.grpg-mission-row').length;
            const cs = getComputedStyle(list);
            let scrollables = [];
            let el = list;
            while (el) {
                const o = getComputedStyle(el).overflowY;
                if (o === 'auto' || o === 'scroll') {
                    scrollables.push({cls: el.className, id: el.id, overflowY: o,
                        sh: el.scrollHeight, ch: el.clientHeight, st: el.scrollTop});
                }
                el = el.parentElement;
            }
            return { rows, listScrollHeight: list.scrollHeight, listClientHeight: list.clientHeight,
                     listScrollTop: list.scrollTop, listOverflowY: cs.overflowY,
                     listMaxHeight: cs.maxHeight, listScrollbarWidth: cs.scrollbarWidth,
                     scrollables };
        }""")
        print("INFO:", info)

        checks[f">= {args.tasks} missions rendered"] = info["rows"] >= args.tasks
        checks["missions list is an internal scroll container"] = (
            info["listOverflowY"] in ("auto", "scroll") and
            info["listScrollHeight"] > info["listClientHeight"])
        checks["scrollbar is visible (not hidden)"] = (
            info["listScrollbarWidth"] == "thin" or info["listScrollbarWidth"] != "none")
        checks["list flex-fills the card (no fixed max-height cap)"] = (
            info["listMaxHeight"] == "none" or not info["listMaxHeight"].endswith("px"))

        page.locator("#grpg-missions-list").hover()
        for _ in range(20):
            page.mouse.wheel(0, 300)
            page.wait_for_timeout(40)
        after = page.evaluate("""() => {
            const list = document.getElementById('grpg-missions-list');
            const outer = document.querySelector('.grpg-col-right');
            return { listScrollTop: list.scrollTop,
                     outerScrollTop: outer ? outer.scrollTop : -1,
                     pageY: window.scrollY };
        }""")
        print("AFTER WHEEL:", after)
        checks["wheel scrolls the missions list"] = after["listScrollTop"] > 0
        checks["wheel does not steal body scroll"] = after["pageY"] == 0

        last = page.locator(".grpg-mission-row").last
        last.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        try:
            last.click()
            page.wait_for_timeout(500)
            modal = page.query_selector("#grpgCompleteModal")
            checks["last mission is clickable after scrolling"] = modal is not None
            if modal:
                page.locator("#grpgCompleteModal .btn-close").first.click()
                page.wait_for_timeout(300)
        except Exception as exc:
            checks["last mission is clickable after scrolling"] = False
            print("click failed:", exc)

        checks["no page js errors"] = len(page_errors) == 0
        if page_errors:
            print("PAGE ERRORS:", page_errors[:5])

        browser.close()

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