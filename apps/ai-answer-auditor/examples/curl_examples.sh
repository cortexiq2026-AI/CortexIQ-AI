#!/usr/bin/env bash
# Example curl calls against a running AI Answer Auditor API instance.
#
# Prerequisites:
#   cd packages/api-py && uvicorn main:app --port 8787
#
# Run:
#   bash curl_examples.sh

set -euo pipefail

BASE_URL="${AUDITOR_API_URL:-http://localhost:8787}"

echo "== Health check =="
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo

echo "== Audit without source documents (web-search / no-evidence path) =="
curl -s -X POST "${BASE_URL}/audit" \
  -H "Content-Type: application/json" \
  -d '{
        "answer": "The Eiffel Tower was completed in 1889 and is 330 meters tall.",
        "question": "Tell me about the Eiffel Tower.",
        "sources": [],
        "allow_web_search": true
      }' | python3 -m json.tool

echo
echo "== Audit with a supplied source document =="
curl -s -X POST "${BASE_URL}/audit" \
  -H "Content-Type: application/json" \
  -d '{
        "answer": "The Eiffel Tower was completed in 1889 and is 330 meters tall.",
        "question": "Tell me about the Eiffel Tower.",
        "sources": [
          {
            "id": "eiffel_wiki",
            "title": "Eiffel Tower",
            "text": "The Eiffel Tower was constructed as the centerpiece of the 1889 World'\''s Fair in Paris. The tower stands 330 metres tall."
          }
        ],
        "allow_web_search": false
      }' | python3 -m json.tool
