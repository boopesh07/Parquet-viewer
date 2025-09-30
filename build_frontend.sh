#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

pushd "$FRONTEND_DIR" >/dev/null

if [ ! -d node_modules ]; then
  echo '▶︎ Installing frontend dependencies'
  yarn install --frozen-lockfile
fi

echo '▶︎ Building frontend bundle'
yarn build

popd >/dev/null

echo '✅ Frontend build complete'
