# Zen RPG Digital Garden — Implementation Plan

**Scope:** Dashboard-only skin. Other pages later.
**Design spec:** `docs/real-life-rpg-dashboard-implementation-guide.md`
**Branch:** `dev`

---

## Architecture: Two-Tier Theme System

### Tier 1: Token Themes (color/font/spacing swaps — same layout)
Each skin = ONE CSS file that only defines `--variables`. Component CSS never changes.

```
css/tokens.css              → --accent, --bg, --text (default light)
  [data-theme="default"][data-scheme="dark"]  → redefines vars (default dark)
css/theme-garden-rpg.css    → redefines vars (garden RPG dark)
css/theme-[future].css      → redefines vars (future skin #3, #4, etc.)
```

- `cards.css`, `buttons.css`, `tables.css` etc. use `var(--accent)`, `var(--bg-surface)` etc.
- New skin = write ~40 lines of variable definitions. Zero component CSS changes.
- Adding skins is trivial and non-breaking.

### Tier 2: Layout Themes (genuinely different page structure)
Only when the page layout is fundamentally different (e.g., garden RPG dashboard has 3-column grid + hero + bottom nav).

- Gets its own template + layout CSS
- Still uses the same `--variables` from Tier 1
- Layout CSS file: `css/layout-garden-rpg.css` (grid, hero, region badges — layout only)
- Layout CSS selectors prefixed with `grpg-` to avoid collisions
- All component styling (colors, borders, fonts) comes from token layer

### File structure per skin:
```
css/
  tokens.css                      → Tier 1: default light + dark
  theme-garden-rpg.css            → Tier 1: garden RPG color tokens
  layout-garden-rpg.css           → Tier 2: garden RPG layout overrides
  [all existing component CSS]    → Shared: use var() tokens, never modified per skin
```

---

## Phase 0 — Commit Current State as Baseline
- [x] Commit all current files as "default" theme baseline
- [x] Verify app runs after commit

---

## Phase 1 — Theme Plumbing (CSS Architecture)

### Token scoping
- [x] Scope `tokens.css` under `[data-theme="default"]` (was `:root`/`[data-theme="light"]`)
- [x] Dark mode selector changed to `[data-theme="default"][data-scheme="dark"]`
- [x] Update all other CSS files with `[data-theme="dark"]` selectors → `[data-theme="default"][data-scheme="dark"]`
- [x] `base2.html` `data-theme="default"` (was `"light"`)

### Garden RPG tokens (Tier 1)
- [x] Create `css/theme-garden-rpg.css` — token overrides only, scoped under `[data-theme="garden-rpg"]`
- [x] Tokens: `--bg-page`, `--bg-panel`, `--text-primary`, `--accent-int/sta/fcs/cha/dsc`, etc.

### Garden RPG layout (Tier 2)
- [ ] Create `css/layout-garden-rpg.css` — layout-only styles (grid, hero, badges, etc.)
- [ ] All selectors prefixed `grpg-`, scoped under `[data-theme="garden-rpg"]`
- [ ] Move any layout CSS out of `theme-garden-rpg.css` into this file

### Inline head script
- [x] Add inline `<script>` in `base2.html` `<head>` — reads localStorage, sets `data-theme` + `data-scheme` before first paint

### Theme switcher
- [x] Create `js/theme-switcher.js` — dropdown handler, sets localStorage + cookie
- [x] Add `<select>` dropdown to navbar in `base2.html`
- [x] Create `js/theme.js` — light/dark toggle within default theme (toggles `data-scheme`)
- [x] Load both scripts in `base2.html`

### Garden RPG CSS loaded
- [x] `theme-garden-rpg.css` linked in `base2.html` `<head>`
- [ ] `layout-garden-rpg.css` linked in `base2.html` `<head>`

### Verification
- [ ] Toggle Default ↔ Garden RPG — no flash of wrong theme on reload
- [ ] Default theme pages look identical before and after this work
- [ ] Light/dark toggle still works within default theme
- [ ] Garden RPG token file has ONLY variable definitions (no component styles)

---

## Phase 2 — Garden RPG Dashboard Template + Layout Shell

### Template
- [ ] Create `templates/partials/` directory
- [ ] Create `templates/dashboard_garden_rpg.html` extending `base2.html`
- [ ] Create empty partials:
  - `partials/_topbar_garden_rpg.html`
  - `partials/_attributes_panel.html`
  - `partials/_garden_status_panel.html`
  - `partials/_hero_garden.html`
  - `partials/_missions_panel.html`
  - `partials/_system_judge_panel.html`
  - `partials/_bottom_stat_row.html`
  - `partials/_bottom_nav_garden_rpg.html`
- [ ] Dashboard template includes all partials per Section 3 layout spec

### CSS Grid Shell (in layout-garden-rpg.css)
- [ ] `.grpg-dashboard` — `grid-template-rows: 72px 1fr 156px 56px; height: 100vh;`
- [ ] `.grpg-main-row` — `grid-template-columns: 300px 1fr 340px; gap: 16px; padding: 16px;`
- [ ] `.grpg-col-left`, `.grpg-col-right` — `display: flex; flex-direction: column; gap: 16px;`
- [ ] Responsive: `@media (max-width: 1024px)` — single column, `height: auto`, CSS order

### Verification
- [ ] Garden-rpg dashboard loads at its route
- [ ] Grid shell renders correct proportions at 1280px, 1440px, 1920px
- [ ] Toggling to default shows normal dashboard

---

## Phase 3 — Route + Theme Detection

- [ ] Modify `views.dashboard()` to check `app_theme` cookie
- [ ] If `app_theme=garden-rpg` → render `dashboard_garden_rpg.html`
- [ ] If `app_theme=default` → render `dashboard.html`
- [ ] Both templates receive the same data context dict

---

## Phase 4 — Topbar (72px row)

- [ ] Build `_topbar_garden_rpg.html` per Section 4 of guide:
  - Hamburger, logo, divider, streak block, DCP block
  - Level ring (inline SVG), XP bar, nav icons, avatar
- [ ] CSS in `layout-garden-rpg.css`
- [ ] Accessibility: `aria-label` on icon buttons, sr-only text on level ring

---

## Phase 5 — Attributes Panel (Left Column)

- [ ] Build `_attributes_panel.html` per Section 5
- [ ] 5 rows: INT/STA/FCS/CHA/DSC with bars and trend arrows (▲/▼/—)
- [ ] CSS in `layout-garden-rpg.css`

---

## Phase 6 — Garden Status Panel (Left Column)

- [ ] Build `_garden_status_panel.html`
- [ ] Ring/gauge + growth stats from context dict

---

## Phase 7 — Hero Garden (Center Column)

- [ ] Source `static/img/garden-hero.jpg`
- [ ] Build `_hero_garden.html` per Section 6:
  - Background image, quote, 3 region badges, petals card, seeds card
- [ ] CSS in `layout-garden-rpg.css`

---

## Phase 8 — Missions Panel (Right Column)

- [ ] Build `_missions_panel.html` per Section 7
- [ ] 4 mission rows with tags, titles, times, XP

---

## Phase 9 — System Judge Panel (Right Column)

- [ ] Build `_system_judge_panel.html` per Section 8
- [ ] Metrics, penalty, review info

---

## Phase 10 — Bottom Stat Row (4 Cards)

- [ ] Build `_bottom_stat_row.html` per Section 9
- [ ] Wayfarer, XP Flow (canvas), Discipline gauge, Recent Activity

---

## Phase 11 — Bottom Nav

- [ ] Build `_bottom_nav_garden_rpg.html` per Section 10
- [ ] 7 nav items, day/night toggle, clock

---

## Phase 12 — Dashboard JS Interactivity

- [ ] Create `js/dashboard-garden-rpg.js` per Section 11
- [ ] Mission toggles, petal toggles, XP chart (Canvas 2D), day/night toggle

---

## Phase 13 — Real Data Wiring

- [ ] Extend `views.dashboard()` context dict per Section 13
- [ ] Compute ring_offset, attributes trends, missions, petals, seeds, judge
- [ ] Remove all hardcoded test data from partials

---

## Phase 14 — Accessibility Pass

- [ ] aria-labels, sr-only text, glyph+color (not color alone), WCAG AA contrast, keyboard nav, focus-visible

---

## Phase 15 — Responsive + Cross-Theme Regression

- [ ] Sub-1024px layout, theme-switch regression, localStorage persistence

---

## Phase 16 — Cleanup + Deploy

- [ ] Remove console.logs, final visual check, commit, deploy
