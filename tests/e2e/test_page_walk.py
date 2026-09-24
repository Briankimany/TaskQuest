"""Playwright walk-through against the already-running local dev server.

Logs in as an existing user (kim / 1234), clicks through every page the app
serves, and logs out again. Uses the local database (instance/rpg_system.db).

Run (dev server must already be running on port 5000):

    venv\\Scripts\\python -m pytest tests\\e2e\\test_page_walk.py --headed
"""
import pytest

CREDS = {"username": "kim", "password": "1234"}

# Every user-facing GET page the app serves. The page is considered reachable
# when it returns HTTP 200 and does not bounce us back to /login (which is what
# an expired/absent session does on members-only routes).
PAGES = [
    "/",
    "/dashboard",
    "/activities",
    "/timetable",
    "/stats",
    "/garden",
    "/journal",
    "/chat",
    "/judge-log",
    "/shop",
    "/help",
    "/docs",
    "/profile",
]


def test_existing_user_walks_all_pages_and_logs_out(page, context, base_url):
    # ── Login as the existing user ──
    page.goto(base_url + "/login", wait_until="domcontentloaded")
    page.fill("#username", CREDS["username"])
    page.fill("#password", CREDS["password"])
    page.click("button[type=submit]")
    page.wait_for_url("**/dashboard", timeout=15000)
    assert "/dashboard" in page.url

    # ── Visit every page ──
    visited = []
    for path in PAGES:
        resp = page.goto(base_url + path, wait_until="domcontentloaded")
        assert resp is not None, f"{path} returned no response"
        assert resp.status == 200, (
            f"{path} returned {resp.status}"
            f"{'' if resp.status != 500 else ' (server error)'}")
        assert "/login" not in page.url, f"{path} bounced back to /login"
        visited.append(f"{path} [{resp.status}]")
    print("pages ok:", ", ".join(visited))

    # /export streams a JSON download, so Playwright can't navigate to it;
    # check it through the browser context's request API (session cookie kept).
    export = context.request.get(base_url + "/export")
    assert export.ok, f"/export returned {export.status}"
    export.json()  # parses -> it is valid JSON export data
    visited.append("/export [download via request API]")
    print("export ok")

    # ── Logout via the UI link (base2.html topbar) ──
    page.goto(base_url + "/dashboard", wait_until="domcontentloaded")
    logout_link = page.locator('a[href="/logout"]')
    if logout_link.count():
        logout_link.first.click()
        page.wait_for_url("**/login", timeout=15000)
    else:
        page.goto(base_url + "/logout", wait_until="domcontentloaded")
        page.wait_for_url("**/login", timeout=15000)
    assert "/login" in page.url

    # Session must be gone: a members-only page now redirects to /login.
    page.goto(base_url + "/dashboard", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15000)
    assert "/login" in page.url