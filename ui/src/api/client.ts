import {
  AuthSessionStatus,
  ConfigPresetSummary,
  JobArtifactsResponse,
  JobDetail,
  JobSummary,
  SessionSummary
} from "../types";

const REQUEST_TIMEOUT_MS = 15_000;
const READ_REQUEST_ATTEMPTS = 3;
const WRITE_REQUEST_ATTEMPTS = 1;

function requestHeaders(init?: RequestInit): Headers {
  return new Headers(init?.headers || {});
}

function isDatabaseLocked(message: string): boolean {
  return /database is locked/i.test(message);
}

function isIdempotentReadMethod(method: string): boolean {
  return method === "GET" || method === "HEAD" || method === "OPTIONS";
}

function parseRetryAfterMillis(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }
  return parsed * 1000;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const isReadMethod = isIdempotentReadMethod(method);
  const attempts = isReadMethod ? READ_REQUEST_ATTEMPTS : WRITE_REQUEST_ATTEMPTS;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch(url, {
        ...(init || {}),
        method,
        credentials: init?.credentials ?? "same-origin",
        headers: requestHeaders(init),
        signal: controller.signal
      });
    } catch (error) {
      const baseMessage = error instanceof Error ? error.message : "Request failed";
      const timeoutMessage =
        error instanceof Error && error.name === "AbortError"
          ? `Request timed out after ${REQUEST_TIMEOUT_MS}ms`
          : baseMessage;
      lastError = new Error(timeoutMessage);
      if (!isReadMethod || attempt === attempts - 1) {
        throw lastError;
      }
      await sleep(150 * (attempt + 1));
      continue;
    } finally {
      window.clearTimeout(timeoutId);
    }

    if (response.ok) {
      return (await response.json()) as T;
    }

    const text = await response.text();
    const error = new Error(text || `Request failed (${response.status})`);
    lastError = error;
    const retryableReadError =
      isReadMethod && (response.status >= 500 || response.status === 429 || isDatabaseLocked(error.message));
    if (!retryableReadError || attempt === attempts - 1) {
      throw error;
    }

    const retryAfterMillis = parseRetryAfterMillis(response.headers.get("Retry-After"));
    await sleep(retryAfterMillis ?? 150 * (attempt + 1));
  }

  throw lastError ?? new Error("Request failed");
}

export function getAuthSessionStatus(): Promise<AuthSessionStatus> {
  return request<AuthSessionStatus>("/api/v1/auth/session");
}

export function loginAuthSession(apiKey: string): Promise<AuthSessionStatus> {
  return request<AuthSessionStatus>("/api/v1/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey })
  });
}

export function logoutAuthSession(): Promise<AuthSessionStatus> {
  return request<AuthSessionStatus>("/api/v1/auth/session", { method: "DELETE" });
}

export async function createProcessJob(payload: Record<string, unknown>): Promise<string> {
  const data = await request<{ job_id: string }>("/api/v1/jobs/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return data.job_id;
}

export async function createProcessJobWithFiles(formData: FormData): Promise<string> {
  const data = await request<{ job_id: string }>("/api/v1/jobs/process", {
    method: "POST",
    body: formData
  });
  return data.job_id;
}

export function listJobs(params?: { limit?: number; offset?: number }): Promise<JobSummary[]> {
  const query = new URLSearchParams();
  if (params?.limit) {
    query.set("limit", String(params.limit));
  }
  if (params?.offset) {
    query.set("offset", String(params.offset));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<JobSummary[]>(`/api/v1/jobs${suffix}`);
}

export function getJob(
  jobId: string,
  params?: { fileLimit?: number; eventLimit?: number }
): Promise<JobDetail> {
  const query = new URLSearchParams();
  if (params?.fileLimit) {
    query.set("file_limit", String(params.fileLimit));
  }
  if (params?.eventLimit) {
    query.set("event_limit", String(params.eventLimit));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<JobDetail>(`/api/v1/jobs/${jobId}${suffix}`);
}

export async function retryJobFailures(jobId: string): Promise<void> {
  await request(`/api/v1/jobs/${jobId}/retry-failures`, { method: "POST" });
}

export async function cleanupJobArtifacts(jobId: string): Promise<void> {
  await request(`/api/v1/jobs/${jobId}/artifacts`, { method: "DELETE" });
}

export function listJobArtifacts(jobId: string): Promise<JobArtifactsResponse> {
  return request<JobArtifactsResponse>(`/api/v1/jobs/${jobId}/artifacts`);
}

export function getJobArtifactDownloadUrl(jobId: string, artifactPath: string): string {
  return `/api/v1/jobs/${jobId}/artifacts/${encodeURIComponent(artifactPath)}`;
}

export function listSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>("/api/v1/sessions");
}

export function getEffectiveConfig(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/v1/config/effective");
}

export function listConfigPresets(): Promise<ConfigPresetSummary[]> {
  return request<ConfigPresetSummary[]>("/api/v1/config/presets");
}

export function getCurrentPreset(): Promise<string | null> {
  return request<{ preset: string | null }>("/api/v1/config/current-preset").then(
    (payload) => payload.preset
  );
}

export function previewConfigPreset(name: string): Promise<Record<string, unknown>> {
  return request<{ effective_config: Record<string, unknown> }>(
    `/api/v1/config/presets/${encodeURIComponent(name)}/preview`
  ).then((payload) => payload.effective_config);
}

export function applyConfigPreset(name: string): Promise<Record<string, unknown>> {
  return request<{ effective_config: Record<string, unknown> }>(
    `/api/v1/config/presets/${encodeURIComponent(name)}/apply`,
    { method: "POST" }
  ).then((payload) => payload.effective_config);
}
