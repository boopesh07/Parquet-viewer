#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend/parquetformatter_api"
ENV_FILE="$ROOT_DIR/backend/.env.production"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID in your environment or backend/.env.production}"
: "${SUPABASE_URL:?Set SUPABASE_URL before deploying}"
: "${SUPABASE_SERVICE_ROLE_KEY:?Set SUPABASE_SERVICE_ROLE_KEY before deploying}"

TEMP_APP_FILE=$(mktemp)
cat "$BACKEND_DIR/app.yaml" > "$TEMP_APP_FILE"

python3 - <<'PY' >> "$TEMP_APP_FILE"
import os

pairs = {
    "SUPABASE_URL": os.environ["SUPABASE_URL"],
    "SUPABASE_SERVICE_ROLE_KEY": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    "SUPABASE_FEEDBACK_TABLE": os.environ.get("SUPABASE_FEEDBACK_TABLE", "feedback"),
    "SUPABASE_SESSION_TABLE": os.environ.get("SUPABASE_SESSION_TABLE", "session_metrics"),
    "ENABLE_GCP_LOGGING": os.environ.get("ENABLE_GCP_LOGGING", "true"),
    "GCP_LOG_NAME": os.environ.get("GCP_LOG_NAME", "parquetformatter-backend"),
}

extra = os.environ.get("ADDITIONAL_ENV_VARS")
if extra:
    for item in extra.split(','):
        if not item.strip():
            continue
        if '=' not in item:
            raise SystemExit(f"Invalid ADDITIONAL_ENV_VARS entry: {item}")
        key, value = item.split('=', 1)
        pairs[key.strip()] = value

def escape(val: str) -> str:
    return val.replace('\\', '\\\\').replace('"', '\\"')

print('\n# Injected environment variables')
print('env_variables:')
for key, value in pairs.items():
    print(f'  {key}: "{escape(value)}"')
PY

APP_YAML="$BACKEND_DIR/app.yaml"
BACKUP_APP_FILE=$(mktemp)
cp "$APP_YAML" "$BACKUP_APP_FILE"
mv "$TEMP_APP_FILE" "$APP_YAML"

cleanup() {
  mv "$BACKUP_APP_FILE" "$APP_YAML"
}
trap cleanup EXIT

echo "▶︎ Deploying backend to Google App Engine project $GCP_PROJECT_ID"
(cd "$BACKEND_DIR" && gcloud app deploy "$APP_YAML" --project "$GCP_PROJECT_ID" --quiet)

trap - EXIT
cleanup

rm -f "$BACKUP_APP_FILE"

echo '✅ Backend deployment complete'
