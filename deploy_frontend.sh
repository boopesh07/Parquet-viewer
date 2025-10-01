#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
ENV_FILE="$FRONTEND_DIR/.env.production"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

: "${VERCEL_TOKEN:?Set VERCEL_TOKEN in environment or frontend/.env.production}"
: "${PRODUCTION_BACKEND_URL:?Set PRODUCTION_BACKEND_URL with your deployed API URL}"
VITE_BACKEND_URL="${VITE_BACKEND_URL:-$PRODUCTION_BACKEND_URL}"

DEFAULT_GIT_NAME=$(git -C "$ROOT_DIR" config user.name 2>/dev/null || echo "$USER")
DEFAULT_GIT_EMAIL=$(git -C "$ROOT_DIR" config user.email 2>/dev/null || echo "")
VERCEL_GIT_NAME=${VERCEL_GIT_COMMIT_AUTHOR_NAME:-$DEFAULT_GIT_NAME}
VERCEL_GIT_EMAIL=${VERCEL_GIT_COMMIT_AUTHOR_EMAIL:-$DEFAULT_GIT_EMAIL}

if [ -z "$VERCEL_GIT_EMAIL" ]; then
  echo '❌ Set VERCEL_GIT_COMMIT_AUTHOR_EMAIL (or configure git user.email) to an email with access to the target Vercel team.' >&2
  exit 1
fi

# Ensure the local repo reports a member email so Vercel CLI validation passes
git -C "$ROOT_DIR" config user.email "$VERCEL_GIT_EMAIL"
git -C "$ROOT_DIR" config user.name "$VERCEL_GIT_NAME"

pushd "$FRONTEND_DIR" >/dev/null

yarn build

VERCEL_ARGS=(deploy --prod --yes --token "$VERCEL_TOKEN")
if [ -n "${VERCEL_SCOPE:-}" ]; then
  VERCEL_ARGS+=(--scope "$VERCEL_SCOPE")
fi

VERCEL_FORCE_NO_GIT=1 \
VERCEL_GIT_COMMIT_AUTHOR_NAME="$VERCEL_GIT_NAME" \
VERCEL_GIT_COMMIT_AUTHOR_EMAIL="$VERCEL_GIT_EMAIL" \
vercel "${VERCEL_ARGS[@]}" \
  --env "VITE_BACKEND_URL=${VITE_BACKEND_URL}" \
  --env "PRODUCTION_BACKEND_URL=${PRODUCTION_BACKEND_URL}"

popd >/dev/null

echo '✅ Frontend deployment complete'
