import {
  ConfigPresetSummary,
  JobArtifactsResponse,
  JobDetail,
  JobSummary,
  SessionSummary
} from "../types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
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

export function listJobs(): Promise<JobSummary[]> {
  return request<JobSummary[]>("/api/v1/jobs");
}

export function getJob(jobId: string): Promise<JobDetail> {
  return request<JobDetail>(`/api/v1/jobs/${jobId}`);
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
