/**
 * Minimal end-to-end example using the TypeScript SDK against a running
 * AI Answer Auditor REST API instance.
 *
 * Prerequisites:
 *   1. Start the API (from packages/api-py): uvicorn main:app --port 8787
 *   2. cd packages/sdk-ts && npm install && npm run build
 *
 * Run:
 *   node --experimental-strip-types typescript_quickstart.ts
 *   (or compile with tsc first, then `node typescript_quickstart.js`)
 */
import { AuditorClient } from "../packages/sdk-ts/src/index";

const ANSWER_FROM_SOME_OTHER_MODEL = `
The Eiffel Tower was completed in 1889 for the World's Fair and stands 330
meters tall, making it the tallest structure in Paris. It was designed by
Gustave Eiffel and was originally intended to be dismantled after 20 years,
but it was kept because it proved useful for radio transmission.
`.trim();

const SOURCE_DOC = `
The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in
Paris, France. It was constructed as the centerpiece of the 1889 World's
Fair. The tower is 330 metres tall and was the tallest man-made structure in
the world for 41 years. It was to be dismantled in 1909, but was kept after
it proved valuable for communication purposes.
`.trim();

async function main() {
  const client = new AuditorClient({ baseUrl: "http://localhost:8787" });

  const report = await client.audit({
    answer: ANSWER_FROM_SOME_OTHER_MODEL,
    question: "Tell me about the Eiffel Tower.",
    sources: [{ id: "eiffel_wiki", title: "Eiffel Tower", text: SOURCE_DOC }],
  });

  console.log(`Verification score:  ${report.verification_score}/100`);
  console.log(`Completeness score:  ${report.completeness_score}/100`);
  console.log(`Total claims:        ${report.total_claims}`);
  console.log(`Unsupported claims:  ${report.unsupported_claims}`);
  console.log(`Contradicted claims: ${report.contradicted_claims}`);
  console.log(`Needs human review:  ${report.needs_human_review}`);
  console.log();
  console.log(report.summary);
  console.log();

  for (const v of report.claim_verifications) {
    console.log(`[${v.status.padStart(18)}] (${v.confidence.toFixed(2)}) ${v.claim.text}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
