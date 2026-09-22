#!/usr/bin/env bash
#
# restart-taskquest.sh — deploy restarter for the homelab TaskQuest service.
#
# Flow (safe-by-default, aborts on error with rollback):
#   1. Backup the sacred DB (+ the app .env) into a timestamped folder.
#   2. (Optional) fast-forward to the deployed branch from origin.
#   3. Apply Alembic migrations (flask db upgrade).
#   4. Restart the systemd unit.
#   5. Health-check the app; on failure roll back DB + code and restart again.
#
# Designed for /home/ajay/apps/taskquest (git-linked repo, branch `dev`).
# systemctl needs sudo: run this script WITH sudo, or as a user authorized
# for the unit.
#
# Usage:
#   sudo bash deploy-scripts/restart-taskquest.sh            # keep current HEAD
#   sudo bash deploy-scripts/restart-taskquest.sh --pull      # git pull --ff-only first
#   sudo env DEPLOY_BRANCH=dev bash deploy-scripts/restart-taskquest.sh --pull
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ajay/apps/taskquest}"
BACKUP_ROOT="${BACKUP_ROOT:-/home/ajay/backups/taskquest-safe}"
SERVICE="${SERVICE:-taskquest.service}"
BRANCH="${DEPLOY_BRANCH:-dev}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:5055/}"
VENV_FLASK="${VENV_FLASK:-$APP_DIR/venv/bin/flask}"

cd "$APP_DIR"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TS"
mkdir -p "$BACKUP_DIR"

log()  { echo "[$(date +%H:%M:%S)] $*"; }
fail() { log "FATAL: $*"; exit 1; }

# ── 1. Backups ─────────────────────────────────────────────────────────────
log "backing up DB + env -> $BACKUP_DIR"
if [ -f instance/rpg_system.db ]; then
    cp -p instance/rpg_system.db "$BACKUP_DIR/rpg_system.db"
else
    log "WARNING: instance/rpg_system.db not found; skipping DB backup"
fi
[ -f .env ] && cp -p .env "$BACKUP_DIR/env.backup" || true

BEFORE="$(git rev-parse --short HEAD 2>/dev/null || echo untracked)"
log "deploying from HEAD $BEFORE"

# ── 2. Pull (only with --pull) ─────────────────────────────────────────────
if [ "${1:-}" = "--pull" ]; then
    log "git fetch + fast-forward $BRANCH"
    git fetch origin
    git checkout "$BRANCH"
    git pull --ff-only origin "$BRANCH" || fail "git pull failed; not touching the service"
fi

# ── 3. Migrations ──────────────────────────────────────────────────────────
log "running flask db upgrade"
"$VENV_FLASK" db upgrade || { log "migration failed"; restore_and_restart; }

# ── 4. Restart + verify with rollback ──────────────────────────────────────
restore_and_restart() {
    log "ROLLING BACK to $BEFORE"
    if [ "$(git rev-parse --short HEAD 2>/dev/null || echo untracked)" != "$BEFORE" ]; then
        git reset --hard "$BEFORE" || true
    fi
    [ -f "$BACKUP_DIR/rpg_system.db" ] && cp -p "$BACKUP_DIR/rpg_system.db" instance/rpg_system.db
    [ -f "$BACKUP_DIR/env.backup" ] && cp -p "$BACKUP_DIR/env.backup" .env
    log "restarting service after rollback"
    systemctl restart "$SERVICE" || true
    exit 1
}
trap 'restore_and_restart' ERR

log "restarting $SERVICE"
systemctl restart "$SERVICE"

log "waiting for $HEALTH_URL"
for i in $(seq 1 30); do
    if curl -fsS -o /dev/null --max-time 5 "$HEALTH_URL"; then
        log "OK: service healthy after deploy"
        trap - ERR
        exit 0
    fi
    sleep 2
done

restore_and_restart