export type JobStatus = "queued" | "running" | "completed" | "partial" | "failed";

export interface SemanticArtifact {
  name: string;
  path: string;
  artifact_type: string;
  format?: string | null;
  size_bytes: number;
}

export interface SemanticOutcome {
  status: string;
  reason_code?: string | null;
  message?: string | null;
  summary?: Record<string, unknown>;
  artifacts?: SemanticArtifact[];
  stage_timings_ms?: Record<string, number>;
}

export interface ProcessResultPayload extends Record<string, unknown> {
  total_files?: number;
  processed_count?: number;
  failed_count?: number;
  skipped_count?: number;
  stage_totals_ms?: Record<string, number>;
  semantic?: SemanticOutcome;
}

export interface JobSummary {
  job_id: string;
  status: JobStatus;
  input_path: string;
  output_dir: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  session_id: string | null;
}

export interface JobDetail extends JobSummary {
  requested_format: string;
  chunk_size: number;
  updated_at: string;
  request_payload: Record<string, unknown>;
  result_payload: ProcessResultPayload;
  request_hash?: string | null;
  artifact_dir?: string | null;
  files: Array<{
    source_path: string;
    output_path: string | null;
    status: string;
    chunk_count: number;
    retry_count?: number;
    source_key?: string | null;
    error_type: string | null;
    error_message: string | null;
  }>;
  events: Array<{
    event_type: string;
    message: string;
    payload: Record<string, unknown>;
    event_time: string;
  }>;
}

export interface JobArtifactEntry {
  path: string;
  size_bytes: number;
  modified_at: string;
}

export interface JobArtifactsResponse {
  job_id: string;
  artifacts: JobArtifactEntry[];
}

export interface ConfigPresetSummary {
  name: string;
  category: string;
  description?: string | null;
  is_builtin: boolean;
}

export interface SessionSummary {
  session_id: string;
  status: string;
  source_directory: string;
  total_files: number;
  processed_count: number;
  failed_count: number;
  updated_at: string;
}

export interface AuthSessionStatus {
  authenticated: boolean;
  api_key_configured: boolean;
  expires_at: string | null;
}
