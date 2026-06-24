#!/bin/bash
set -e

export HOME=/home/frappe
export PYENV_ROOT=/home/frappe/.pyenv
export NVM_DIR=/home/frappe/.nvm
export PATH="/home/frappe/.local/bin:$PYENV_ROOT/shims:$PYENV_ROOT/bin:$NVM_DIR/versions/node/v24.13.0/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

BENCH_CMD="/home/frappe/.local/bin/bench"
PYTHON_CMD="/home/frappe/.pyenv/versions/3.14.2/bin/python3"

# Ensure bench CLI is installed for the active Python
if ! "$BENCH_CMD" --version &>/dev/null; then
  echo "Installing frappe-bench CLI..."
  "$PYTHON_CMD" -m pip install --user frappe-bench
fi

BENCH_BASE="/home/frappe/bench-data"
BENCH_DIR="$BENCH_BASE/frappe-bench"
SITE_NAME="hrms-main"
DB_ROOT_PASSWORD="admin123"

CUSTOM_APP_PATH="/workspace/custom_apps/wa_hr_api"
CUSTOM_APP_NAME="$(basename "$CUSTOM_APP_PATH")"
CUSTOM_APP_TARGET="$BENCH_DIR/apps/$CUSTOM_APP_NAME"

export UV_LINK_MODE=copy
export UV_HTTP_TIMEOUT=300
export UV_INDEX_URL=https://pypi.org/simple
export UV_CACHE_DIR="$BENCH_BASE/.uv-cache"

mkdir -p "$BENCH_BASE" "$UV_CACHE_DIR"
cd "$BENCH_BASE"

if [ ! -d "$BENCH_DIR/apps/frappe" ] || [ ! -f "$BENCH_DIR/sites/common_site_config.json" ]; then
  echo "Creating fresh bench..."
  rm -rf "$BENCH_DIR"

  "$BENCH_CMD" init \
    --frappe-branch version-16 \
    --python "$PYTHON_CMD" \
    --skip-redis-config-generation \
    frappe-bench
fi

cd "$BENCH_DIR"

"$BENCH_CMD" set-mariadb-host mariadb
"$BENCH_CMD" set-redis-cache-host redis://redis:6379
"$BENCH_CMD" set-redis-queue-host redis://redis:6379
"$BENCH_CMD" set-redis-socketio-host redis://redis:6379
python3 -c "
import json
cfg_path = 'sites/common_site_config.json'
with open(cfg_path) as f: cfg = json.load(f)
cfg['socketio_port'] = 9002
cfg['webserver_port'] = 8000
cfg['developer_mode'] = 1
with open(cfg_path, 'w') as f: json.dump(cfg, f, indent=1)
"

sed -i '/redis/d' Procfile || true
sed -i '/watch/d' Procfile || true

NODE_BIN="$NVM_DIR/versions/node/v24.13.0/bin/node"
if grep -q '^socketio:' Procfile; then
  sed -i "s|^socketio:.*|socketio: $NODE_BIN apps/frappe/socketio.js|" Procfile
else
  echo "socketio: $NODE_BIN apps/frappe/socketio.js" >> Procfile
fi

[ -d apps/erpnext ] || "$BENCH_CMD" get-app --branch version-16 erpnext
[ -d apps/hrms ] || "$BENCH_CMD" get-app --branch version-16 hrms

# Sync custom app AFTER bench exists
if [ -d "$CUSTOM_APP_PATH" ]; then
  echo "Syncing custom app: $CUSTOM_APP_NAME"
  rm -rf "$CUSTOM_APP_TARGET"
  mkdir -p "$(dirname "$CUSTOM_APP_TARGET")"
  cp -R "$CUSTOM_APP_PATH" "$CUSTOM_APP_TARGET"

  ./env/bin/pip install -e "$CUSTOM_APP_TARGET"

  {
    grep -v '^[[:space:]]*$' sites/apps.txt 2>/dev/null || true
    printf '%s\n' "$CUSTOM_APP_NAME"
  } | awk '!seen[$0]++' > sites/apps.txt.tmp

  mv sites/apps.txt.tmp sites/apps.txt
fi

until python3 -c "import socket; socket.create_connection(('mariadb',3306),2).close()"; do
  echo "Waiting for MariaDB..."
  sleep 2
done

if [ ! -d "$BENCH_DIR/sites/$SITE_NAME" ]; then
  "$BENCH_CMD" new-site "$SITE_NAME" \
    --db-host mariadb \
    --mariadb-root-password "$DB_ROOT_PASSWORD" \
    --admin-password admin \
    --no-mariadb-socket

  "$BENCH_CMD" --site "$SITE_NAME" install-app erpnext
  "$BENCH_CMD" --site "$SITE_NAME" install-app hrms
fi

if [ -d "$CUSTOM_APP_TARGET" ]; then
  if ! "$BENCH_CMD" --site "$SITE_NAME" list-apps | grep -qx "$CUSTOM_APP_NAME"; then
    "$BENCH_CMD" --site "$SITE_NAME" install-app "$CUSTOM_APP_NAME"
  fi
  "$BENCH_CMD" build --app "$CUSTOM_APP_NAME" || true
fi

"$BENCH_CMD" --site "$SITE_NAME" set-config developer_mode 1
"$BENCH_CMD" --site "$SITE_NAME" enable-scheduler
"$BENCH_CMD" use "$SITE_NAME"

exec "$BENCH_CMD" start