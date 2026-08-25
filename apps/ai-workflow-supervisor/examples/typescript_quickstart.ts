/**
 * Minimal end-to-end example using the TypeScript SDK against a running
 * AI Workflow Supervisor REST API instance.
 *
 * Prerequisites:
 *   1. Start the API (from packages/api-py): uvicorn main:app --port 8789
 *   2. cd packages/sdk-ts && npm install && npm run build
 *
 * Run:
 *   node --experimental-strip-types typescript_quickstart.ts
 *   (or compile with tsc first, then `node typescript_quickstart.js`)
 */
import { SupervisorClient } from "../packages/sdk-ts/src/index";

const TASK = "Research 3 cloud architecture options, compare them, find the costs, and recommend one.";

const INCOMPLETE_AGENT_OUTPUT = `
We looked at AWS and GCP for the new service. AWS EC2 t3.micro instances
run about $0.0104/hr on-demand, while GCP's e2-micro is roughly $0.0084/hr.
Both platforms offer autoscaling and managed Kubernetes. Azure was also
considered briefly. Overall, we recommend GCP for the lower compute cost.
`.trim();

async function main() {
  const client = new SupervisorClient({ baseUrl: "http://localhost:8789" });

  const report = await client.supervise({
    task: TASK,
    agent_output: INCOMPLETE_AGENT_OUTPUT,
  });

  console.log(`task_complete:    ${report.task_complete}`);
  console.log(`completion_score: ${report.completion_score}/100`);
  console.log(report.summary);

  if (report.blocking_failures.length > 0) {
    console.log("Blocking failures:");
    for (const failure of report.blocking_failures) {
      console.log(`  - ${failure}`);
    }
  }
  console.log();

  for (const r of report.item_results) {
    const marker = r.status === "satisfied" ? "PASS" : r.status === "partially_satisfied" ? "PART" : "FAIL";
    const req = r.item.required ? "required" : "optional";
    console.log(`[${marker.padStart(4)} | ${req.padStart(8)}] ${r.item.description}`);
    console.log(`           ${r.explanation}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
