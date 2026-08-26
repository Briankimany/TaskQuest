# Real Life RPG Dashboard — Implementation Guide (vanilla HTML/CSS/JS + Jinja)

Stack: plain HTML, CSS, JS, Jinja2 templates. No React, no build-step framework. This is a NEW THEME layered onto an existing app that already has a UI — the user must be able to switch between the existing theme and this one ("garden-rpg") at runtime. Every rule below is written with that constraint in mind. Follow this in order. Don't improvise layout or values that are specified.

---

## 0. How this fits into an existing project (read this first)

Assume the existing project already has:
- A base Jinja template (commonly `templates/base.html`) that every page extends.
- An existing `static/css/` folder with the current theme's stylesheet(s).
- Some existing JS in `static/js/`.

Do NOT replace or edit the existing theme's CSS files. Do NOT hardcode this theme as the only option. Instead:

1. Add a new stylesheet `static/css/theme-garden-rpg.css` that is only active when a `data-theme="garden-rpg"` attribute is present on `<html>` or `<body>`. Every single selector in that file must be scoped under `[data-theme="garden-rpg"]` so it cannot leak into or fight with the existing theme when both stylesheets are loaded on the page at the same time.
2. Add a theme switcher: a tiny JS file `static/js/theme-switcher.js` that reads/writes a `theme` value to `localStorage`, sets `document.documentElement.setAttribute('data-theme', value)` on load and on user toggle, and exposes a `<select>` or toggle button in the existing UI (wherever the existing settings/nav area is) with at least two options: `"default"` and `"garden-rpg"`.
3. Load both stylesheets on every page (`base.html`'s `<head>`) — the `data-theme` attribute decides which rules actually apply, so there is zero flash-of-wrong-theme as long as `theme-switcher.js` runs before first paint (put the localStorage-read + attribute-set as an inline `<script>` in `<head>`, before the stylesheets even, so it doesn't wait on JS file download).
4. This dashboard's markup lives in its own template, `templates/dashboard_garden_rpg.html`, which extends the same `base.html` as the rest of the app so nav, auth, and existing chrome keep working. Do not fork `base.html` into a second copy.

Inline head script (put this literally in `base.html`, above the CSS `<link>` tags):
```html
<script>
  (function() {
    var saved = localStorage.getItem('theme') || 'default';
    document.documentElement.setAttribute('data-theme', saved);
  })();
</script>
<link rel="stylesheet" href="{{ url_for('static', filename='css/theme-default.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/theme-garden-rpg.css') }}">
```

---

## 1. File structure to create

```
/templates
  base.html                          (existing — edit only as described in Section 0)
  dashboard_garden_rpg.html          (new — the page itself)
  /partials
    _topbar_garden_rpg.html
    _attributes_panel.html
    _garden_status_panel.html
    _hero_garden.html
    _missions_panel.html
    _system_judge_panel.html
    _bottom_stat_row.html
    _bottom_nav_garden_rpg.html
/static
  /css
    theme-garden-rpg.css             (new, single file, all rules scoped — see Section 2)
  /js
    theme-switcher.js                (new — Section 0)
    dashboard-garden-rpg.js          (new — all interactivity for this page, Section 11)
  /img
    garden-hero.jpg                  (background illustration — see Section 6 for sourcing)
```

Each `_partial.html` is included from `dashboard_garden_rpg.html` with `{% include "partials/_x.html" %}`. Every partial receives its data from the same context dict passed down from the view (Section 9's data shape) — do not fetch data inside partials.

---

## 2. CSS tokens — `theme-garden-rpg.css`, top of file

Everything scoped under `[data-theme="garden-rpg"]` on `:root`/`html`. Do not use bare `:root { }` — that would leak into the default theme.

```css
[data-theme="garden-rpg"] {
  --bg-page: #05060A;
  --bg-panel: #0F1218;
  --bg-panel-raised: #151923;
  --border-hairline: #232838;
  --border-strong: #34394A;

  --text-primary: #F2F3F5;
  --text-secondary: #9BA1AE;
  --text-muted: #5F6472;

  --accent-int: #34C6E8;
  --accent-sta: #E85B4B;
  --accent-fcs: #E8A93C;
  --accent-cha: #9B7FE8;
  --accent-dsc: #4FCB7C;

  --accent-success: #3FCB7C;
  --accent-danger: #E8544B;
  --accent-warning: #E8A93C;
  --accent-info: #34C6E8;

  --xp-gradient: linear-gradient(90deg, #34C6E8, #E85B9C);
}

[data-theme="garden-rpg"] body {
  background: var(--bg-page);
  color: var(--text-primary);
}
```

Every rule for every component below must be nested/prefixed the same way, e.g. `[data-theme="garden-rpg"] .grpg-panel { ... }`. Prefix every class name in this theme with `grpg-` (short for garden-rpg) so nothing can collide with existing class names in the app's default theme, even by accident. Example: `.grpg-topbar`, `.grpg-attr-row`, `.grpg-mission-item`.

Typography rule: system sans for all UI text except `.grpg-quote`, which uses `font-family: Georgia, serif; font-style: italic;`.

Panel titles: `font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-secondary); font-weight: 600;`

Corners: panels `border-radius: 14px; border: 1px solid var(--border-hairline); background: var(--bg-panel);`. Pills `border-radius: 999px`. Buttons/nav items `border-radius: 10px`.

---

## 3. Page layout — `dashboard_garden_rpg.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="grpg-dashboard">
  {% include "partials/_topbar_garden_rpg.html" %}
  <div class="grpg-main-row">
    <div class="grpg-col-left">
      {% include "partials/_attributes_panel.html" %}
      {% include "partials/_garden_status_panel.html" %}
    </div>
    {% include "partials/_hero_garden.html" %}
    <div class="grpg-col-right">
      {% include "partials/_missions_panel.html" %}
      {% include "partials/_system_judge_panel.html" %}
    </div>
  </div>
  {% include "partials/_bottom_stat_row.html" %}
  {% include "partials/_bottom_nav_garden_rpg.html" %}
</div>
{% endblock %}
```

CSS for the shell:

```css
[data-theme="garden-rpg"] .grpg-dashboard {
  display: grid;
  grid-template-rows: 72px 1fr 156px 56px;
  height: 100vh;
}
[data-theme="garden-rpg"] .grpg-main-row {
  display: grid;
  grid-template-columns: 300px 1fr 340px;
  gap: 16px;
  padding: 16px;
}
[data-theme="garden-rpg"] .grpg-col-left,
[data-theme="garden-rpg"] .grpg-col-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

Responsive: under 1024px, `.grpg-main-row` becomes `grid-template-columns: 1fr; grid-template-rows: auto;` and `.grpg-dashboard` height becomes `auto` with normal page scroll. Order on mobile via CSS `order`: topbar(0) → hero(1) → attributes(2) → missions(3) → garden-status(4) → system-judge(5) → bottom-stat-row(6) → bottom-nav(7). Do this with a `@media (max-width: 1024px)` block at the bottom of the CSS file, not with JS.

---

## 4. Partial: `_topbar_garden_rpg.html` (72px row)

Plain HTML, data comes from Jinja variables (e.g. `{{ streak }}`, `{{ dcp }}`, `{{ level }}`, `{{ xp_current }}`, `{{ xp_next }}`, `{{ user.avatar_url }}`). Structure left to right:

1. Hamburger button (`<button class="grpg-icon-btn" aria-label="Open menu">`).
2. Logo mark + two-line label block ("REAL LIFE RPG" / "BALANCE. DISCIPLINE. GROWTH.").
3. 1px vertical divider.
4. Streak stat block (flame icon colored `--accent-fcs`, "{{ streak }}" big, "STREAK" / "BEST {{ streak_best }}" small).
5. DCP stat block (shield icon colored `--accent-dsc`, "{{ dcp }}" big, "DCP" / "DISCIPLINE" small).
6. Level ring: an inline `<svg>` circle pair (track circle + progress circle). Set the progress circle's `stroke-dasharray`/`stroke-dashoffset` via a Jinja-computed inline style: `style="stroke-dashoffset: {{ ring_offset }};"` where `ring_offset` is computed server-side as `circumference * (1 - xp_current/xp_next)`. Center text "{{ level }}" / "LEVEL".
7. XP block: "{{ xp_current }} / {{ xp_next }}" text + a thin bar div whose fill width is set inline: `style="width: {{ (xp_current/xp_next*100)|round(1) }}%;"`.
8. Nav icon group: 4 stacked icon+label buttons (Today/Map/Journal/Stats), each an `<a>` to the relevant route, current page gets class `grpg-nav-active`.
9. Avatar `<img>` (40px round) + chevron.

Icons: use inline SVG (outline style, ~18-24px) or an existing icon font already in the project if one exists — do not add a whole new icon library just for this theme if the base project already ships one (check `base.html` head for an existing icon `<link>` first).

---

## 5. Partial: `_attributes_panel.html`

```html
<div class="grpg-panel grpg-attr-panel">
  <div class="grpg-panel-header">
    <span class="grpg-panel-title">Attributes</span>
    <button class="grpg-icon-btn" aria-label="View attribute trends"><!-- trend icon --></button>
  </div>
  {% for attr in attributes %}
  <div class="grpg-attr-row" style="--attr-color: var(--accent-{{ attr.code|lower }});">
    <div class="grpg-attr-top">
      <span class="grpg-attr-icon-badge"><!-- icon --></span>
      <span class="grpg-attr-code">{{ attr.code }}</span>
      <span class="grpg-attr-name">{{ attr.name }}</span>
      <span class="grpg-attr-value">{{ attr.value }}</span>
      <span class="grpg-attr-trend grpg-trend-{{ attr.trend_dir }}">{{ attr.trend_label }}</span>
    </div>
    <div class="grpg-bar-track">
      <div class="grpg-bar-fill" style="width: {{ attr.value }}%; background: var(--attr-color);"></div>
    </div>
  </div>
  {% endfor %}
</div>
```

`attributes` is a list of dicts, one per row, in this exact order for this screen: INT 72 (+2), STA 81 (-1), FCS 68 (+4), CHA 63 (flat), DSC 78 (+1). `trend_dir` is one of `up`/`down`/`flat`, and CSS colors `.grpg-trend-up` green, `.grpg-trend-down` red, `.grpg-trend-flat` muted, using a triangle glyph (▲/▼/—) in the HTML itself, not a CSS-only color — this is required for accessibility (Section 12), color can't be the only signal.

Row spacing: 14px gap between `.grpg-attr-row` elements, 18px panel padding.

---

## 6. Partial: `_hero_garden.html`

```html
<div class="grpg-hero">
  <img src="{{ url_for('static', filename='img/garden-hero.jpg') }}" alt="" class="grpg-hero-bg">
  <p class="grpg-quote">"{{ quote_line_1 }}<br>{{ quote_line_2 }}"</p>

  <div class="grpg-region-badge" style="top: 32%; left: 46%; --badge-color: var(--accent-int);">
    <span class="grpg-badge-icon"><!-- book icon --></span>
    <span class="grpg-badge-label">ACADEMY<br><small>INT {{ region_academy_value }}</small></span>
  </div>
  <div class="grpg-region-badge" style="top: 48%; left: 22%; --badge-color: #34C6E8;">
    <span class="grpg-badge-icon"><!-- wave icon --></span>
    <span class="grpg-badge-label">RIVER<br><small>STA {{ region_river_value }} ▲</small></span>
  </div>
  <div class="grpg-region-badge" style="top: 45%; left: 76%; --badge-color: var(--accent-fcs);">
    <span class="grpg-badge-icon"><!-- moon icon --></span>
    <span class="grpg-badge-label">MOON<br><small>FCS {{ region_moon_value }}</small></span>
  </div>

  <div class="grpg-overlay-card" style="bottom: 4%; left: 3%;">
    <div class="grpg-panel-header"><!-- flower icon --><span>PETALS</span></div>
    <p class="grpg-overlay-sub">Today's Tasks</p>
    <ul class="grpg-checklist" id="grpg-petals-list">
      {% for task in petals %}
      <li class="grpg-check-row" data-done="{{ 'true' if task.done else 'false' }}">
        <button class="grpg-check-toggle" aria-label="Toggle {{ task.label }}"></button>
        <span>{{ task.label }}</span>
      </li>
      {% endfor %}
    </ul>
  </div>

  <div class="grpg-overlay-card" style="bottom: 4%; left: 42%;">
    <div class="grpg-panel-header"><!-- seedling icon --><span>SEEDS</span></div>
    <p class="grpg-overlay-sub">Future Quests</p>
    <ul class="grpg-checklist">
      {% for quest in seeds %}
      <li class="grpg-lock-row"><!-- lock icon --><span>{{ quest.label }}</span></li>
      {% endfor %}
    </ul>
    <button class="grpg-ghost-btn grpg-add-seed">+ ADD NEW SEED</button>
  </div>
</div>
```

CSS: `.grpg-hero { position: relative; border-radius: 14px; overflow: hidden; }`, `.grpg-hero-bg { width:100%; height:100%; object-fit: cover; display:block; }`, every absolutely-positioned child uses `position: absolute;` with the inline `top`/`left` percentages from Section 6 of the original spec (kept as inline styles per element, driven by Jinja variables if positions ever need to become configurable — for this screen they can be hardcoded inline as shown above).

Image sourcing note: `garden-hero.jpg` is a single static asset — a Japanese garden scene at dusk, cherry blossoms, a stone bridge, a pagoda, distant mountains, warm lantern light. Source or commission this once and drop it in `static/img/`; do not attempt to generate it at request time in the page render path.

Petals checklist rows toggle done/not-done via JS (Section 11), which flips the `data-done` attribute and re-renders the checkbox fill — style both states with plain CSS attribute selectors: `.grpg-check-row[data-done="true"] .grpg-check-toggle { background: var(--accent-success); }`.

---

## 7. Partial: `_missions_panel.html`

```html
<div class="grpg-panel grpg-missions-panel">
  <div class="grpg-panel-header">
    <span class="grpg-panel-title">Today's missions</span>
    <span class="grpg-count-pill">{{ missions|length }}</span>
  </div>
  {% for m in missions %}
  <div class="grpg-mission-row" data-mission-id="{{ m.id }}" data-done="{{ 'true' if m.done else 'false' }}">
    <div class="grpg-mission-top">
      <button class="grpg-mission-status" style="--tag-color: var(--accent-{{ m.tag_color }});" aria-label="Toggle {{ m.title }}"></button>
      <span class="grpg-mission-tag" style="color: var(--accent-{{ m.tag_color }});">[{{ m.tag }}]</span>
      <span class="grpg-mission-title">{{ m.title }}</span>
      <span class="grpg-mission-xp">{{ '+%d XP'|format(m.xp) }}</span>
    </div>
    <div class="grpg-mission-meta">
      {% if m.done %}<span class="grpg-done-label">✓ DONE</span>{% else %}{{ m.time_range }} · {{ m.countdown }}{% endif %}
    </div>
  </div>
  {% endfor %}
  <button class="grpg-ghost-btn grpg-view-all">VIEW ALL MISSIONS →</button>
</div>
```

Data for this screen (pass as `missions` list from the view function, in this order):
1. id `mission-1`, tag `MAIN`, tag_color `fcs`, "Study Control Systems", 14:00–16:00, "2h 14m left", +120 XP, not done
2. id `mission-2`, tag `DAILY`, tag_color `dsc`, "Read 30 min", done, +40 XP
3. id `mission-3`, tag `SIDE`, tag_color `cha`, "Exercise (HIIT)", 18:00–18:45, "4h 14m left", +60 XP, not done
4. id `mission-4`, tag `SIDE`, tag_color `cha`, "Build project", 20:00–21:30, "6h 14m left", +80 XP, not done

---

## 8. Partial: `_system_judge_panel.html`

```html
<div class="grpg-panel grpg-judge-panel">
  <div class="grpg-panel-header">
    <span class="grpg-panel-title">System judge</span>
    <a href="{{ url_for('judge_log') }}" class="grpg-link">View log</a>
  </div>
  <p class="grpg-judge-review-label">Last review</p>
  <p class="grpg-judge-review-title">{{ judge.reviewed_task }}
    <span class="grpg-danger-pill">{{ judge.missed_count }} missed tasks</span>
  </p>
  {% for metric in judge.metrics %}
  <div class="grpg-metric-row">
    <span>{{ metric.label }}</span>
    <div class="grpg-bar-track"><div class="grpg-bar-fill" style="width: {{ metric.value }}%; background: var(--accent-info);"></div></div>
    <span>{{ metric.value }}%</span>
  </div>
  {% endfor %}
  <div class="grpg-penalty-row">
    <span>Penalty</span>
    <span class="grpg-penalty-value">{{ judge.penalty }} XP</span>
  </div>
  <button class="grpg-solid-btn">OPEN FULL LOG</button>
</div>
```

Data: `judge.reviewed_task = "Study Control Systems"`, `judge.missed_count = 3`, `judge.metrics = [{label: "Validity", value: 78}, {label: "Responsibility", value: 72}, {label: "Consistency", value: 89}]`, `judge.penalty = -47`.

---

## 9. Partial: `_bottom_stat_row.html` — 4 cards

Four `.grpg-stat-card` elements inside `.grpg-bottom-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }` (becomes `grid-template-columns: repeat(2, 1fr)` under 1024px, per the responsive block in Section 3).

**Card 1 — Wayfarer**: title/subtitle + "NEXT: {{ next_title }}", big "{{ xp_current }} / {{ xp_next }} XP" + "{{ xp_pct }}%", progress bar (same gradient as topbar), reward chips row (Level {{ level+1 }}, New Title, +5 Max Energy).

**Card 2 — XP Flow**: a `<canvas id="grpg-xp-chart">` element. Do NOT pull in a heavy charting library if the base project doesn't already have one — draw this with the native Canvas 2D API directly in `dashboard-garden-rpg.js` (Section 11 has the function). Data: 7 values for Mon–Sun, e.g. `[1400, 1750, 2100, 1650, 2400, 2000, 0]` passed as a JSON blob via `<script type="application/json" id="grpg-xp-data">{{ xp_week|tojson }}</script>` that the JS file reads.

**Card 3 — Discipline**: inline SVG radial gauge (same ring technique as the level ring in Section 4), center "{{ discipline_score }}" / "/100" / "STABLE" (label text driven by `{{ discipline_status }}`, uppercase, colored `--accent-info` when "STABLE", `--accent-warning` when "AT RISK", `--accent-danger` when "CRITICAL" — again using both color and text, not color alone). Right side: 3 metric rows (Consistency, Reliability, Responsibility) same pattern as judge metrics but no bar, just label/value pairs, plus a "Trend (7d)" mini sparkline (inline SVG polyline, values from `{{ discipline_trend|tojson }}`).

**Card 4 — Recent Activity**: list of `activity` entries, each with a status icon (`completed`/`completed_late`/`abandoned`/`in_progress` → different SVG icon + color per Section 12 rules), name, status word, and XP delta (green/red/muted "--").

Data: (1) Read 30 min / completed / +40 XP, (2) Study Control Systems / completed_late / -12 XP, (3) Exercise (HIIT) / abandoned / -30 XP, (4) Build project / in_progress / "--".

---

## 10. Partial: `_bottom_nav_garden_rpg.html`

```html
<nav class="grpg-bottom-nav">
  <div class="grpg-nav-items">
    {% for item in nav_items %}
    <a href="{{ item.href }}" class="grpg-nav-item {{ 'grpg-nav-item-active' if item.active }}">
      <span class="grpg-nav-icon"><!-- item.icon --></span>
      <span class="grpg-nav-label">{{ item.label }}</span>
    </a>
    {% endfor %}
  </div>
  <div class="grpg-nav-clock">
    <span><!-- sun icon --> DAY {{ current_time }}</span>
    <button id="grpg-daynight-toggle" class="grpg-toggle" role="switch" aria-checked="false" aria-label="Toggle day and night visual mode"></button>
  </div>
</nav>
```

`nav_items`: Home, Missions, Garden, Stats, Journal, Inventory, Shop — 7 items, `active: true` only on Home for this page.

---

## 11. JS — `dashboard-garden-rpg.js`

Plain vanilla JS, no framework, attach at the bottom of `dashboard_garden_rpg.html` with `<script src="{{ url_for('static', filename='js/dashboard-garden-rpg.js') }}" defer></script>`.

Required functions:

1. `initMissionToggles()` — `document.querySelectorAll('.grpg-mission-status')`, on click toggle the parent row's `data-done` attribute, update the XP total shown in the topbar XP block (`document.querySelector('.grpg-xp-value')`) by adding/subtracting that mission's XP (read from a `data-xp` attribute you add to each row in the template), and re-render the mission's meta line between the time/countdown text and "✓ DONE".
2. `initPetalsToggles()` — same pattern for `.grpg-check-toggle` in the Petals card.
3. `drawXpChart()` — reads the JSON blob from `#grpg-xp-data`, draws 7 bars on the `#grpg-xp-chart` canvas using plain `CanvasRenderingContext2D` calls (`fillRect` per bar, scaled to the canvas height, color `getComputedStyle` read of `--accent-info` so it still respects the theme token). Redraw on window resize (debounced).
4. `initHoverStates()` — not usually needed if done in pure CSS `:hover`, so prefer CSS `:hover` on `.grpg-panel` for the border-color raise instead of JS. Only add JS here if the base project's CSS reset prevents `:hover` from working as expected.
5. `initDayNightToggle()` — click handler on `#grpg-daynight-toggle`, flips `aria-checked`, purely visual for now (no real light-mode for this theme, see Section 0), just toggles a class for the thumb position.

Wrap all of the above in a single `DOMContentLoaded` listener at the bottom of the file. Do not attach listeners before the DOM is parsed.

---

## 12. Accessibility requirements (do not skip)

- Every icon-only `<button>` needs `aria-label`.
- The level ring and discipline gauge need visually-hidden text (`<span class="sr-only">Level 27, 82 percent to next level</span>`) stating the value in words, in addition to the visual ring.
- Never rely on color alone: attribute trend arrows use a glyph (▲/▼/—) plus color; mission/activity status use an icon shape plus color; System Judge penalty and discipline status show a text label plus color.
- Check `--text-secondary` and `--text-muted` against `--bg-panel` for WCAG AA contrast (4.5:1 body, 3:1 large text ≥24px) — these two are the most likely tokens to fail, verify with a contrast checker before shipping.
- Full keyboard reachability in visual order: theme switcher → topbar nav → attributes → garden status → hero overlay interactive items (petals checkboxes, add-seed button) → missions → system judge → bottom stat cards → bottom nav. Every focusable element needs a visible `:focus-visible` outline: `outline: 2px solid var(--accent-info); outline-offset: 2px;`.

---

## 13. Data contract (what the Flask/Django/whatever view must pass to the template)

Single context dict, one source of truth, nothing hardcoded in partials beyond static layout percentages:

```python
context = {
    "streak": 17, "streak_best": 24, "dcp": 86,
    "level": 27, "xp_current": 12840, "xp_next": 15600, "ring_offset": <computed>,
    "attributes": [ {code, name, value, trend_dir, trend_label}, ... ],  # 5 items
    "region_academy_value": 72, "region_river_value": 81, "region_moon_value": 68,
    "quote_line_1": "Discipline today.", "quote_line_2": "Freedom tomorrow.",
    "petals": [ {label, done}, ... ],
    "seeds": [ {label}, ... ],
    "missions": [ {id, tag, tag_color, title, time_range, countdown, xp, done}, ... ],
    "judge": { reviewed_task, missed_count, metrics: [...], penalty },
    "next_title": "Pathfinder", "xp_pct": 82,
    "xp_week": [1400, 1750, 2100, 1650, 2400, 2000, 0],
    "discipline_score": 86, "discipline_status": "STABLE", "discipline_trend": [...],
    "activity": [ {name, status, xp_delta}, ... ],
    "nav_items": [ {label, href, icon, active}, ... ],
    "current_time": "18:24",
}
```

---

## 14. Progress tracker

Copy this checklist into an issue/ticket or a `PROGRESS.md` at the project root and check items off as they're completed. Do not start a phase before the previous phase's checklist is fully checked — this is a sequential build, not parallel.

### Phase 0 — Theme plumbing (prerequisite, blocks everything else)
- [ ] `theme-garden-rpg.css` file created, empty except for the `[data-theme="garden-rpg"]` token block (Section 2)
- [ ] `theme-switcher.js` created and wired into existing settings/nav UI
- [ ] Inline head script added to `base.html` (Section 0), verified no flash-of-wrong-theme on reload
- [ ] Both stylesheets confirmed loading on every page without visual regression to the EXISTING theme (toggle back and forth, existing pages must look identical to before this work started)
- [ ] `dashboard_garden_rpg.html` created, extends `base.html`, currently empty/blank page reachable via a route

### Phase 1 — Static shell, no data
- [ ] `.grpg-dashboard` grid shell in place with 4 empty placeholder rows sized correctly (72px / 1fr / 156px / 56px)
- [ ] `.grpg-main-row` 3-column grid in place with 3 empty placeholder columns (300px / 1fr / 340px)
- [ ] Confirmed correct proportions at 1280px, 1440px, 1920px viewport widths

### Phase 2 — Left column
- [ ] `_attributes_panel.html` built and rendering all 5 rows from static test data
- [ ] `_garden_status_panel.html` built and rendering ring + growth stats from static test data

### Phase 3 — Center hero
- [ ] `garden-hero.jpg` sourced and placed in `static/img/`
- [ ] `_hero_garden.html` built, background image rendering with `border-radius`/`object-fit` correct
- [ ] Quote block positioned and styled
- [ ] All 3 region badges positioned and styled, checked at 3 breakpoints
- [ ] Petals card built with working checklist markup (JS wiring comes in Phase 7)
- [ ] Seeds card built with lock rows and add-seed button

### Phase 4 — Right column
- [ ] `_missions_panel.html` built, all 4 mission rows rendering from static test data
- [ ] `_system_judge_panel.html` built, all 3 metrics + penalty rendering from static test data

### Phase 5 — Bottom row
- [ ] Card 1 (Wayfarer) built
- [ ] Card 2 (XP Flow) canvas element in place, `drawXpChart()` rendering real bars
- [ ] Card 3 (Discipline) gauge + metrics built
- [ ] Card 4 (Recent Activity) list built

### Phase 6 — Bottom nav
- [ ] `_bottom_nav_garden_rpg.html` built, all 7 nav items rendering, active state correct on Home
- [ ] Day/night toggle present and clickable (visual only per Section 0)

### Phase 7 — Interactivity
- [ ] `initMissionToggles()` working — clicking a mission updates its state and the topbar XP value
- [ ] `initPetalsToggles()` working
- [ ] `drawXpChart()` redraws correctly on window resize
- [ ] `initDayNightToggle()` working

### Phase 8 — Real data wiring
- [ ] View function assembles the full context dict from Section 13 using real data sources (not static test data)
- [ ] All static test data removed from templates — confirm by grepping partials for any hardcoded numbers that should have come from `context`

### Phase 9 — Accessibility pass
- [ ] Every checklist item in Section 12 verified manually (keyboard-only pass through the whole page, screen reader spot-check on the level ring / gauges / trend arrows / status icons, contrast check on `--text-secondary` and `--text-muted`)

### Phase 10 — Responsive + cross-theme regression
- [ ] Sub-1024px stacked layout verified (Section 3 responsive block), order matches spec, page scrolls correctly
- [ ] Full theme-switch regression: toggle default → garden-rpg → default repeatedly, confirm no layout shift or leaked styles on any other page in the app
- [ ] `localStorage` persistence verified across a hard reload and a new tab

### Phase 11 — Cleanup
- [ ] Remove any leftover `console.log` placeholders from Section 11 stub handlers once real routes/endpoints exist for View Log / View All Missions / Add Seed / View All (activity)
- [ ] Final visual diff against the reference image
