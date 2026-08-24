import type { AuditRequest, AuditReport } from "./types";

export interface AuditorClientOptions {
  /** Base URL of a running ai-answer-auditor API instance, e.g. http://localhost:8787 */
  baseUrl: string;
  /** Optional fetch override, e.g. for auth headers or a custom runtime. */
  fetchImpl?: typeof fetch;
  /** Optional extra headers (e.g. Authorization) sent with every request. */
  headers?: Record<string, string>;
}

export class AuditorClientError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "AuditorClientError";
    this.status = status;
    this.body = body;
  }
}

/**
 * Thin HTTP client for the AI Answer Auditor REST API. Deliberately does not
 * reimplement the audit pipeline — it just calls the running Python service.
 * This keeps a single source of truth for the verification logic.
 */
export class AuditorClient {
  private baseUrl: string;
  private fetchImpl: typeof fetch;
  private headers: Record<string, string>;

  constructor(options: AuditorClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.headers = options.headers ?? {};
  }

  async audit(request: AuditRequest): Promise<AuditReport> {
    const response = await this.fetchImpl(`${this.baseUrl}/audit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.headers,
      },
      body: JSON.stringify(request),
    });

    const body = await response.json().catch(() => undefined);

    if (!response.ok) {
      const detail =
        body && typeof body === "object" && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : response.statusText;
      throw new AuditorClientError(`Audit request failed: ${detail}`, response.status, body);
    }

    return body as AuditReport;
  }

  async health(): Promise<{ status: string; llm_provider: string; search_provider: string }> {
    const response = await this.fetchImpl(`${this.baseUrl}/health`, { headers: this.headers });
    if (!response.ok) {
      throw new AuditorClientError("Health check failed", response.status, undefined);
    }
    return response.json();
  }
}
