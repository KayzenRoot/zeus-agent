#!/usr/bin/env bash
# Zeus controlled update (interim channel until the Zeus-owned installer exists,
# see .zeus/docs/work-orders/ZEUS-001-installer-local-design.md and
# .zeus/docs/deployment-vps.md section 7).
#
#   zeus_update.sh --check    show incoming commits, change nothing
#   zeus_update.sh --apply    fetch, switch to the audited remote main, rebuild
#                             the container, health-check, auto-rollback on failure
#
# Safety properties: refuses any origin that is not the Zeus repository, never
# downloads from the Nous infrastructure, records both SHAs before switching,
# and rolls back automatically when the rebuilt stack fails its health check.
set -euo pipefail

REPO_DIR="${ZEUS_UPDATE_REPO:-$(pwd)}"
COMPOSE_DIR="${ZEUS_UPDATE_COMPOSE_DIR:-$REPO_DIR}"
ALLOWED_ORIGIN="https://github.com/KayzenRoot/zeus-agent.git"
ALLOWED_ORIGIN_SSH="git@github.com:KayzenRoot/zeus-agent.git"
HEALTH_URL="${ZEUS_UPDATE_HEALTH_URL:-http://127.0.0.1:9119/api/health}"
HEALTH_TIMEOUT="${ZEUS_UPDATE_HEALTH_TIMEOUT:-60}"

mode="${1:-}"
case "$mode" in
  --check|--apply) ;;
  *) echo "usage: $0 --check | --apply" >&2; exit 2 ;;
esac

cd "$REPO_DIR"

origin_url="$(git remote get-url origin)"
if [ "$origin_url" != "$ALLOWED_ORIGIN" ] && [ "$origin_url" != "$ALLOWED_ORIGIN_SSH" ]; then
  echo "REFUSING: origin is '$origin_url' — this script only updates from $ALLOWED_ORIGIN" >&2
  exit 2
fi

git fetch origin main

old_sha="$(git rev-parse HEAD)"
new_sha="$(git rev-parse origin/main)"
incoming="$(git log --oneline "$old_sha..$new_sha" | wc -l)"

echo "current: $old_sha"
echo "target:  $new_sha ($incoming new commit(s))"
if [ "$old_sha" = "$new_sha" ]; then
  echo "already up to date."
  exit 0
fi
git log --oneline "$old_sha..$new_sha"

if [ "$mode" = "--check" ]; then
  echo "check only — nothing changed. Run with --apply to update."
  exit 0
fi

git checkout "$new_sha"
echo "checked out $new_sha — rebuilding..."

if ! (cd "$COMPOSE_DIR" && docker compose build && docker compose up -d); then
  echo "BUILD/UP FAILED — rolling back to $old_sha" >&2
  git checkout "$old_sha"
  (cd "$COMPOSE_DIR" && docker compose build && docker compose up -d)
  exit 1
fi

echo "waiting for /api/health (timeout ${HEALTH_TIMEOUT}s)..."
healthy=false
for _ in $(seq 1 "$HEALTH_TIMEOUT"); do
  if curl -sf --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
    healthy=true
    break
  fi
  sleep 1
done

if [ "$healthy" = true ]; then
  echo "UPDATE OK: $old_sha -> $new_sha (health check passed)"
else
  echo "HEALTH CHECK FAILED — rolling back to $old_sha" >&2
  git checkout "$old_sha"
  (cd "$COMPOSE_DIR" && docker compose build && docker compose up -d)
  exit 1
fi
