#!/usr/bin/env bash
# Cleanup of dead one-off scripts identified by the engineering audit.
# Review before running; each path is one I verified is not imported anywhere.
# Run from the repository root:
#   bash scripts/cleanup_dead_files.sh
set -euo pipefail

cd "$(dirname "$0")/.."

DEAD_BACKEND=(
  # Diagnostic / debug scripts (none imported by runtime modules)
  backend/_check_db.py
  backend/_create_user.py
  backend/_seed_all.py
  backend/_test.json
  backend/check_cmms_data.py
  backend/check_duplicates.py
  backend/check_no_scores.py
  backend/check_obs.py
  backend/check_question_match.py
  backend/check_report_content.py
  backend/check_report_data.py
  backend/check_responses.py
  backend/check_scores.py
  backend/clean_current_duplicates.py
  backend/cleanup_duplicate_responses.py
  backend/create_admin_fix.py
  backend/create_local_user.py
  backend/debug_responses.py
  backend/debug_responses_query.py
  backend/delete_all_responses.py
  backend/fix_local_admin.py
  # One-off ad-hoc migrations superseded by run_migrations()
  backend/add_finalized_at.py
  backend/migrate_add_draft_na.py
  backend/migrate_add_iso_criticality.py
  # Data cleanup scripts (DANGEROUS — keep one in a tools/ dir if needed)
  backend/remove_duplicates.py
  backend/rescore_responses.py
  # Seeds not called by init_db.py
  backend/seed_checklist_observations.py
  backend/seed_responses.py
  backend/seed_sample_assessments.py
  backend/seed_vnext.py
  # Ad-hoc tests not in pytest layout
  backend/test_cmms_upload.py
  backend/test_data_saving.py
  backend/test_local.py
  backend/test_report_with_cmms.py
  backend/test_response.py
  # Misc one-offs
  backend/update_iso_mappings.py
  backend/update_response_texts.py
  backend/verify_all_scores.py
  backend/init_local_db.py
)

DEAD_ROOT=(
  # Replaced by init_db.py with INITIAL_ADMIN_* env vars
  create_admin.py
  create_local_admin.py
  # Replaced by `uvicorn main:app` from README
  start_backend.bat
  start_frontend.bat
)

echo "Removing dead backend scripts…"
for f in "${DEAD_BACKEND[@]}"; do
  if [[ -e "$f" ]]; then
    rm -f -- "$f"
    echo "  removed $f"
  fi
done

echo "Removing dead root scripts…"
for f in "${DEAD_ROOT[@]}"; do
  if [[ -e "$f" ]]; then
    rm -f -- "$f"
    echo "  removed $f"
  fi
done

# Rename CMMS_INTEGRATION_GUIDE.py (it is docs in a .py file)
if [[ -f backend/CMMS_INTEGRATION_GUIDE.py ]]; then
  mv backend/CMMS_INTEGRATION_GUIDE.py backend/CMMS_INTEGRATION_GUIDE.md
  echo "  renamed backend/CMMS_INTEGRATION_GUIDE.py -> .md"
fi

echo "Done."
