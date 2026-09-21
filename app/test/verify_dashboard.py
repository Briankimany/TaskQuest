"""Regression verifier for the Garden RPG dashboard skin.

Boots the Flask app, renders /dashboard as user 1, and checks the theme,
layout, topbar, overlay cards, and dashboard JS against the canonical spec.

Run from the repo root with the project venv:
    venv\\Scripts\\python.exe app\\test\\verify_dashboard.py
Exit code is 0 when every check passes, 1 otherwise.
"""

import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

from app import create_app  # noqa: E402

CORE = os.path.join(REPO, "app", "static", "css", "theme-garden-rpg.css")
LAYOUT = os.path.join(REPO, "app", "static", "css", "layout-garden-rpg.css")
JS = os.path.join(REPO, "app", "static", "js", "dashboard-garden-rpg.js")
HERO = os.path.join(REPO, "app", "templates", "partials", "_hero_garden.html")
TOPBAR_TPL = os.path.join(REPO, "app", "templates", "partials", "_topbar_garden_rpg.html")
BOTTOM_ROW = os.path.join(REPO, "app", "templates", "partials", "_bottom_stat_row.html")

DEPRECATED = [
    "#4FC3F7", "#3AB6F0", "#F58FBE", "#F78FB3", "#98E391", "#A5DC86",
    "#A58FE0", "#B79CED", "#F0C75E", "#FFE082", "#0B1622", "#1C2836",
    "#2A3D4C", "#111C28",
]


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
    resp = client.get("/dashboard", follow_redirects=True)
    html = resp.get_data(as_text=True)
    status = resp.status_code

    theme = read(CORE)
    layout = read(LAYOUT)
    js = read(JS)
    hero = read(HERO)
    topbar_tpl = read(TOPBAR_TPL)
    bottom_row = read(BOTTOM_ROW)

    checks = {}

    # ── Page render ──
    checks["page 200"] = status == 200

    # ── Unicode hygiene ──
    checks["no text flower glyphs"] = "\u273f" not in html
    checks["no lock emoji"] = "\U0001f512" not in html
    checks["template flower icons are svg (no fill=var)"] = 'fill="var(' not in hero
    checks["no mission unicode glyphs in template"] = all(
        ent not in html for ent in ("x2713", "x23F0", "x2717", "x2716", "x23F1")
    )
    checks["no unicode glyphs in dashboard JS"] = all(
        ch not in js for ch in ("\u2713", "\u2717", "\u23f0", "\u23f1")
    )

    # ── Canonical tokens ──
    checks["spirit tokens: cyan family"] = all(t in theme for t in (
        "--cyan-muted: #147A96", "--cyan: #1CAED5", "--cyan-bright: #31D2F2"))
    checks["spirit tokens: pink family"] = all(t in theme for t in (
        "--pink-muted: #9D4D60", "--pink: #E36C83", "--pink-bright: #F28FA0"))
    checks["spirit tokens: purple/gold/success"] = all(t in theme for t in (
        "--purple: #9B7FE8", "--gold: #E9A83D", "--success: #39C979"))
    checks["surface ui-bg 0..3 blue-black"] = all(t in theme for t in (
        "--ui-bg-0: #01060F", "--ui-bg-1: #050D16",
        "--ui-bg-2: #07131C", "--ui-bg-3: #0A1821"))
    checks["nav active maroon pill"] = "--nav-active: #7A1F2B" in theme and "--nav-active-hover: #8C2635" in theme
    checks["no deprecated hexes in src"] = all(h not in theme and h not in layout and h not in js for h in DEPRECATED)

    # ── Panel depth model ──
    checks["panel layered depth bg"] = (
        "radial-gradient(circle at 12% 8%" in layout and "rgba(7,19,28,0.90)" in layout)
    checks["panel 1px border-neutral"] = "border: 1px solid var(--border-neutral)" in layout
    checks["panel depth shadow"] = "inset 0 1px 0 rgba(255,255,255,0.03)" in layout and "0 8px 24px rgba(0,0,0,0.32)" in layout
    checks["surface variants defined"] = all(
        ".grpg-surface--" + f in layout for f in ("cyan", "pink", "gold"))
    checks["hover border only"] = ".grpg-panel:hover" in layout and ".grpg-overlay-card:hover" not in layout

    # ── Status circles (precision spec) ──
    checks["mission circle 18px 50%"] = "width: 18px;" in fragment(layout, ".grpg-mission-status {", 260) and "border-radius: 50%" in fragment(layout, ".grpg-mission-status {", 260)
    checks["mission incomplete tag border"] = "border: 2px solid var(--tag-color" in layout
    checks["mission done success fill"] = "background: var(--success)" in fragment(layout, ".grpg-mission-row[data-done=\"true\"] .grpg-mission-status {", 200)
    checks["svg check data-uri (stroke ui-bg-1)"] = "M1 4L3.5 6.5L9 1" in layout and "%23050D16" in layout

    # ── XP bar / count pill / bar track ──
    checks["xp-bar cyan gradient + glow"] = "linear-gradient(90deg, var(--cyan), var(--cyan-bright))" in layout
    checks["count pill neutral surface"] = "grpg-count-pill" in layout
    checks["bar track translucent"] = "background: rgba(20, 38, 47, 0.70)" in layout

    # ── Garden status ──
    garden_status = read(os.path.join(REPO, "app", "templates", "partials", "_garden_status_panel.html"))
    checks["garden ring pink->cyan gradient"] = "var(--pink)" in garden_status and "var(--cyan)" in garden_status
    checks["tree canonical pink canopy"] = "var(--pink-muted)" in garden_status

    # ── Relative-anchor system: overlay full-bleed + var-derived center lane ──
    dash_tpl = read(os.path.join(REPO, "app", "templates", "dashboard_garden_rpg.html"))
    checks["center-cell spacer removed (no .grpg-hero)"] = (
        ".grpg-hero {" not in layout and
        'class="grpg-hero"' not in dash_tpl and
        "grpg-hero\"" not in dash_tpl)
    checks["overlay full-bleed absolute"] = (
        "position: absolute" in fragment(layout, "[data-theme=\"garden-rpg\"] .grpg-hero-overlay {", 300) and
        "inset: 0" in fragment(layout, "[data-theme=\"garden-rpg\"] .grpg-hero-overlay {", 300))
    checks["column widths are single-source vars"] = (
        "--col-l: 330px" in layout and "--col-r: 380px" in layout and
        "grid-template-columns: var(--col-l) 1fr var(--col-r)" in layout)
    checks["overlay row tracks center cell via vars"] = "bottom: 26px" not in layout
    checks["right col hidden re-tracks vars (1100px)"] = (
        "--col-l: 280px" in layout and "--col-r: 0px" in layout and
        "grid-template-columns: var(--col-l) 1fr var(--col-r)" in layout)
    checks["single column zeroes vars (900px)"] = (
        "--col-l: 0px" in fragment(layout, "max-width: 900px", 4000) and
        "--col-r: 0px" in fragment(layout, "max-width: 900px", 4000))
    checks["night-mode overlay retargeted"] = ".grpg-hero-overlay::after" in layout

    # ── Petals/Seeds cards removed ──
    checks["no overlay card classes in hero"] = (
        "grpg-overlay-card" not in hero and "grpg-overlay-row" not in hero and
        "grpg-surface--seed" not in hero and "grpg-petals-list" not in hero and
        "left:681px" not in hero and "left:1008px" not in hero)
    checks["no overlay card css remains"] = (
        "grpg-overlay-card" not in layout and "grpg-overlay-row" not in layout and
        "grpg-overlay-ring" not in layout and "grpg-check-toggle" not in layout and
        "grpg-check-row" not in layout and "grpg-lock-row" not in layout and
        "grpg-scroll-list" in layout)
    checks["no petals/seeds js remains"] = (
        "syncPetals" not in js and "grpg-petals-list" not in js and
        "anchor(--river-anchor" not in js)

    # ── Loc markers ──
    checks["loc-card rounded no clip-path"] = "clip-path" not in fragment(layout, "\n[data-theme=\"garden-rpg\"] .grpg-loc-card {", 400) and "border-radius: var(--radius-sm)" in fragment(layout, "\n[data-theme=\"garden-rpg\"] .grpg-loc-card {", 400)
    checks["loc-card glow dot"] = "0 0 10px 2px" in fragment(layout, ".grpg-loc-dot", 200) and "border-radius: 50%" in fragment(layout, ".grpg-loc-dot", 200)

    # ── Recent Activity rows: no status label ──
    checks["activity rows have no status label (tpl)"] = "IN PROGRESS" not in bottom_row and "act.status" not in bottom_row
    checks["activity rows have no status label (js)"] = "stLabel" not in js and "IN PROGRESS" not in js

    # ── System Judge removed from dashboard ──
    checks["no judge include in dashboard"] = (
        "_system_judge_panel" not in dash_tpl and "grpg-judge-card" not in dash_tpl)
    checks["no judge js remains"] = (
        "reconcileJudge" not in js and "grpg-judge" not in js and
        "system-judge/latest" not in js and "data-action=\"accept\"" not in js and "data-action=\"dispute\"" not in js)
    ctx_builder = read(os.path.join(REPO, "app", "utils", "assets", "context_builder.py"))
    checks["no judge context remains"] = (
        "judge_reviews" not in ctx_builder and "build_judge_reviews" not in ctx_builder and
        "missed_count" not in ctx_builder)
    views_src = read(os.path.join(REPO, "app", "routes", "views.py"))
    checks["no judge call passes missed_count to garden ctx"] = "missed_count=missed_count" not in views_src
    checks["judge navlink in topbar"] = "views.judge_log" in topbar_tpl and "Judge" in topbar_tpl
    checks["judge_log route survives"] = "judge-log" in views_src and "def judge_log" in views_src

    # ── Completion popup (click mission row) ──
    missions_tpl = read(os.path.join(REPO, "app", "templates", "partials", "_missions_panel.html"))
    checks["no per-mission complete button"] = (
        '<button class="grpg-mission-status' not in missions_tpl and "aria-pressed" not in missions_tpl)
    checks["mission row is clickable target"] = (
        'class="grpg-mission-row' in missions_tpl and 'role="button"' in missions_tpl and
        'tabindex="0"' in missions_tpl and "data-done=" in missions_tpl)
    checks["status indicator is passive span"] = (
        '<span class="grpg-mission-status' in missions_tpl and "aria-hidden=\"true\"" in missions_tpl)
    checks["completion modal open on row click"] = (
        "openCompletionModal" in js and "closest('.grpg-mission-row')" in js and
        "grpgCompleteModal" in js and "grpg-complete-confirm" in js)
    checks["popup fields: time/status/reason"] = all(token in js for token in (
        "grpg-complete-at", "grpg-complete-time", "grpg-complete-reason", "grpg-complete-status"))
    checks["popup sends full payload"] = all(token in js for token in (
        "actual_time_taken", "completed_on", "timetable_entry_id", "status: status"))
    checks["reason required for partial/skipped"] = (
        "A reason is required for " in js and "status !== 'completed' && !reason" in js)
    checks["segmented status styles"] = (
        "grpg-complete-status" in layout and "grpg-status-option" in layout and
        "grpg-status-option-active" in layout)
    payloads = read(os.path.join(REPO, "app", "utils", "assets", "dashboard_payloads.py"))
    checks["time-of-day mission ordering (next first, earliest last)"] = (
        "_mission_order_key" in payloads and "start_minute >= now_minute" in payloads and
        "24 * 60" in payloads)
    checks["client re-sorts rows to server order"] = (
        "grpg-missions-list" in js and "data-mission-id=\"" in js and "appendChild" in js)

    # ── Scrollable missions list, no VIEW ALL toggle ──
    checks["view-all toggle removed"] = (
        "grpg-missions-toggle" not in missions_tpl and "grpg-missions-toggle" not in js and
        "applyMissionsCollapse" not in js and "VIEW ALL" not in missions_tpl)
    checks["hidden-row gating gone"] = (
        "grpg-missions-hidden-row" not in missions_tpl and
        "grpg-missions-hidden-row" not in layout and "grpg-missions-hidden-row" not in js)
    checks["mission list scrolls with hidden bars"] = (
        "grpg-missions-scroll" in missions_tpl and
        "scrollbar-width: none" in layout and "-webkit-scrollbar" in layout and
        "display: none" in fragment(layout, "grpg-missions-scroll::-webkit-scrollbar", 200))

    # ── Dashboard JS ──
    checks["JS chart cyan fallback"] = "#1CAED5" in js
    checks["JS renders activity rows"] = "reconcileActivity" in js

    # ── Topbar (exact spec) ──
    checks["topbar header 96px + base"] = "height: 96px;" in layout and "#0D1117" in layout and "#2A3040" in layout
    checks["topbar nav labels uppercase #C5CAD3"] = "#C5CAD3" in layout
    checks["level ring 104px + pink/gold"] = "width: 104px;" in layout and "#F0555C" in layout and "#F5B942" in topbar_tpl
    checks["level ring number 36px w800"] = "font-size: 36px;" in layout and "font-weight: 800;" in layout
    checks["xp block 220px + track #252B38"] = "width: 220px;" in layout and "#252B38" in layout
    checks["bottom nav maroon pill rounded"] = "background: var(--nav-active)" in layout and "border-radius: var(--radius-pill)" in layout
    checks["diagonal clock divider kept"] = "transform: rotate(20deg)" in layout
    checks["thousands separators in xp format"] = "'{:,}'.format" in topbar_tpl

    # ── Layout scale (1080p pass) ──
    checks["side columns via var-based grid"] = "grid-template-columns: var(--col-l) 1fr var(--col-r)" in layout and "--col-l: 330px" in layout
    checks["bottom row 190px"] = "height: 190px;" in layout

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