# TaskQuest

Turn your daily schedule into a game. Plan tasks, complete quests, earn EXP,
and level up — a gamified productivity engine backed by a Flask API.

## Highlights

- **Activities & sub-activities** — organize work into groups with RPG
  attributes (INT, STA, FCS, CHA, DSC) and per-task EXP.
- **Daily timetable** — schedule tasks for any day, mark tasks cyclic
  (repeat by weekday), get smart recurring-task suggestions, and let the
  scheduler insert short buffer breaks between tasks.
- **Quests & leveling** — complete tasks for EXP and level your character;
  the garden-RPG dashboard shows today's missions, XP progress, and a live
  discipline overview.
- **System Judge** — skip/late evaluations and penalties are scored by an
  LLM through an [OmniRoute](https://omniroute.local) combo, with a
  LIVE / PROVISIONAL / OFF status pill and a judge log.
- **Backup & restore** — single-file JSON export/import per account.
- **One-line regressions** — source-level verifiers plus Playwright probes
  gate every feature (see [Testing](#testing)).

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Flask, Flask-SQLAlchemy, Flask-Migrate |
| Database | SQLite (default), MySQL/Postgres via `TASKQUEST_DATABASE_URL` |
| LLM judge | OpenAI-compatible client against an OmniRoute gateway |
| Front-end | Server-rendered templates + vanilla JS/CSS, several themes |
| Tests | pytest + self-contained `verify_*.py` / `probe_*.py` runners |

## Quick start

```bat
python -m venv venv
venv\Scripts\pip install -r app\requirements.txt
set FLASK_DEBUG=1
venv\Scripts\python run.py
```

Create a `.env` next to the project root (auto-loaded by `app/config.py`):

```
SECRET_KEY=change-me
FLASK_DEBUG=1
```

Open <http://127.0.0.1:5000>. The database schema is created on first boot.

> **Note** — `OMNIROUTE_*` variables are optional. When the LLM gateway is
> unreachable or misconfigured, the System Judge falls back to deterministic
> scoring instead of hanging.

## OmniRoute / System Judge

Judge and penalty evaluation run through an OmniRoute combo rather than a
direct model key:

- **Combos carry provider auth.** A combo like `free-coders` resolves to a
  provider connection authenticated server-side in OmniRoute. TaskQuest sends
  no `x-opencode-session` header.
- **Bearer key is required.** The gateway rejects unauthenticated requests
  (`401 "Authentication required"`). The key is read from a platform-aware
  env var: `OMNIROUTE_API_KEY` on Windows/dev, `OMNIROUTE_TASKQUEST_API_KEY`
  on Linux/homelab.
- **Config**: `OMNIROUTE_URL` (gateway base) and `OMNIROUTE_MODEL` (combo id)
  override the defaults in `app/seed/data/assistant/provider_config.yaml`
  (default combo: `free-coders`).
- **Graceful fallback**: unreachable gateway → deterministic multipliers and
  `PROVISIONAL` verdicts, never a hang.

## Configuration

Full reference, including `TASKQUEST_DATABASE_URL`, `SECRET_KEY`,
`OMNIROUTE_URL` / `OMNIROUTE_MODEL` / auth keys, `APP_NAME`, and logging, is
in [DEPLOY.md](DEPLOY.md).

## Testing

```bat
venv\Scripts\python app\test\verify_tt.py          REM timetable regression gate (48 checks)
venv\Scripts\python app\test\verify_dashboard.py   REM garden dashboard gate (72 checks)
venv\Scripts\python app\test\verify_activities.py  REM activities view gate (61 checks)
venv\Scripts\python app\test\probe_mission_scroll.py --tasks 15   REM browser probe: filled missions card scroll
venv\Scripts\python app\test\probe_tt_edit.py      REM browser probe: edit-panel prefill
venv\Scripts\pytest tests                          REM unit tests
```

`verify_*.py` self-boot the app and check markup/CSS/JS against the spec;
`probe_*.py` drive a real (headless) browser and hit the live API for
behavioural coverage.

## Deployment

See [DEPLOY.md](DEPLOY.md) for local dev, the homelab service layout
(`taskquest.service` + nginx), and the
`deploy-scripts/restart-taskquest.sh` deploy script (DB backup → migrations →
service restart → automated rollback).

## Docs & API

- [API docs](https://cynic1.pythonanywhere.com/docs)