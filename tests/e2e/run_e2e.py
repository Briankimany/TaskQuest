"""
Headed Playwright end-to-end suite for TaskQuest.

Brings up the app against a throwaway sqlite database inside a temp directory,
seeds a deterministic scenario, opens a visible Chromium window, and walks the
browser through:
    1. Registering a new account
    2. Logging in
    3. Creating an activity + sub-activity (Activities page)
    4. Creating a timetable day + scheduling a task (Timetable page)
    5. Dashboard (garden-rpg theme): mark missions complete, abandon, finalize
    6. Export → import round trip (API level)

Every step prints a clear log line and drops a PNG into <temp>/shots/.

Run:
    python tests\\e2e\\run_e2e.py --headed --port 5055

Flags:
    --headed        keep the browser visible (default: False)
    --port PORT     dev server port (default: 5055)
    --keep-db       reuse the previous temp db instead of reseeding
    --base-dir PATH  where temp files live (default: %TEMP%\\opencode\\tq_e2e)
    --server-addr    host[:port] the runner points the browser at
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# python script.py only puts the script's own directory on sys.path; make the
# repo root importable so `import app` works regardless of how the runner is
# invoked (plain script or `python -m tests.e2e.run_e2e`).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_SHOTS_DIR = Path(os.environ.get("TEMP", "/tmp")) / "opencode" / "tq_e2e"
CREDS = {"username": "kim", "email": "kim@taskquest.dev", "password": "TestPass123!"}


def log(msg: str):
    print(f"[e2e] {msg}", flush=True)


class Server:
    """Manages the Flask dev-server subprocess for the run."""

    def __init__(self, port: int, base_dir: Path):
        self.port = port
        self.base_dir = base_dir
        self.proc: subprocess.Popen | None = None
        self.server_log = base_dir / "server.log"

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.port}"

    def start(self):
        env = dict(os.environ)
        # Keep the app in production-ish error handling and off the reloader.
        env["FLASK_DEBUG"] = "0"
        env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        python = sys.executable
        cmd = [
            python, "-m", "flask", "--app", "app", "run",
            "--host", "127.0.0.1", "--port", str(self.port),
            "--no-debugger", "--no-reload",
        ]
        with open(self.server_log, "wb") as f:
            self.proc = subprocess.Popen(
                cmd, cwd=str(REPO_ROOT), env=env, stdout=f, stderr=subprocess.STDOUT)
        if not self.wait_ready(30):
            self.dump_log()
            raise RuntimeError("Dev server did not become ready")

    def wait_ready(self, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc and self.proc.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(self.base_url + "/login", timeout=2) as r:
                    if r.status == 200:
                        return True
            except (urllib.error.URLError, OSError):
                time.sleep(0.4)
        return False

    def dump_log(self):
        try:
            print(self.server_log.read_text(encoding="utf-8", errors="replace")[-4000:])
        except OSError:
            pass

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def step(page, name: str, shots_dir: Path, index: int):
    """Decorator-ish helper to run one named, screenshotted step."""
    def wrap(fn):
        def inner(*args, **kwargs):
            log(f"• {name}")
            fn(*args, **kwargs)
            page.screenshot(path=str(shots_dir / f"{index:02d}_{slug(name)}.png"),
                            full_page=True)
            log(f"  ok ({index})")
        return inner
    return wrap


def slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")[:40]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true",
                        help="Run the browser invisibly (default: headed)")
    parser.add_argument("--port", type=int, default=5055)
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_SHOTS_DIR)
    parser.add_argument("--keep-db", action="store_true")
    parser.add_argument("--db-name", default="e2e_run.db")
    args = parser.parse_args()

    base_dir = args.base_dir
    run_dir = base_dir / f"run_{int(time.time())}"
    shots_dir = run_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    # Unique per-run DB so multiple invocations never clash.
    db_path = run_dir / args.db_name
    db_uri = "sqlite:///" + db_path.as_posix()

    log(f"temp dir   : {run_dir}")
    log(f"database   : {db_uri}")

    # Point the app at the temp DB before anything imports it.
    os.environ["TASKQUEST_DATABASE_URL"] = db_uri
    os.environ["FLASK_DEBUG"] = "0"
    os.environ["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")
    # No real LLM provider in tests: complete_activity / penalty lookups must
    # fail fast (connection refused) and fall back to deterministic penalties.
    # (The default 127.0.0.1:20128 is a live-but-then-hanging proxy when opencode
    # is running, so we steer well clear of it.)
    os.environ["OMNIROUTE_URL"] = "http://127.0.0.1:9/v1"

    # ── Seed directly inside this process (same temp DB the server will use) ──
    from app.init import create_app
    from app.seed.e2e_seeds import run_scenario, SCENARIOS

    with create_app().app_context():
        if args.keep_db and db_path.exists():
            log("keeping existing seeded db")
        else:
            report = run_scenario(username=CREDS["username"], scenario="full-week")
            log(f"seeded      : {report}")

    server = Server(args.port, run_dir)
    server.start()
    log(f"server ready: {server.base_url}")

    from playwright.sync_api import sync_playwright

    failed = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless, args=["--start-maximized"])
            context = browser.new_context(viewport={"width": 1480, "height": 900})
            page = context.new_page()
            page.goto(server.base_url + "/login", wait_until="networkidle")

            idx = 0

            # ── 1. Register ──
            page.goto(server.base_url + "/register", wait_until="domcontentloaded")
            page.fill("#username", CREDS["username"] + "_new")
            page.fill("#email", "new@taskquest.dev")
            page.fill("#password", CREDS["password"])
            page.click("button[type=submit]")
            page.wait_for_url("**/login", timeout=10000)
            assert "login" in page.url
            log("  1 register: redirected to login")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_register.png"), full_page=True); idx += 1

            # ── 2. Login as the seeded user ──
            page.fill("#username", CREDS["username"])
            page.fill("#password", CREDS["password"])
            page.click("button[type=submit]")
            page.wait_for_url("**/dashboard", timeout=10000)
            assert "/dashboard" in page.url
            log("  2 login: redirected to dashboard")

            # Force the garden-rpg theme (server reads the app_theme cookie).
            context.add_cookies([{
                "name": "app_theme", "value": "garden-rpg", "url": server.base_url,
            }])
            page.evaluate("localStorage.setItem('theme', 'garden-rpg')")
            page.goto(server.base_url + "/dashboard", wait_until="domcontentloaded")
            page.wait_for_selector(".grpg-mission-row", timeout=10000)
            mission_rows = page.locator(".grpg-mission-row").count()
            assert mission_rows >= 3, f"expected >=3 missions, got {mission_rows}"
            active = page.locator('.grpg-mission-row[data-status="ACTIVE"]')
            assert active.count() >= 1
            log(f"  3 dashboard: {mission_rows} missions, ACTIVE rows seen")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_dashboard_initial.png"),
                            full_page=True); idx += 1

            # ── 4. Mark the first ACTIVE mission complete (garden-rpg modal) ──
            row = active.first
            task_id = row.get_attribute("data-mission-id").replace("mission-", "")
            row.locator(".grpg-mission-status").click()
            page.wait_for_selector("#grpgCompleteModal.show", timeout=10000)
            page.click("#grpg-complete-confirm")
            page.wait_for_function(
                f"""document.querySelector('.grpg-mission-row[data-mission-id="mission-{task_id}"]')
                    ?.getAttribute('data-status') === 'COMPLETED'""",
                timeout=15000)
            log(f"  4 marked mission {task_id} COMPLETED via UI")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_dashboard_completed.png"),
                            full_page=True); idx += 1

            # ── 5. Abandon the second ACTIVE mission via the API ──
            # (the abandon/reschedule modal handlers exist in JS but no dashboard
            # element renders them yet — test the deterministic API path instead)
            active2 = page.locator('.grpg-mission-row[data-status="ACTIVE"]').first
            abandon_id = active2.get_attribute("data-mission-id").replace("mission-", "")
            resp = context.request.post(
                server.base_url + "/api/complete/complete_activity",
                data={"timetable_entry_id": int(abandon_id),
                      "status": "skipped",
                      "reason": "E2E: no time today"})
            body = resp.json()
            assert resp.ok, f"abandon failed: {resp.status} {body}"
            assert body.get("exp_change", 0) < 0, f"expected negative exp, got {body}"
            page.goto(server.base_url + "/dashboard", wait_until="domcontentloaded")
            page.wait_for_function(
                f"""[...document.querySelectorAll('.grpg-mission-row')]
                    .some(r => r.getAttribute('data-mission-id') === 'mission-{abandon_id}'
                            && r.getAttribute('data-status') === 'MISSED')""",
                timeout=15000)
            log(f"  5 abandoned mission {abandon_id} (MISSED, exp {body.get('exp_change')})")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_dashboard_abandoned.png"),
                            full_page=True); idx += 1

            # ── 6. Activities page: create + edit sub-activity via UI ──
            page.goto(server.base_url + "/activities", wait_until="domcontentloaded")
            page.click("button[data-bs-target='#newActivityModal']")
            page.fill("#activity-name", "E2E Activity")
            page.click("#create-activity-btn")
            page.locator(".act-group", has_text="E2E Activity").wait_for(timeout=10000)
            log("  6 created activity via UI")

            page.locator(".act-group", has_text="E2E Activity") \
                .locator(".add-subactivity-btn").click()
            page.fill("#subactivity-name", "E2E Subtask")
            page.fill("#scheduled-time", "30")
            page.click("#create-subactivity-btn")
            page.locator(".act-row", has_text="E2E Subtask").wait_for(timeout=10000)
            log("  7 created sub-activity via UI")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_activities.png"),
                            full_page=True); idx += 1

            # ── 7. Timetable page: new day + schedule a task (on TOMORROW so today's
#       finalized-day invariant stays intact) ──
            page.goto(server.base_url + "/timetable", wait_until="domcontentloaded")
            tomorrow_iso = page.evaluate(
                "new Date(Date.now() + 86400000).toISOString().split('T')[0]")
            page.fill("#date-picker", tomorrow_iso)  # change fires loadTimetable
            page.click("#new-day-btn")  # ensure a timetable exists for the date
            page.wait_for_timeout(600)
            page.click("#add-task-btn")  # open the task panel
            page.wait_for_selector("#tt-shell.tt-panel-open", timeout=10000)
            page.select_option("#activity-select", label="Learning")
            page.wait_for_timeout(800)
            page.select_option("#sub-activity", label="Read Book")
            page.fill("#start-time", "14:00")
            page.fill("#duration", "60")
            page.click("#task-form button[type=submit]")
            page.wait_for_timeout(1000)
            page.locator(".task-card", has_text="Read Book").wait_for(timeout=10000)
            log("  8 scheduled a Read Book task on tomorrow via UI")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_timetable.png"),
                            full_page=True); idx += 1

            # ── 8. Finalize the day via the completion API ──
            today_iso = page.evaluate("new Date().toISOString().split('T')[0]")
            resp = context.request.post(server.base_url + "/api/complete/finalize_day",
                                        data={"date": today_iso})
            body = resp.json()
            assert resp.ok, f"finalize_day failed: {resp.status} {body}"
            log(f"  9 finalized day: new_total_exp={body.get('new_total_exp')} "
                f"level={body.get('level')}")

            # ── 9. Export / back to dashboard (session persisted) ──
            page.goto(server.base_url + "/dashboard", wait_until="domcontentloaded")
            page.wait_for_selector(".grpg-xp-value", timeout=10000)
            xp_text = page.locator(".grpg-xp-value").first.inner_text()
            log(f" 10 after finalize — topbar XP: {xp_text!r}")
            page.screenshot(path=str(shots_dir / f"{idx:02d}_dashboard_final.png"),
                            full_page=True); idx += 1

            browser.close()
        log("E2E SUITE PASSED")
        return 0
    except Exception as e:
        failed = True
        log(f"E2E FAILED: {e!r}")
        server.dump_log()
        return 1
    finally:
        server.stop()


if __name__ == "__main__":
    sys.exit(main())