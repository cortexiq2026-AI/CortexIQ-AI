import type { SupervisionRequest, SupervisionReport } from "./types";

export interface SupervisorClientOptions {
  /** Base URL of a running ai-workflow-supervisor API instance, e.g. http://localhost:8789 */
  baseUrl: string;
  /** Optional fetch override, e.g. for auth headers or a custom runtime. */
  fetchImpl?: typeof fetch;
  /** Optional extra headers (e.g. Authorization) sent with every request. */
  headers?: Record<string, string>;
}

export class SupervisorClientError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "SupervisorClientError";
    this.status = status;
    this.body = body;
  }
}

/**
 * Thin HTTP client for the AI Workflow Supervisor REST API. Deliberately
 * does not reimplement the supervision pipeline — it just calls the running
 * Python service, keeping a single source of truth for the completion-gate
 * logic.
 */
export class SupervisorClient {
  private baseUrl: string;
  private fetchImpl: typeof fetch;
  private headers: Record<string, string>;

  constructor(options: SupervisorClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.headers = options.headers ?? {};
  }

  async supervise(request: SupervisionRequest): Promise<SupervisionReport> {
    const response = await this.fetchImpl(`${this.baseUrl}/supervise`, {
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
      throw new SupervisorClientError(`Supervision request failed: ${detail}`, response.status, body);
    }

    return body as SupervisionReport;
  }

  async health(): Promise<{ status: string; llm_provider: string; search_provider: string }> {
    const response = await this.fetchImpl(`${this.baseUrl}/health`, { headers: this.headers });
    if (!response.ok) {
      throw new SupervisorClientError("Health check failed", response.status, undefined);
    }
    return response.json();
  }
}
