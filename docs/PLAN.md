# TaskQuest — Implementation Plan (Judge × Timezone × Merge Import + Tests)

**Date:** 2026-09-21
**Repo:** `E:\BACKUP\PROJECTS\TASKQUEST\TaskQuest` (git HEAD `2d15e69`, work-in-progress changes are present but uncommitted; no commits will be made without explicit permission).

This plan covers three feature areas plus a comprehensive, file-split test module
and a JSON seed dataset. It supersedes the earlier garden-RPG layout round (that
work is complete and merged into the working tree).

---

## 1. System Judge — configurable timeout, health, status pill

### Goal
Judge reviews must never black-hole a request (~3 min worst case today:
`timeout=60s` (yaml) x up to 4 attempts from `max_retries=0` + own retry loop).
The timeout is **config**, not a hardcoded constant, and defaults to **90 seconds**. UI
shows a live status pill (LIVE / PROVISIONAL / OFF) and marks fallback verdicts as provisional.

### Current state (verified)
- `app/utils/managers/ai_assistant.py` — sync `OpenAI()` client; `base_url` from `OMNIROUTE_URL`
  else `provider_config.yaml`; `timeout` read from yaml (`60.0`); `max_retries=0`; own retry loop
  using yaml `retries: 3` with 0.5s sleep between attempts. `complete()` returns `None` on
  persistent transport failure → `PenaltyEvaluator` returns `None` → `JudgeManager` records
  deterministic fallback metrics:
  ```python
  {"validity": d*100, "responsibility": d*95, "consistency": d*100+10,
   "explanation": "The oracles were unavailable; a provisional verdict was recorded."}
  ```
- `app/seed/data/assistant/provider_config.yaml` — `timeout: 60.0`, `retries: 3`.
- `openai==3.8.0` installed in the venv but **not pinned** in `app/requirements.txt`.
- Orphaned `GET /api/system-judge/latest` (no handler) — remove or wire.

### Changes
1. **`provider_config.yaml`**: `timeout: 90.0` (left in yaml = version-controlled config).
2. **`ai_assistant._build_client()`**: resolve timeout as
   `float(os.getenv("OMNIROUTE_TIMEOUT") or self.config.get("timeout", 90.0))` —
   env override, then yaml, then 90.0 default. Nothing hardcoded smaller.
3. **`AIAssistant.health_check()`** (new): parse `base_url`, open a TCP connection to
   `host:port` with `timeout=int(config timeout)` (instant on connection-refused, bounded
   otherwise), return `(ok: bool, latency_ms: int, detail: str)`. This is the reachability
   probe used by the pill — cheap, never blocks longer than the configured timeout.
4. **`app/utils/judge_status.py`** (new): `get_judge_status(user) -> dict`
   `{state: LIVE|PROVISIONAL|OFF, latency_ms, detail, provisional: bool, reached_at}`.
   - `reached = AIAssistant().health_check()`.
   - `LIVE` = reached and no fallback on the user's most recent review.
   - `PROVISIONAL` = reached but the latest review used the fallback marker
     (explanations containing `"oracles were unavailable"`).
   - `OFF` = unreachable.
5. **`GET /api/judge/health`** (new, in `judge_api.py`): returns the status dict for the
   logged-in user. Timestamped.
6. **Status pill UI**:
   - `app/templates/partials/_topbar_garden_rpg.html`: small dot + label chip served
     from a `judge_status` context var (LIVE=green / PROVISIONAL=amber / OFF=red).
   - `app/templates/judge_log.html`: same chip + `data-provisional` badge on fallback reviews.
7. **Provisional badge** (`JudgeReview`): derivable from `explanation == fallback marker`; add a
   Jinja helper `/ context flag` in `judge_log` route. No schema change needed.
8. **Pin `openai==3.8.0`** in `app/requirements.txt`.
9. Wire the status into `views.dashboard()`/`judge_log()` context so the pill renders server-side
   (no extra page JS round-trip on load; `/api/judge/health` exists for refresh polling).

### Acceptance
- `OMNIROUTE_TIMEOUT=1` + endpoint that black-holes → judge returns within ~2s worst case for 2
  attempts (config: env override wins; attempts still bounded by yaml `retries`).
- Unreachable provider (env `OMNIROUTE_URL=http://127.0.0.1:9/v1`) → `OFF` pill, fallback
  metrics, provisional badge, page still renders.
- Reachable provider without fallback → `LIVE`.

---

## 2. Timezone correctness — UTC storage, user-local days

### Goal
All *instants* stored as UTC; all *calendar-day* logic (timetable `date`, `completed_on`,
"today", streaks, `TimetableEntry.start_time/end_time`) evaluated in the **account's**
timezone, never the server wall clock. Per-account `timezone` column, default
`Africa/Nairobi`. Travels in backups so a server move never shifts historical days.

### Current state (verified)
- `User.created_at`, `Activity.created_at` use `datetime.utcnow` (naive UTC — fine).
- `JudgeReview.created_at/updated_at` use `datetime.now` (server local — STORED WRONG).
- "Today" uses server `datetime.now().date()` (views.py:78,135,207,319,344,371;
  dashboard_api.py:35,54,78; timetable_api.py multiple; api.py:352; context_builder.py:77;
  completion_manager.py:102,143; user_manger.py:78,107 streak/best-streak).
- `routes_api_utils.to_utc_from_user_input(...)` exists with `skip_conversion=True`
  (conversion off). Callers: timetable_api.py:38,153,235,250.
- `pytz==2025.2` already pinned. JS fallback `Intl.DateTimeFormat().resolvedOptions().timeZone
  || 'Africa/Nairobi'` in dashboard-garden-rpg.js:63 only.
- No `User.timezone` column; no Jinja tz filters; no `g.user`.

### Changes
1. **Migration** `migrations/versions/<hash>_user_timezone.py`:
   `with op.batch_alter_table('user')` → `add_column timezone String(64)`
   with `server_default='Africa/Nairobi'`, then `UPDATE` nulls, keep non-null.
2. **`app/models/user.py`**: `timezone = db.Column(db.String(64), nullable=False,
   server_default='Africa/Nairobi', default='Africa/Nairobi')` (create_all path for tests).
3. **`app/utils/timezones.py`** (new):
   - `DEFAULT_TIMEZONE = "Africa/Nairobi"`
   - `get_user_tz(user) -> pytz.timezone` (invalid → default)
   - `today_for(user) -> date` = `datetime.now(tz).date()`
   - `now_for(user) -> datetime` (tz-aware)
   - `utc_now_naive()` for storage (keeps existing naive-column style, guaranteed UTC)
   - `to_user_dt(naive_utc, tz) -> datetime` (localize→astimezone)
   - `to_utc_from_user_input(..., skip_conversion=False)` default flip after wiring callers.
4. **Store UTC where stored local**:
   - `JudgeReview.created_at/updated_at` → `utc_now_naive()` (defaults + `onupdate`).
   - `backup_service`: `_restore_judge_reviews` fallback datetimes → UTC naive;
     `exported_at` → `utc_now_naive().isoformat()`.
5. **User-local "today" everywhere day-scoped** (thread `user` / `user_id`):
   - `views.py` dashboard default date, `current_time_str`, stats `today`, profile `today`,
     backup filename date.
   - `dashboard_api.py:35,54,78` — `today_for`.
   - `timetable_api.py` `datetime.now()` sites that mean "today" → `today_for`.
   - `api.py:352` last-30-days.
   - `context_builder.py:77` now.
   - `completion_manager.py:102,143`.
   - `user_manger.py` `get_streak/get_best_streak` → add `today: date = None` param DEFAULTING
     to server date (back-compat), callers pass `today_for(user)`.
   - `task_scheduler` is date-injected already (`date_obj` from caller) → no change, callers fix.
6. **Jinja filters** (`app/init.py` + `timezones.py`):
   - `before_request` sets `g.user` (from session) and `g.user_tz`.
   - `{{ dt | udt }}` naive-UTC→user-tz ISO; `{{ dt | udate }}` → date str.
   - Used in `judge_log.html` (review.created_at/updated_at).
7. **`routes_api_utils.to_utc_from_user_input`**: kept `skip_conversion=True` (default) — the
   timetable callers parse HH:MM *wall-clock* times that are stored as-is in the user's local
   day; converting them through UTC would shift the clock for any non-UTC timezone. Genuine
   *instant* conversions go through the new `app/utils/timezones.py` helpers instead.
8. **Profile + capture**:
   - `profile.html`: timezone `<select>` (pytz names) + Save → `POST /api/prefs/timezone`.
   - `auth.js`/login page one-liner: `fetch('/api/prefs/timezone', … navigator… )` only when the
     stored account tz is still the default or absent.
   - `GET /api/prefs/timezone` for select current value.
9. **JS**: keep browser-local time displays; server payloads already render localized strings.
   Fix e2e seed "today" to use the seeded user tz (avoid midnight boundary flakes).

### Explicit non-goals
- No midnight-snap database column type changes. `completed_on`/`Timetable.date` remain
  `Date` (user-local calendar day, now guaranteed derived from user tz).
- No full calendar picker; `start_time/end_time` remain wall-clock.

---

## 3. Export / Import — schema v2, cross-account MERGE import

### Goal (user decisions locked)
1. **Import is a MERGE, never a replace.** Nothing is deleted. Conflicts keep the
   **target's** row, skip the imported copy, and are all **reported** on the import page.
   Report-and-continue (no blocking acknowledgement).
2. Import works **cross-account** (remove owner/username/email guard — it was a soft string
   check; backups carry no IDs).
3. Full import **preview** (dry-run simulation with counts + conflict lists + typo advisories)
   before any write.
4. **Identity / matching:** normalize (`strip()` → `lower()` → collapse inner spaces), then
   **exact match**. Case/whitespace variants = conflict; anything else = new.
   - Activity match → **do NOT recreate**, but **descend** into the target activity and merge
     sub-activities (each sub keyed on normalized `(activity name, sub name)` path).
   - SubActivity match inside matched parent → keep target/skip/report; unmatched → add.
   - Timetable: exact `date`. TimetableEntry: `(date, sub path, start_time)`.
   - CompletionLog: `(day = timetable date OR completed_on, activity path, sub path,
     start_time if present)`.
   - JudgeReview: follows its completion log; imported only if that log was newly added.
   - Re-importing the same file = no-op (all keys skip).
5. **Typo advisory only:** `difflib.SequenceMatcher.ratio() >= 0.80` between imported and a
   target name → listed under "possible duplicates (kept separate)" at activity and sub level.
   Never auto-merged, never blocking.
6. **Stats recompute after merge:** `total_exp = Σ exp_impact` over the merged union of logs
   (null/absent exp_impact counted as 0, noted in the report); `level` = highest
   `Level.level_number` with `required_exp <= total_exp` (curve `required_exp = 500*n`, from
   `e2e_seeds.ensure_levels` + `instance/rpg_system.db`); `INT/STA/FCS/CHA/DSC` stay the
   **target's** current values.
7. **Schema v2**: add `user.timezone` to export/import; retain `schema_version` check with
   tolerant read of v1 files (v1 → no timezone → import-time account default).
8. `password` never imported; imported username/email display-only.

### Current state (verified)
- `backup_service.py` FORMAT_ID `taskquest-backup`, SCHEMA_VERSION 1; full-replace restore;
  owner guard at L158-166; ID-free name/date lookups; robust `_parse_time`/`_find_sub`.
- Routes `views.py:363` `/export`, `:382` `/import` (POST, single file, flash+redirect).
- Profile UI: `profile.html:108-125` — replace wording, `onsubmit confirm('...REPLACE...')`.
- Level curve confirmed live: `required_exp = 500 * level_number` (20 rows in instance db).

### Changes to `backup_service.py`
1. `SCHEMA_VERSION = 2`; export gains `"timezone": user.timezone` in `user` section.
2. **New `app/utils/merge_matcher.py`** (keeps service readable):
   - `normalize(name)` trivial; `is_near_duplicate(a, b)` via `difflib >= 0.80`.
   - Entity key builders per rules above.
3. **`export_user_data`**: no behavior change except v2 + timezone + `exported_at` UTC.
4. **`import_user_data(user, payload, apply=True)`** → split into:
   - `preview_import(user, payload) -> ImportReport` — pure simulation, no writes, no
     exceptions on conflicts; returns `{added: {...counts}, skipped: {...} conflicts: [
     {entity, imported, matched_target, reason}], near_duplicates: [...], recompute:
     {prev_exp, new_exp, prev_level, new_level, attrs: 'kept'}, notes: [...]}`.
   - `import_user_data(user, payload, report: ImportReport = None)` — applies the merge in ONE
     transaction (rollback on any unexpected error); runs the same matching so the report
     matches what was written.
5. **Matcher internals:**
   - activity map (normalized name → target Activity) vs build.
   - sub path map per activity.
   - timetable date map; entry key = (sub resolved id, `start_time:MM:SS`).
   - log key = (`timetable_date or completed_on`, act key, sub key, start minutes if entry).
   - reviews only attach to logs that were actually added (link via the added log row id).
6. **Stats recompute** runs after successful merge (only when new logs were added):
   - ensure `Level` rows exist for needed thresholds (copy `ensure_levels`-style, up to what's
     needed) — do **not** overwrite existing Level rows.
   - `total_exp = Σ log.exp_impact or 0` across user's logs; `level` per rule.
7. **Remove the same-account guard** (owner/username/email checks at L158-166) — keep
   `format`/`schema_version` structural validation; unknown `format` still rejected.
8. **V1 file tolerance:** accept `schema_version: 1` (missing `timezone` → default), reject
   anything else.

### Routes & UI
1. **`views.py`**:
   - `POST /import/preview` — multipart upload → parse → `preview_import` → render an import
     **preview page** (new `templates/import_preview.html`) showing per-section added/skipped
     counts, the conflict list, near-duplicate advisories, recompute summary, and a
     "Confirm import" form carrying the same file bytes (hidden input, base64 or temp file on
     disk keyed by a short-lived token) → `POST /import`.
   - `POST /import` — now MERGE via `import_user_data`; flash report summary (added/skipped);
     redirect to profile.
   - `GET /export` unchanged (now emits v2).
2. **`profile.html`** Backup & Restore section: replace confirm dialog text ("Restore") with
   "This will MERGE the backup into your account; conflicting rows keep your existing data.
   You'll see a preview first." Button "Import Backup → review".
3. Password never touched; `_restore_user` dropped (stats now recomputed, attrs kept);

### Acceptance
- Export → import into a different account produces a union; conflicting rows keep target;
  report lists every skip; typo names appear in advisory.
- Import the same file twice → second report all-skipped, no duplicate rows.
- Import into fresh account == full restore (all added).
- Totals recomputed; level matches `500*n` curve; target attrs unchanged.

---

## 4. Seed dataset — `tests/seed_backup.json`

Inspired by `instance/rpg_system BACKUP FROM PYTHONANYWERE.db` (kim/test/Gatu users; 18
activities, 43 sub-activities, 29 logs, 20 timetables, 91 entries) and the live Level curve.

A single v2 backup-format JSON used by the test module and import previews. Includes:
- A `user` section (`username: ada`, INT/STA/FCS/CHA/DSC values, `timezone: Africa/Nairobi`,
  level/total_exp).
- Activities exercising the matcher deliberately:
  - `School` (subs `Math`, `English`) — target will also have `school` via case-conflict tests.
  - `Context Switch` (buffer) vs a misspelled `Contextswithc` typo pair.
  - `Personal` / `personal` case fold.
  - 3 more normal activities with 2 subs each.
- 4 timestamp-ordered timetables (2 with entries that also appear as completion logs) so
  round-trip ordering is deterministic.
- Completion logs with a mix of positive/negative `exp_impact` (recompute sums to a known value)
  with `comment: "SEED"` marker; absent `exp_impact` on one log (counted 0).
- 2 judge reviews attached to imported logs with the fallback marker explanation (provisional).
- Dates fixed (e.g. 2026-05-04 … 2026-05-07) so tests are deterministic regardless of run day.

---

## 5. Test module — split into logical `.py` files

Root: `tests/` (pytest, sqlite-in-temp via `TASKQUEST_DATABASE_URL`). Existing
`tests/e2e/run_e2e.py` stays a separate playwright gate.

```
tests/
  conftest.py                # app/db/client fixtures; temp db; Level rows; user fixture
  seed_backup.json            # §4 seed used by backup/merge/preview tests
  test_timezone.py            # tz util, today_for, migration column, streak today threading,
                              # JudgeReview UTC storage, udt/udate filters, /api/prefs/timezone
  test_judge.py               # timeout env-override, health_check reachable/refused,
                              # /api/judge/health states, provisional marker detection,
                              # openai pinned in requirements.txt
  test_export_format.py       # v2 marker, timezone present, exports match re-import, no IDs
  test_import_merge.py        # merge rules: case conflict, descend-into-sub, sub add,
                              # timetable/entry dedupe, log dedupe, idempotent re-import,
                              # near-duplicate advisory, stats recompute + level curve,
                              # attrs kept, cross-account OK, v1 tolerance, invalid format
  test_import_preview.py      # preview==apply parity, counts, conflict list, token flow
  e2e/run_e2e.py              # existing end-to-end gate (unchanged)
```

`conftest.py` fixtures:
- `app` — fresh `create_app()` with `TASKQUEST_DATABASE_URL` → temp file; `db.create_all()`;
  `ensure_levels(80)`-style Level rows.
- `client` — Flask test client; `user` — seeded account; `other_user` — cross-account import
  target; `seed_payload` — loads `seed_backup.json`.
- `judge_off_env` — monkeypatched env `OMNIROUTE_URL=http://127.0.0.1:9/v1` +
  `OMNIROUTE_TIMEOUT=0.5` for fast-fail judge tests.

Test command (document in plan + README):
```
cd TaskQuest
venv\Scripts\python -m pytest tests -q
venv\Scripts\python tests\e2e\run_e2e.py --headed --port 5055   # verification gate
```

---

## 6. Verification sequence (final gate)
1. `python -m pytest tests -q` — all new modules green.
2. `python tests\e2e\run_e2e.py --headed --port 5055` — 10/10 steps green.
3. Manual: Profile → export → import into a second account with pre-existing data → confirm
   merge + conflict report + recomputed total/level on the dashboard.
4. Judge pill: with OmniRoute up (LIVE), with endpoint stopped (OFF + provisional), with
   `OMNIROUTE_TIMEOUT` env override verifying non-hardcoded timeout.
5. No regression on the 1920×1080 layout round (garden dashboard still renders at 190px stat
   cards — the new pill must not overflow the topbar).

## Out of scope / follow-up
- Deleting the orphan `GET /api/system-judge/latest` route is folded in §1 only if harmless.
- Committing all of the above (explicit permission required).