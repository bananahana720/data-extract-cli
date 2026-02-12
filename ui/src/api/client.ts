import {
  ConfigPresetSummary,
  JobArtifactsResponse,
  JobDetail,
  JobSummary,
  SessionSummary
} from "../types";

function isDatabaseLocked(message: string): boolean {
  return /database is locked/i.test(message);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function request<T>(url: string, init?: RequestInit, attempts = 3): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const response = await fetch(url, init);
    if (response.ok) {
      return (await response.json()) as T;
    }

    const text = await response.text();
    const error = new Error(text || `Request failed (${response.status})`);
    lastError = error;
    if (!isDatabaseLocked(error.message) || attempt === attempts - 1) {
      throw error;
    }

    await sleep(150 * (attempt + 1));
  }

  throw lastError ?? new Error("Request failed");
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
