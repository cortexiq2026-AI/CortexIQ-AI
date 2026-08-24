#!/usr/bin/env bash
# Example curl calls against a running AI Completeness Checker API instance.
#
# Prerequisites:
#   cd packages/api-py && uvicorn main:app --port 8788
#
# Run:
#   bash curl_examples.sh

set -euo pipefail

BASE_URL="${CHECKER_API_URL:-http://localhost:8788}"

echo "== Health check =="
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo

echo "== Check with explicit expected topics =="
curl -s -X POST "${BASE_URL}/check" \
  -H "Content-Type: application/json" \
  -d '{
        "answer": "Our authentication system uses OAuth2 with JWT tokens. Authorization uses role-based access control. All data in transit is encrypted with TLS 1.3.",
        "document_type": "security architecture",
        "expected_topics": ["Authentication", "Authorization", "Encryption", "Logging", "Risks"],
        "auto_derive_topics": false
      }' | python3 -m json.tool

echo
echo "== Check with auto-derived topics from a question =="
curl -s -X POST "${BASE_URL}/check" \
  -H "Content-Type: application/json" \
  -d '{
        "answer": "Our authentication system uses OAuth2 with JWT tokens. Authorization uses role-based access control. All data in transit is encrypted with TLS 1.3.",
        "question": "Describe the security architecture of the system.",
        "document_type": "security architecture",
        "auto_derive_topics": true
      }' | python3 -m json.tool
