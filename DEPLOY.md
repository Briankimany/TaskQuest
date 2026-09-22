# Deployment Guide

TaskQuest is a Flask (`app/init.py:create_app()`) application backed by
Flask-SQLAlchemy. It has no PaaS-coupled code, so it runs anywhere that can
host a WSGI app. This guide covers local development and a minimal
PythonAnywhere deployment.

## 1. Local development

```bat
venv\Scripts\python -m venv venv        REM create a venv once
venv\Scripts\pip install -r app\requirements.txt
```

Create a `.env` next to the project root (auto-loaded by `app/config.py`):

```
FLASK_DEBUG=1
SECRET_KEY=change-me
TASKQUEST_DATABASE_URL=sqlite:///C:/absolute/path/taskquest.db
OMNIROUTE_URL=http://127.0.0.1:20128/v1
OMNIROUTE_MODEL=free-coders
```

Run:

```bat
set FLASK_DEBUG=0
venv\Scripts\python -c "from app.init import create_app; app=create_app(); app.run(host='127.0.0.1', port=5055)"
```

Point your browser at `http://127.0.0.1:5055`.

## 2. Configuration reference (environment variables)

| Variable | Purpose | Default |
| --- | --- | --- |
| `TASKQUEST_DATABASE_URL` | SQLAlchemy database URL (MySQL / Postgres / SQLite) | `sqlite:///<instance>/rpg_system.db` |
| `SECRET_KEY` | Flask sessions. Set a long random value in production. | `dev` |
| `FLASK_DEBUG` | `1` shows Werkzeug tracebacks, `0` renders friendly 500 pages | `0` |
| `OMNIROUTE_URL` | Base URL of the LLM/OpenAI-compatible proxy used for penalty & late-task evaluation | from `app/seed/data/assistant/provider_config.yaml` |
| `OMNIROUTE_MODEL` | Model (or OmniRoute combo id) sent to the proxy | `free-coders` (see `provider_config.yaml`) |
| `OMNIROUTE_API_KEY` | Bearer key for the proxy on Windows/dev boxes | — |
| `OMNIROUTE_TASKQUEST_API_KEY` | Bearer key for the proxy on Linux/homelab | — |
| `APP_NAME` | Brand name shown in templates | `TaskQuest` |
| `APP_TAGLINE` | Tagline shown on the landing page | `A framework for intentional living` |
| `TESTING_KEY` | Auto-generated on first boot if absent | random UUID |
| `SUPPORT_EMAIL` / `SUPPORT_MAIL` | Contact address on the 404 page | `support@testingdomain.com` |
| `LOGGING_LEVEL` | Python logging level | `DEBUG` |

> If `OMNIROUTE_URL` is unreachable, the app never hangs: penalty/late-task
> evaluation falls back instantly to deterministic multipliers.

`OMNIROUTE_MODEL` is an OmniRoute **combo** id (e.g. `free-coders`, which routes
to a freelancer-tier model combo). The combo's provider connection is
authenticated server-side inside OmniRoute, so TaskQuest sends no per-request
session id. The gateway does however require a Bearer key, read from a
platform-aware env var (Windows/`OMNIROUTE_API_KEY`, Linux/`OMNIROUTE_TASKQUEST_API_KEY`);
see `app/utils/managers/ai_assistant.py` and `provider_config.yaml`.

## 3. PythonAnywhere (free tier)

1. **Upload the repo** and create a virtualenv:

   ```bash
   mkvirtualenv --python=python3.10 taskquest
   pip install -r app/requirements.txt
   ```

2. **Set environment variables** in the PythonAnywhere "Web > Environment"
   panel, or export them in a `~/.bashrc`-sourced file. At minimum:

   ```
   TASKQUEST_DATABASE_URL=mysql+mysqldb://USER:PASS@USER.mysql.pythonanywhere-services.com/USER$taskquest
   SECRET_KEY=<long random string>
   FLASK_DEBUG=0
   OMNIROUTE_URL=<your LLM proxy base, or leave unset for deterministic fallback>
   ```

   The integrated MySQL wizard under "Databases" will give you the exact URL.

3. **WSGI file** — replace the contents of the tab's `wsgi.py` with:

   ```python
   import os
   os.environ.setdefault("FLASK_DEBUG", "0")

   from app.init import create_app

   application = create_app()
   ```

4. **Static files.** The app already serves `/static` from `app/static`
   (Flask default with `Flask(__name__, instance_relative_config=True)`).
   Under PythonAnywhere you can optionally map a URL (*e.g.*
   `/static/`) to `/home/<user>/<project>/app/static` in the "Web > Static
   Files" section for better caching. Do **not** delete the
   `app/static/assets/img/backup_static_img/` folder.

5. **Database schema** is created automatically on first import
   (`db.create_all()` in `create_app()`). If you later change models, run a
   migration via the Flask-Migrate tooling in the repo.

6. **Enable HTTPS** and reload the web app from the PythonAnywhere "Web" tab.

## 4. Pre-deploy verification

Run the headed end-to-end suite (requires `pip install -r requirements-dev.txt`
and `playwright install chromium`):

```bat
venv\Scripts\python -c "from app.init import create_app; app=create_app(); app.run(port=5055)"  REM skip: runner starts its own server
set PYTHONPATH=%CD%
venv\Scripts\python tests\e2e\run_e2e.py --port 5055 --headless
```

Smoke-check export/import manually at `Profile -> Backup & Restore`:
export a JSON backup, then restore it and confirm your data reloads.

## 5. Backup & restore

Every account can download a single-file JSON backup from its **Profile**
page and restore it into the same account. Restoring **replaces** all data.
Only the account named in the backup file can restore it.