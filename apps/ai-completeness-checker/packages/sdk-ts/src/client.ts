import type { CompletenessRequest, CompletenessReport } from "./types";

export interface CheckerClientOptions {
  /** Base URL of a running ai-completeness-checker API instance, e.g. http://localhost:8788 */
  baseUrl: string;
  /** Optional fetch override, e.g. for auth headers or a custom runtime. */
  fetchImpl?: typeof fetch;
  /** Optional extra headers (e.g. Authorization) sent with every request. */
  headers?: Record<string, string>;
}

export class CheckerClientError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "CheckerClientError";
    this.status = status;
    this.body = body;
  }
}

/**
 * Thin HTTP client for the AI Completeness Checker REST API. Deliberately
 * does not reimplement the analysis pipeline — it just calls the running
 * Python service, keeping a single source of truth for the logic.
 */
export class CheckerClient {
  private baseUrl: string;
  private fetchImpl: typeof fetch;
  private headers: Record<string, string>;

  constructor(options: CheckerClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.headers = options.headers ?? {};
  }

  async check(request: CompletenessRequest): Promise<CompletenessReport> {
    const response = await this.fetchImpl(`${this.baseUrl}/check`, {
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
      throw new CheckerClientError(`Completeness check failed: ${detail}`, response.status, body);
    }

    return body as CompletenessReport;
  }

  async health(): Promise<{ status: string; llm_provider: string }> {
    const response = await this.fetchImpl(`${this.baseUrl}/health`, { headers: this.headers });
    if (!response.ok) {
      throw new CheckerClientError("Health check failed", response.status, undefined);
    }
    return response.json();
  }
}
