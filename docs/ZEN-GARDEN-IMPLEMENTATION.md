# Zen RPG Digital Garden — Implementation Plan

**Scope:** Dashboard-only skin. Other pages later.
**Design spec:** `docs/real-life-rpg-dashboard-implementation-guide.md`
**Current state:** Professional/philosophical theme is the "default". Garden RPG will be a second switchable skin.
**Branch:** `dev` (committed baseline first, then work on feature branch)

---

## Phase 0 — Commit Current State as Baseline
- [ ] Stage all current files (default theme)
- [ ] Commit as "refactor: professional theme baseline"
- [ ] Verify app runs

---

## Phase 1 — Theme Plumbing (CSS Architecture)

**Goal:** Two themes coexist. `data-theme="default"` = current professional. `data-theme="garden-rpg"` = new Zen RPG. Both stylesheets load on every page. Only one is active at a time.

- [ ] Scope current `tokens.css` light/dark vars under `[data-theme="default"]` instead of bare `:root`/`[data-theme="light"]`
- [ ] Change `data-theme="light"` in `base2.html` to `data-theme="default"`
- [ ] Update `theme.js` to toggle `data-theme` between `"default-light"` and `"default-dark"` within the default theme
- [ ] Create `static/css/theme-garden-rpg.css` with empty `[data-theme="garden-rpg"]` token block (Section 2 of guide)
- [ ] Add inline `<script>` in `base2.html` `<head>` above all CSS links:
  ```html
  <script>
    (function() {
      var saved = localStorage.getItem('theme') || 'default';
      document.documentElement.setAttribute('data-theme', saved);
    })();
  </script>
  ```
- [ ] Load `theme-garden-rpg.css` after `tokens.css` in `base2.html`
- [ ] Create `static/js/theme-switcher.js` — reads/writes `theme` in localStorage, sets `data-theme` on `<html>`, triggers page reload or theme swap
- [ ] Add theme switcher dropdown to navbar (between nav links and theme-toggle button)
- [ ] Garden RPG CSS uses `grpg-` prefix on all class names to avoid collisions

**CSS scoping strategy:**
```
[data-theme="default"] { /* current light theme vars */ }
[data-theme="default"][data-scheme="dark"] { /* current dark theme vars */ }
[data-theme="garden-rpg"] { /* garden RPG vars — dark by default */ }
```

This way `data-theme` selects the design system, and within default, `data-scheme` selects light/dark. Garden RPG is always dark.

### Files modified:
- `app/static/css/tokens.css` — re-scope under `[data-theme="default"]`
- `app/templates/base2.html` — add inline head script, load garden CSS, add switcher to nav
- `app/static/js/theme.js` — rename to handle `data-scheme` within default theme

### Files created:
- `app/static/css/theme-garden-rpg.css`
- `app/static/js/theme-switcher.js`

---

## Phase 2 — Garden RPG Dashboard Template + Layout Shell

**Goal:** Empty grid shell renders correctly at all breakpoints.

- [ ] Create `app/templates/partials/` directory
- [ ] Create `app/templates/dashboard_garden_rpg.html` extending `base2.html`
- [ ] Create empty partials:
  - `partials/_topbar_garden_rpg.html`
  - `partials/_attributes_panel.html`
  - `partials/_garden_status_panel.html`
  - `partials/_hero_garden.html`
  - `partials/_missions_panel.html`
  - `partials/_system_judge_panel.html`
  - `partials/_bottom_stat_row.html`
  - `partials/_bottom_nav_garden_rpg.html`
- [ ] Dashboard template includes all partials per Section 3 layout
- [ ] CSS grid shell in `theme-garden-rpg.css`:
  - `.grpg-dashboard` — `grid-template-rows: 72px 1fr 156px 56px; height: 100vh;`
  - `.grpg-main-row` — `grid-template-columns: 300px 1fr 340px; gap: 16px; padding: 16px;`
  - `.grpg-col-left`, `.grpg-col-right` — `display: flex; flex-direction: column; gap: 16px;`
- [ ] Responsive `@media (max-width: 1024px)` — single column, `height: auto`, CSS order for mobile

### Files created:
- `app/templates/dashboard_garden_rpg.html`
- `app/templates/partials/_topbar_garden_rpg.html`
- `app/templates/partials/_attributes_panel.html`
- `app/templates/partials/_garden_status_panel.html`
- `app/templates/partials/_hero_garden.html`
- `app/templates/partials/_missions_panel.html`
- `app/templates/partials/_system_judge_panel.html`
- `app/templates/partials/_bottom_stat_row.html`
- `app/templates/partials/_bottom_nav_garden_rpg.html`

---

## Phase 3 — Route + Theme Detection

**Goal:** When garden-rpg theme is active, `/dashboard` serves the garden template.

- [ ] Modify `views.dashboard()` to check a cookie for theme preference
- [ ] If `theme=garden-rpg` cookie → render `dashboard_garden_rpg.html`
- [ ] If `theme=default` cookie → render `dashboard.html` (current)
- [ ] Theme switcher JS sets a cookie alongside localStorage
- [ ] Both templates receive the same data context dict from the view
- [ ] Verify: switch theme → navigate to `/dashboard` → correct template renders

### Files modified:
- `app/routes/views.py` — add theme detection in `dashboard()` route
- `app/static/js/theme-switcher.js` — set cookie on theme change

---

## Phase 4 — Topbar (72px row)

**Goal:** Full topbar with streak, DCP, level ring, XP bar, nav icons, avatar.

- [ ] Build `_topbar_garden_rpg.html` per Section 4:
  - Hamburger button with `aria-label`
  - Logo + two-line label ("REAL LIFE RPG" / "BALANCE. DISCIPLINE. GROWTH.")
  - 1px vertical divider
  - Streak block (flame icon `--accent-fcs`, count, "STREAK" / "BEST")
  - DCP block (shield icon `--accent-dsc`, value, "DCP" / "DISCIPLINE")
  - Level ring — inline SVG `<circle>` pair, `stroke-dashoffset` set via Jinja
  - XP block — "{{ xp_current }} / {{ xp_next }}" + thin bar div
  - Nav icon group — 4 buttons (Today/Map/Journal/Stats), `grpg-nav-active` on current
  - Avatar `<img>` (40px round) + chevron
- [ ] CSS for `.grpg-topbar` — 72px, flex, styling per Section 2 tokens
- [ ] Accessibility: all icon-only buttons have `aria-label`, level ring has `<span class="sr-only">`

---

## Phase 5 — Attributes Panel (Left Column)

**Goal:** 5 attribute rows with bars and trend arrows.

- [ ] Build `_attributes_panel.html` per Section 5
- [ ] 5 rows: INT/STA/FCS/CHA/DSC — icon badge, code, name, value, trend (▲/▼/—)
- [ ] Bar track + fill per attribute, color from `--accent-{attr}`
- [ ] CSS: 14px gap between rows, 18px panel padding
- [ ] Accessibility: glyph + color for trends

---

## Phase 6 — Garden Status Panel (Left Column)

**Goal:** Garden growth stats display.

- [ ] Build `_garden_status_panel.html`
- [ ] Ring/gauge + growth stats
- [ ] Data from context dict

---

## Phase 7 — Hero Garden (Center Column)

**Goal:** Beautiful garden scene with floating region badges and task overlays.

- [ ] Source/create `static/img/garden-hero.jpg` — Japanese garden at dusk
- [ ] Build `_hero_garden.html` per Section 6:
  - Background image, `border-radius: 14px`, `overflow: hidden`
  - Quote block — Georgia serif italic
  - 3 region badges (Academy/River/Moon) absolutely positioned
  - Petals card (bottom-left) — today's tasks checklist
  - Seeds card (bottom-center) — future quests with locks + add button
- [ ] CSS for `.grpg-hero`, `.grpg-region-badge`, `.grpg-overlay-card`, `.grpg-checklist`
- [ ] Checklist toggle done/not-done via CSS attribute selectors

---

## Phase 8 — Missions Panel (Right Column)

**Goal:** Today's missions list with tags and XP.

- [ ] Build `_missions_panel.html` per Section 7
- [ ] 4 mission rows: tag (MAIN/DAILY/SIDE), title, time, countdown, XP
- [ ] Toggle button, "VIEW ALL MISSIONS" ghost button
- [ ] CSS: `.grpg-mission-row` styling

---

## Phase 9 — System Judge Panel (Right Column)

**Goal:** Review metrics and penalty display.

- [ ] Build `_system_judge_panel.html` per Section 8
- [ ] Last review label, task name, missed count pill
- [ ] 3 metric rows (Validity/Responsibility/Consistency) with bars
- [ ] Penalty row, "OPEN FULL LOG" button

---

## Phase 10 — Bottom Stat Row (4 Cards)

**Goal:** Wayfarer, XP Flow, Discipline, Recent Activity cards.

- [ ] Build `_bottom_stat_row.html` per Section 9
- [ ] Card 1 — Wayfarer: level, title, XP, progress bar, reward chips
- [ ] Card 2 — XP Flow: `<canvas id="grpg-xp-chart">` + JSON data blob
- [ ] Card 3 — Discipline: inline SVG radial gauge, metrics, sparkline
- [ ] Card 4 — Recent Activity: list with status icons, names, XP deltas
- [ ] CSS: `grid-template-columns: repeat(4, 1fr)`, responsive `repeat(2, 1fr)`

---

## Phase 11 — Bottom Nav

**Goal:** 7-item navigation bar with day/night toggle.

- [ ] Build `_bottom_nav_garden_rpg.html` per Section 10
- [ ] 7 nav items: Home/Missions/Garden/Stats/Journal/Inventory/Shop
- [ ] Active state on Home, day/night toggle (visual only), clock display
- [ ] CSS: 56px height

---

## Phase 12 — Dashboard JS Interactivity

**Goal:** Mission toggles, petal toggles, XP chart, all interactive.

- [ ] Create `static/js/dashboard-garden-rpg.js` per Section 11:
  - `initMissionToggles()` — toggle done state, update topbar XP
  - `initPetalsToggles()` — toggle checklist items
  - `drawXpChart()` — Canvas 2D bar chart from JSON blob, resize handler
  - `initDayNightToggle()` — visual toggle
- [ ] Load in `dashboard_garden_rpg.html` with `defer`
- [ ] All functions in `DOMContentLoaded` listener

---

## Phase 13 — Real Data Wiring

**Goal:** Dashboard renders with real user data, no hardcoded test data.

- [ ] Extend `views.dashboard()` context dict per Section 13:
  - `streak`, `streak_best`, `dcp`
  - `level`, `xp_current`, `xp_next`, `ring_offset`
  - `attributes` list (5 items with trend data)
  - Region values, quote lines
  - `petals`, `seeds`, `missions` lists
  - `judge` dict with metrics
  - `xp_week` array, discipline data
  - Activity log, nav items, current time
- [ ] Compute `ring_offset` server-side
- [ ] Build attribute trend data from completion history
- [ ] Remove all hardcoded test data from partials
- [ ] Grep partials for any remaining hardcoded values

---

## Phase 14 — Accessibility Pass

- [ ] Every icon-only button has `aria-label`
- [ ] Level ring and discipline gauge have `<span class="sr-only">`
- [ ] Trend arrows use glyph + color
- [ ] Status uses icon shape + color
- [ ] WCAG AA contrast on `--text-secondary` and `--text-muted` vs `--bg-panel`
- [ ] Full keyboard reachability in visual order
- [ ] `:focus-visible` outlines on all focusable elements

---

## Phase 15 — Responsive + Cross-Theme Regression

- [ ] Sub-1024px stacked layout verified
- [ ] Full theme-switch regression: Default → Garden RPG → Default
- [ ] No layout shift or leaked styles on any page
- [ ] `localStorage` + cookie persistence across reload

---

## Phase 16 — Cleanup + Deploy

- [ ] Remove leftover `console.log`
- [ ] Final visual check against guide reference
- [ ] Test on PythonAnywhere
- [ ] Commit all garden-rpg work
