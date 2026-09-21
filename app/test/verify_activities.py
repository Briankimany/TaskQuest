"""Regression verifier for the Activities page card-list redesign.

Boots the Flask app and verifies that the activities page is a collapsible
card list (no `<table>` anywhere), with persisted collapse state and the CRUD
surface unchanged: New Activity, per-group Sub/edit/delete, per-row
edit/delete, attribute badges, modals, empty groups.

Classes are namespaced `act-*` so they never collide with the Tasks page's
existing `.activity-group*` styles or the `.table-app` tables used elsewhere.

Run from the repo root with the project venv:
    venv\\Scripts\\python.exe app\\test\\verify_activities.py
Exit code is 0 when every check passes, 1 otherwise.
"""

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

from app import create_app  # noqa: E402

ACT_TPL = os.path.join(REPO, "app", "templates", "activities.html")
ACT_CSS = os.path.join(REPO, "app", "static", "css", "activities.css")
ACT_JS = os.path.join(REPO, "app", "static", "js", "activities.js")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    resp = client.get("/activities")
    html = resp.get_data(as_text=True)
    status = resp.status_code

    tpl = read(ACT_TPL)
    css = read(ACT_CSS)
    js = read(ACT_JS)

    checks = {}

    # ── Page renders ──
    checks["activities page renders 200"] = status == 200
    checks["page has activities container"] = 'id="activities-container"' in html
    checks["styles block loads activities.css"] = 'css/activities.css' in tpl and "{% block styles %}" in tpl

    # ── No tables ──
    checks["no <table> in template"] = "<table" not in tpl
    checks["no </table> in template"] = "</table" not in tpl
    checks["no table-app class in template"] = "table-app" not in tpl
    checks["no thead/tbody/tr/td in template"] = not any(x in tpl for x in ("<thead", "<tbody", "<tr", "<td"))
    checks["no table-app references in JS"] = "table-app" not in js

    # ── Card-list structure (namespaced act-*) ──
    checks["group card present"] = "act-group" in tpl
    checks["group carries data-id"] = 'act-group mb-3" data-id="' in tpl
    checks["group carries data-group-name"] = "data-group-name=" in tpl
    checks["header role=button + aria-expanded"] = (
        'class="act-group-header" role="button" tabindex="0" aria-expanded="false"' in tpl)
    checks["chevron present"] = "lucide-chevron-right" in tpl and "chevron" in css
    checks["count badge present"] = 'class="count"' in tpl
    checks["collapsible body"] = 'class="act-group-body"' in tpl
    checks["app-card-header only on page card"] = tpl.count("app-card-header") == 1
    checks["row structure"] = 'class="act-row" data-id="' in tpl
    checks["row name/meta/attributes/actions"] = (
        'class="activity-name name"' in tpl and
        'class="meta font-mono"' in tpl and
        'class="attributes"' in tpl and
        'class="actions"' in tpl)
    checks["no inline badge widths (CSS override)"] = 'style="width:28px' not in tpl
    checks["data-attributes is valid JSON attr"] = "data-attributes='{{ sub.attribute_weights|tojson }}" in tpl
    checks["row edit button labeled Edit"] = (
        'edit-subactivity-btn' in tpl and '</i> Edit' in tpl and
        'title="Edit sub-activity"' in tpl)
    checks["row delete button titled"] = (
        'delete-subactivity-btn' in tpl and 'title="Delete sub-activity"' in tpl)
    checks["group edit button labeled Edit"] = (
        'edit-activity-btn' in tpl and '</i> Edit' in tpl and
        'title="Edit activity name"' in tpl)
    checks["add sub-activity labeled + titled"] = (
        'add-subactivity-btn' in tpl and 'Add Sub-Activity' in tpl and
        'title="Add a sub-activity to this activity"' in tpl)
    checks["dark-mode secondary button contrast"] = (
        '[data-theme="default"][data-scheme="dark"] .btn-app-secondary' in read(
            os.path.join(REPO, "app", "static", "css", "buttons.css")))
    checks["empty group placeholder kept"] = "No sub-activities yet" in tpl
    checks["empty list state kept"] = "Create Your First Activity" in tpl

    # ── No collision with Tasks page .activity-group* ──
    checks["no tasks .activity-group names in template"] = "activity-group" not in tpl
    checks["no tasks .activity-group names in CSS"] = "activity-group" not in css
    checks["no tasks .activity-group names in JS"] = "activity-group" not in js
    checks["no generic .activity-row names in JS"] = "activity-row" not in js

    # ── CRUD surface unchanged ──
    for label, needle in [
        ("new activity button", "create-activity-btn"),
        ("new activity modal", 'id="newActivityModal"'),
        ("add-subactivity button", "add-subactivity-btn"),
        ("edit-activity button", "edit-activity-btn"),
        ("delete-activity button", "delete-activity-btn"),
        ("edit-subactivity button", "edit-subactivity-btn"),
        ("delete-subactivity button", "delete-subactivity-btn"),
        ("edit modal", 'id="editSubActivityModal"'),
        ("delete confirm modal", 'id="deleteConfirmModal"'),
        ("attr badges with tooltips", 'attr-badge-' in tpl and 'data-bs-toggle="tooltip"'),
    ]:
        checks[label] = needle in tpl

    # ── CSS: collapse animation + compact rows ──
    checks["body collapses via max-height"] = (
        ".act-group-body {" in css and "max-height: 0;" in css and
        "transition: max-height 220ms ease" in css)
    checks["body has no padding leak"] = ".act-group-body { padding" not in css
    checks["chevron rotates on expand"] = (
        ".act-group.is-expanded .chevron" in css and "rotate(90deg)" in css)
    checks["header compact + hoverfeedback"] = (
        ".act-group-header {" in css and "padding: 14px 20px" in css and
        "cursor: pointer" in css and "var(--bg-hover)" in css)
    checks["row compact + dividers"] = (
        ".act-row {" in css and "padding: 8px 20px" in css and
        "border-top: 1px solid var(--border)" in css)
    checks["group actions flush right"] = (
        ".act-group-header .actions {" in css and "margin-left: auto" in css)
    checks["row actions flush right"] = (
        ".act-row .actions {" in css and "margin-left: auto" in css)
    checks["compact badges in rows"] = (
        ".act-row .attr-badge {" in css and "width: 26px" in css and "height: 26px" in css)
    checks["card uses default-theme tokens"] = (
        "var(--card-bg)" in css and "var(--card-border)" in css and
        "var(--radius-md)" in css)

    # ── JS: selectors re-pointed + collapse logic ──
    checks["no table-coupled selectors remain"] = not any(x in js for x in (
        "closest('tr')", "td:first-child", "activity-card", "closest('.app-card')"))
    checks["group selectors used"] = ".act-group" in js and ".act-row" in js
    checks["collapse toggle present"] = "toggleGroup" in js and "classList.toggle('is-expanded')" in js
    checks["localStorage persistence"] = "localStorage.setItem" in js and "localStorage.getItem" in js and ".expanded" in js
    checks["persist key uses group name"] = "data-group-name" in js and "groupKey" in js
    checks["height sync on state change"] = "scrollHeight" in js and "syncHeight" in js
    checks["action clicks dont toggle"] = "closest('.actions')" in js
    checks["keyboard toggle"] = "keydown" in js and "aria-expanded" in js
    checks["row delete name lookup"] = "closest('.act-row').querySelector('.name')" in js
    checks["group delete name lookup"] = "closest('.act-group').querySelector('.name')" in js
    checks["update name uses group"] = ".act-group[data-id=" in js

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