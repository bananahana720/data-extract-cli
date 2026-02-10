export type JobStatus = "queued" | "running" | "completed" | "partial" | "failed";

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
  result_payload: Record<string, unknown>;
  files: Array<{
    source_path: string;
    output_path: string | null;
    status: string;
    chunk_count: number;
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

export interface SessionSummary {
  session_id: string;
  status: string;
  source_directory: string;
  total_files: number;
  processed_count: number;
  failed_count: number;
  updated_at: string;
}
