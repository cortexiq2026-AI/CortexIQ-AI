/**
 * Minimal end-to-end example using the TypeScript SDK against a running
 * AI Completeness Checker REST API instance.
 *
 * Prerequisites:
 *   1. Start the API (from packages/api-py): uvicorn main:app --port 8788
 *   2. cd packages/sdk-ts && npm install && npm run build
 *
 * Run:
 *   node --experimental-strip-types typescript_quickstart.ts
 *   (or compile with tsc first, then `node typescript_quickstart.js`)
 */
import { CheckerClient } from "../packages/sdk-ts/src/index";

const ANSWER_FROM_SOME_OTHER_MODEL = `
Our authentication system uses OAuth2 with JWT tokens for session management.
Users log in via their corporate SSO provider, and tokens expire after 24
hours. For authorization, we use role-based access control with three tiers:
admin, editor, and viewer. All data in transit is encrypted using TLS 1.3,
and data at rest is encrypted with AES-256.
`.trim();

async function main() {
  const client = new CheckerClient({ baseUrl: "http://localhost:8788" });

  const report = await client.check({
    answer: ANSWER_FROM_SOME_OTHER_MODEL,
    document_type: "security architecture",
    expected_topics: [
      "Authentication",
      "Authorization",
      "Encryption",
      "Logging and Monitoring",
      "Functionality Overview",
      "Risks and Threat Model",
    ],
    auto_derive_topics: false,
  });

  console.log(`Completeness score: ${report.completeness_score}/100`);
  console.log(report.summary);
  console.log();

  for (const c of report.topic_coverage) {
    console.log(`${c.topic.name.padEnd(28)} ${c.status.padEnd(20)} ${c.quality}`);
    console.log(`    ${c.explanation}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
