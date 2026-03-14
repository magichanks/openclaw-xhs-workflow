#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <packs-root> <topic-slug> [YYYY-MM-DD]" >&2
  exit 1
fi

PACKS_ROOT="$1"
TOPIC_SLUG="$2"
POST_DATE="${3:-$(date +%F)}"
TARGET_DIR="${PACKS_ROOT}/${POST_DATE}-${TOPIC_SLUG}"

if [[ -e "${TARGET_DIR}" ]]; then
  echo "Pack already exists: ${TARGET_DIR}" >&2
  exit 1
fi

mkdir -p "${TARGET_DIR}/assets"

cat > "${TARGET_DIR}/brief.md" <<EOF
# Brief

- Date: ${POST_DATE}
- Topic slug: ${TOPIC_SLUG}
- Audience:
- Core value proposition:
- Evidence source:
- CTA:
- Must not claim:
- Competitive references:
EOF

cat > "${TARGET_DIR}/title.txt" <<'EOF'
Write one final title here.
EOF

cat > "${TARGET_DIR}/content.txt" <<'EOF'
Write the final XiaoHongShu body here.
EOF

cat > "${TARGET_DIR}/hashtags.txt" <<'EOF'
#example #workflow #draft
EOF

cat > "${TARGET_DIR}/asset_plan.md" <<'EOF'
# Asset Plan

## Cover
- Primary message:
- Source:
- Visual direction:
- Keep it to one image only:
- Redaction notes:
EOF

cat > "${TARGET_DIR}/research.md" <<'EOF'
# Research Summary

- Add research notes here.
EOF

cat > "${TARGET_DIR}/research.json" <<'EOF'
[]
EOF

cat > "${TARGET_DIR}/image_prompts.md" <<'EOF'
# Image Prompts

## Cover
- Goal:
- Prompt:
EOF

cat > "${TARGET_DIR}/review_checklist.md" <<'EOF'
# Review Checklist

- [ ] Claims are verified
- [ ] No private or sensitive data
- [ ] Title is specific
- [ ] CTA is explicit
EOF

cat > "${TARGET_DIR}/workflow_state.json" <<EOF
{
  "pack_id": "${POST_DATE}-${TOPIC_SLUG}",
  "mode": "save_draft",
  "state": "created",
  "owner": "xhs-orchestrator",
  "content_status": "pending",
  "image_status": "pending",
  "review_status": "pending",
  "publisher_status": "pending",
  "failed_reason": "",
  "last_step": "init",
  "updated_at": ""
}
EOF

cat > "${TARGET_DIR}/review_report.json" <<'EOF'
{
  "decision": "pending",
  "summary": "",
  "findings": [],
  "updated_at": ""
}
EOF

cat > "${TARGET_DIR}/publish_result.json" <<'EOF'
{
  "status": "pending",
  "mode": "",
  "title": "",
  "images": [],
  "note_url": "",
  "error": "",
  "updated_at": ""
}
EOF

cat > "${TARGET_DIR}/agent_runs.json" <<'EOF'
[]
EOF

echo "${TARGET_DIR}"
