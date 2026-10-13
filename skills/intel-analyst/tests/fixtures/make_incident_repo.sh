#!/usr/bin/env bash
# Build the investigation-scenario fixture: a small checkout service whose
# payment calls fail after a deploy.
#
# Planted cause: commit 3 changes the payment client to take a timeout in
# milliseconds, but RETRY_TIMEOUT in config.py stays 30 (it meant seconds).
# Misleading noise in logs/app.log: DNS slowness for the same host that began
# three hours before the deploy, and a GC pause after it.
#
# Usage: make_incident_repo.sh <empty-or-missing-dir>
set -euo pipefail

dir="${1:?usage: make_incident_repo.sh <dir>}"
mkdir -p "$dir"
cd "$dir"
if [ -n "$(ls -A .)" ]; then
  echo "error: $dir is not empty" >&2
  exit 1
fi

g() { git -c user.name=fixture -c user.email=fixture@example.invalid "$@"; }
commit() {
  local when="$1" msg="$2"
  g add -A
  GIT_AUTHOR_DATE="$when" GIT_COMMITTER_DATE="$when" g commit -q -m "$msg"
}

git init -q -b main

mkdir -p checkout
cat > checkout/payments.py <<'EOF'
import time
import urllib.request

PAYMENTS_URL = "http://payments.example.internal/charge"
RETRY_TIMEOUT = 30  # seconds
RETRIES = 3


def charge(order_id, amount_cents):
    body = f'{{"order": "{order_id}", "amount": {amount_cents}}}'.encode()
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(PAYMENTS_URL, data=body, method="POST")
            with urllib.request.urlopen(req, timeout=RETRY_TIMEOUT) as resp:
                return resp.status == 200
        except OSError:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"payment failed for order {order_id}")
EOF
cat > requirements.txt <<'EOF'
gunicorn==22.0.0
EOF
commit "2026-09-28T10:00:00Z" "Initial checkout service"

cat > checkout/config.py <<'EOF'
PAYMENTS_URL = "http://payments.example.internal/charge"
RETRY_TIMEOUT = 30  # seconds
RETRIES = 3
EOF
cat > checkout/payments.py <<'EOF'
import time
import urllib.request

from checkout.config import PAYMENTS_URL, RETRIES, RETRY_TIMEOUT


def charge(order_id, amount_cents):
    body = f'{{"order": "{order_id}", "amount": {amount_cents}}}'.encode()
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(PAYMENTS_URL, data=body, method="POST")
            with urllib.request.urlopen(req, timeout=RETRY_TIMEOUT) as resp:
                return resp.status == 200
        except OSError:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"payment failed for order {order_id}")
EOF
commit "2026-10-01T16:30:00Z" "Move payment settings into config module"

cat > checkout/http.py <<'EOF'
import urllib.request


def post(url, body, timeout_ms):
    """POST body to url. timeout_ms is the socket timeout in milliseconds."""
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
        return resp.status
EOF
cat > checkout/payments.py <<'EOF'
import time

from checkout.config import PAYMENTS_URL, RETRIES, RETRY_TIMEOUT
from checkout.http import post


def charge(order_id, amount_cents):
    body = f'{{"order": "{order_id}", "amount": {amount_cents}}}'.encode()
    for attempt in range(RETRIES):
        try:
            return post(PAYMENTS_URL, body, timeout_ms=RETRY_TIMEOUT) == 200
        except OSError:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"payment failed for order {order_id}")
EOF
commit "2026-10-06T13:55:00Z" "Route outbound calls through shared http helper"

cat > requirements.txt <<'EOF'
gunicorn==23.0.0
EOF
commit "2026-10-06T13:57:00Z" "Bump gunicorn to 23.0.0"

# Logs are runtime output, not part of the repository history.
mkdir -p logs
cat > logs/app.log <<'EOF'
2026-10-06T10:58:12Z INFO  checkout started version=2026.10.01
2026-10-06T11:04:40Z WARN  dns: slow resolution host=payments.example.internal elapsed_ms=1180
2026-10-06T11:31:02Z WARN  dns: slow resolution host=payments.example.internal elapsed_ms=1420
2026-10-06T12:15:19Z INFO  charge ok order=88121 elapsed_ms=212
2026-10-06T12:47:55Z WARN  dns: slow resolution host=payments.example.internal elapsed_ms=990
2026-10-06T13:20:08Z INFO  charge ok order=88342 elapsed_ms=1490
2026-10-06T13:41:33Z WARN  dns: slow resolution host=payments.example.internal elapsed_ms=1310
2026-10-06T14:00:05Z INFO  checkout started version=2026.10.06
2026-10-06T14:02:11Z ERROR charge failed order=88410 error="payment failed for order 88410" cause=socket.timeout attempts=3
2026-10-06T14:02:47Z ERROR charge failed order=88411 error="payment failed for order 88411" cause=socket.timeout attempts=3
2026-10-06T14:03:30Z WARN  dns: slow resolution host=payments.example.internal elapsed_ms=1250
2026-10-06T14:05:02Z WARN  gc: pause_ms=840 heap_mb=612
2026-10-06T14:05:40Z ERROR charge failed order=88415 error="payment failed for order 88415" cause=socket.timeout attempts=3
2026-10-06T14:09:13Z ERROR charge failed order=88419 error="payment failed for order 88419" cause=socket.timeout attempts=3
2026-10-06T14:12:58Z INFO  payments upstream health=ok p50_ms=180 p99_ms=900
2026-10-06T14:14:21Z ERROR charge failed order=88424 error="payment failed for order 88424" cause=socket.timeout attempts=3
EOF
echo "fixture ready: $dir"
