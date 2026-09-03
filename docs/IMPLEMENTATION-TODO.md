# REAL LIFE RPG — Implementation TODO

Phases H0–H10, extending the existing garden-rpg theme.
Guide: `docs/coding-agent-guide.md` | Image brief: `docs/garden-image-generation-brief.md`

> **Status Legend:** ✅ done | ⬜ pending | 🔧 partial

---

## Phase H-Data — Data model additions
- [x] `regions` dict (academy/river/moon/village) + `garden_health`, `player`, `missions`, `seeds`, `judge_reviews`, `activity`, `world_events`
- [x] `tier` computed server-side in `context_builder.py`
- [x] `attr_delta_str` for feedback loop

## Phase H0 — Asset placeholder system
- [x] `app/utils/assets/__init__.py` — `asset_exists()`, `region_art()`, `hero_bg()`, `health_overlay()`
- [x] `static/img/` + `static/img/regions/` directories
- [x] `{% if exists %}` branch in hero + all 4 region overlays + health overlay
- [x] Placeholder CSS (`.grpg-placeholder-hero/region/label`)
- [x] `onerror` fallback on all `<img>` tags
- [x] Verified: no images → clean placeholders

## Phase H1+H6 — Stateful garden + color semantics
- [x] Hero renders tier art/placeholder per region via Stage 0 pattern
- [x] Region anchor positions (Academy 32/46, River 48/22, Moon 45/76, Village 68/58)
- [x] z-index stacking (bg 1, health 2, region 3, UI 4)
- [x] Region click → expanded panel showing 3 recent `activity` for that region
- [x] `.grpg-region-pulse` on completion (2s)
- [x] `--accent-active` token (neutral — active/selected only)
- [x] Green limited to DSC; completions use gold/white; penalties subdued red

## Phase H2 — Fix navigation
- [x] Removed "Today" from topbar; Home is today
- [x] Topbar icons secondary/muted (`grpg-topbar-secondary`)
- [x] Bottom nav = ONLY primary nav, all icon+label (no emoji)
- [x] Avatar → profile link

## Phase H3+H7 — Mission depth + feedback loop
- [x] Difficulty dots + attr color dots per mission
- [x] Expandable row (click) revealing attrs/difficulty/deadline/reward/streak-risk/target + START/RESCHEDULE/ABANDON
- [x] Status enum styling (COMPLETED, COMPLETED_LATE, MISSED, LOCKED, ABANDONED, RESCHEDULED)
- [x] "Current Objective" block (highest-priority ACTIVE mission + START button)
- [x] Completion → inline summary (attrs → region) + region pulse (H7)
- [x] Recent Activity rows: name, time, XP, → region

## Phase H4 — System Judge
- [x] Numbered review, task, reason, 3 metrics, penalty, discipline delta, ACCEPT/DISPUTE
- [x] Judge history list routes from log data

## Phase H5 — Visual hierarchy
- [x] Tier 1 hero w/ soft vignette; Tier 4 analytics muted/thinner
- [x] Petals/Seeds cards translucent

## Phase H8 — Stats page
- [x] `stats_garden_rpg.html` — attributes, mission breakdown, streak, duration, penalty history, activity log
- [x] Bottom-nav Stats lands on it (theme-detected)

## Phase H9 — Player identity
- [x] Garden name serif label near quote
- [x] Wayfarer card: title, next, streak, attrs
- [x] Avatar → `/profile` (`profile.html`: title, level, attrs, read-only garden)
- 🔧 Journal `linked_attr` — NO journal model exists yet; deferred until journal feature

## Phase H10 — Atmosphere/polish
- [x] Petal drift, firefly glow (Moon), water shimmer (River) — motion-gated
- [x] Border treatment variation
- 🔧 Optional Focus Mode — deferred

---

## Not yet scoped
- Journal feature (needed for `linked_attr`)
- Focus Mode (post-H1–H9 hardening)
