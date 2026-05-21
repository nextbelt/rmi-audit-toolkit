#!/usr/bin/env bash
# Rotate every credential that was in supa_vars.json.
#
# Prereqs (you must be authenticated before running):
#   railway login            # opens browser; logs CLI into your Railway account
#   railway link             # select the rmi-audit-toolkit project
#   supabase login           # logs CLI in
#   # Supabase service-role key rotation is dashboard-only as of CLI 2.x.
#   # The script will print the dashboard URL when it gets there.
#
# Idempotent: re-running re-rotates. Each step exits non-zero on failure.
set -euo pipefail

cd "$(dirname "$0")/.."

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }
}
require railway
require supabase
require python

echo
echo "============================================================"
echo "  RMI Audit Toolkit — secret rotation"
echo "============================================================"
echo

# 1. Generate a strong new SECRET_KEY ───────────────────────────────
NEW_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
echo "[1/4] Generated new SECRET_KEY ($(echo -n "$NEW_SECRET_KEY" | wc -c) chars)"

# 2. Rotate Railway Postgres password ───────────────────────────────
# Railway exposes DATABASE_URL as a service variable; rotating the underlying
# Postgres password requires the Postgres plugin's "reset password" RPC.
echo "[2/4] Rotate Railway Postgres password"
echo "      Open Railway dashboard → Project → Postgres service →"
echo "      Variables → reset the POSTGRES_PASSWORD."
echo "      The connection string consumed by the backend (DATABASE_URL on"
echo "      the backend service) will be regenerated automatically."
echo
read -rp "Press Enter once you've rotated the Postgres password... " _

# 3. Push new SECRET_KEY + ENVIRONMENT to Railway backend ───────────
echo "[3/4] Set new SECRET_KEY and ENVIRONMENT=production on Railway backend"
railway variables --service rmi-audit-toolkit-backend \
  --set SECRET_KEY="$NEW_SECRET_KEY" \
  --set ENVIRONMENT="production"
echo "  ✓ pushed to Railway"

# 4. Rotate Supabase service-role + anon keys ───────────────────────
echo "[4/4] Rotate Supabase keys"
echo "      Open Supabase dashboard → Project Settings → API → Reveal"
echo "      'Project API keys', click 'Generate new' for both anon and"
echo "      service_role. Then paste the new service_role key here:"
read -rp "New SUPABASE_SERVICE_KEY: " NEW_SUPABASE_SERVICE_KEY
read -rp "New SUPABASE_ANON_KEY: " NEW_SUPABASE_ANON_KEY

railway variables --service rmi-audit-toolkit-backend \
  --set SUPABASE_SERVICE_KEY="$NEW_SUPABASE_SERVICE_KEY" \
  --set SUPABASE_ANON_KEY="$NEW_SUPABASE_ANON_KEY"

# Frontend only needs the anon key
railway variables --service rmi-audit-toolkit-frontend \
  --set VITE_SUPABASE_ANON_KEY="$NEW_SUPABASE_ANON_KEY"

echo "  ✓ pushed Supabase keys to Railway"

# Restart both services so they pick up the new env
railway redeploy --service rmi-audit-toolkit-backend
railway redeploy --service rmi-audit-toolkit-frontend

echo
echo "Rotation complete."
echo "Existing JWTs are now invalid; users must sign in again."
echo "If you have an active DB session pool, it will reconnect with the new password."
