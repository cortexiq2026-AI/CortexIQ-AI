#!/usr/bin/env bash
# Example curl calls against a running AI Workflow Supervisor API instance.
#
# Prerequisites:
#   cd packages/api-py && uvicorn main:app --port 8789
#
# Run:
#   bash curl_examples.sh

set -euo pipefail

BASE_URL="${SUPERVISOR_API_URL:-http://localhost:8789}"

echo "== Health check =="
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo

echo "== Supervise with auto-derived checklist (incomplete output) =="
curl -s -X POST "${BASE_URL}/supervise" \
  -H "Content-Type: application/json" \
  -d '{
        "task": "Research 3 cloud architecture options, compare them, find the costs, and recommend one.",
        "agent_output": "We looked at AWS and GCP. AWS costs $0.0104/hr, GCP costs $0.0084/hr. We recommend GCP.",
        "auto_derive_checklist": true
      }' | python3 -m json.tool

echo
echo "== Supervise with an explicit checklist =="
curl -s -X POST "${BASE_URL}/supervise" \
  -H "Content-Type: application/json" \
  -d '{
        "task": "Research 3 cloud architecture options, compare them, find the costs, and recommend one.",
        "agent_output": "We compared AWS, GCP, and Azure on cost and scalability. We recommend GCP.",
        "checklist": [
          "Compares at least 3 distinct cloud alternatives",
          "Collects pricing for each alternative",
          "Compares scalability",
          "Compares security",
          "States the pricing data as-of date",
          "Provides a final recommendation"
        ],
        "auto_derive_checklist": false
      }' | python3 -m json.tool
