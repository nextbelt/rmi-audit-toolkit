#!/usr/bin/env bash
# Create the private "evidence" bucket in Supabase Storage and push the
# resulting bucket name to Railway env. Run once.
#
# Prereqs:
#   supabase login
#   railway login && railway link
set -euo pipefail

BUCKET="${SUPABASE_BUCKET:-evidence}"
PROJECT_REF="${SUPABASE_PROJECT_REF:-xfccxewswuovijuqfyos}"

echo "Creating private bucket '$BUCKET' on project $PROJECT_REF…"
supabase storage create "$BUCKET" --project-ref "$PROJECT_REF" --private || true

echo "Setting STORAGE_BACKEND=supabase and SUPABASE_BUCKET on Railway backend…"
railway variables --service rmi-audit-toolkit-backend \
  --set STORAGE_BACKEND="supabase" \
  --set SUPABASE_BUCKET="$BUCKET"

railway redeploy --service rmi-audit-toolkit-backend

echo
echo "Done. The backend will write new uploads to supabase://${BUCKET}/<path>."
echo "Old uploads stored on the Railway ephemeral disk are NOT migrated —"
echo "if you have any, copy them out before the next redeploy wipes them."
