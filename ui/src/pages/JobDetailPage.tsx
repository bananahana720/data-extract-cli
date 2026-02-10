import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { cleanupJobArtifacts, getJob, retryJobFailures } from "../api/client";
import { JobDetail } from "../types";

const STAGES = ["extract", "normalize", "chunk", "semantic", "output"];
const LIFECYCLE_ORDER = ["queued", "running", "finished", "cleanup", "error"];
const LIFECYCLE_LABELS: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  finished: "Finished",
  cleanup: "Cleanup",
  error: "Error"
};
type CopyStatus =
  | { kind: "success"; message: string }
  | { kind: "error"; message: string }
  | null;

function toNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function formatDuration(durationMs: number): string {
  if (!Number.isFinite(durationMs) || durationMs <= 0) {
    return "0s";
  }
  const totalSeconds = Math.floor(durationMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not available";
  }
  return new Date(value).toLocaleString();
}

function remediationHint(file: JobDetail["files"][number]): string {
  const errorType = (file.error_type || "").toLowerCase();
  const message = (file.error_message || "").toLowerCase();
  if (errorType.includes("permission") || message.includes("permission")) {
    return "Verify read permissions for this file, then run Retry Failed.";
  }
  if (errorType.includes("timeout") || message.includes("timed out")) {
    return "Retry Failed is recommended. If this repeats, reduce input size or system load.";
  }
  if (errorType.includes("notfound") || message.includes("not found")) {
    return "Confirm the file still exists at the original path before retrying.";
  }
  if (errorType.includes("unsupported") || message.includes("unsupported")) {
    return "Convert this file to a supported format, then rerun the job.";
  }
  return "Review the error details and use Retry Failed after addressing the root issue.";
}

export function JobDetailPage() {
  const { jobId = "" } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(null);

  useEffect(() => {
    let timer: number | undefined;

    async function refresh() {
      if (!jobId) {
        return;
      }

      try {
        const detail = await getJob(jobId);
        setJob(detail);
        setError(null);

        if (detail.status === "queued" || detail.status === "running") {
          timer = window.setTimeout(refresh, 1000);
        }
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load job";
        setError(message);
      }
    }

    void refresh();
    return () => {
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [jobId]);

  const stageTotals = useMemo(() => {
    const stageMap = (job?.result_payload?.stage_totals_ms as Record<string, number>) || {};
    return STAGES.map((name) => ({
      name,
      ms: Number(stageMap[name] || 0)
    }));
  }, [job]);
  const lifecycleEvents = useMemo(() => {
    if (!job) {
      return [];
    }
    const lifecycleTypes = new Set(LIFECYCLE_ORDER);
    return [...job.events]
      .filter((event) => lifecycleTypes.has(event.event_type))
      .sort((left, right) => Date.parse(left.event_time) - Date.parse(right.event_time));
  }, [job]);

  async function runRetry() {
    if (!jobId) {
      return;
    }
    setRetrying(true);
    try {
      await retryJobFailures(jobId);
      setJob(await getJob(jobId));
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Retry failed";
      setError(message);
    } finally {
      setRetrying(false);
    }
  }

  async function runCleanup() {
    if (!jobId) {
      return;
    }
    setCleaning(true);
    try {
      await cleanupJobArtifacts(jobId);
      setJob(await getJob(jobId));
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Cleanup failed";
      setError(message);
    } finally {
      setCleaning(false);
    }
  }

  async function copyOutputPath(path: string) {
    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard API unavailable");
      }
      await navigator.clipboard.writeText(path);
      setCopyStatus({ kind: "success", message: "Output path copied to clipboard." });
    } catch {
      setCopyStatus({
        kind: "error",
        message: "Unable to copy output path. Copy it manually from the summary."
      });
    }
  }

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!job) {
    return <p className="muted">Loading job details...</p>;
  }

  const failedFiles = job.files.filter((file) => file.status === "failed");
  const totalFiles = Math.max(job.files.length, toNumber(job.result_payload?.total_files, job.files.length));
  const processedFiles = Math.max(
    totalFiles - failedFiles.length,
    toNumber(job.result_payload?.processed_count, totalFiles - failedFiles.length)
  );
  const completedPercent = totalFiles > 0 ? Math.round((processedFiles / totalFiles) * 100) : 0;
  const boundedPercent = Math.min(Math.max(completedPercent, 0), 100);
  const skippedFiles = toNumber(job.result_payload?.skipped_count);
  const hasCleanupEvent = lifecycleEvents.some((event) => event.event_type === "cleanup");
  const isActive = job.status === "queued" || job.status === "running";
  const startedAtMs = job.started_at ? Date.parse(job.started_at) : NaN;
  const finishedAtMs = job.finished_at ? Date.parse(job.finished_at) : NaN;
  const elapsedDuration = Number.isFinite(startedAtMs)
    ? Number.isFinite(finishedAtMs)
      ? formatDuration(finishedAtMs - startedAtMs)
      : `${formatDuration(Date.now() - startedAtMs)} elapsed`
    : "Not started";
  const nextAction =
    isActive && job.status === "queued"
      ? "Wait for the worker to start processing."
      : isActive && job.status === "running"
        ? "Monitor progress. Retry and cleanup actions become available after terminal status."
        : failedFiles.length > 0
          ? "Use Retry Failed to reprocess only failed files."
          : hasCleanupEvent
            ? "Artifacts are already cleaned. Start a new run when ready."
            : "Review outputs, then use Cleanup Artifacts to remove persisted job files.";

  return (
    <section className="panel job-detail" data-testid="job-detail-page">
      <article className="summary-card" data-testid="job-summary-card">
        <div className="row-between">
          <div>
            <h2>Job {job.job_id}</h2>
            <p className="muted">Input: {job.input_path}</p>
            <p className="muted">Output: {job.output_dir}</p>
          </div>
          <span className={`status ${job.status}`} data-testid="job-status-chip">
            {job.status}
          </span>
        </div>
        <div className="summary-metrics">
          <article className="metric-card" data-testid="job-metric-total">
            <span>Total Files</span>
            <strong>{totalFiles}</strong>
          </article>
          <article className="metric-card" data-testid="job-metric-processed">
            <span>Processed</span>
            <strong>{processedFiles}</strong>
          </article>
          <article className="metric-card" data-testid="job-metric-failed">
            <span>Failed</span>
            <strong>{failedFiles.length}</strong>
          </article>
          <article className="metric-card" data-testid="job-metric-skipped">
            <span>Skipped</span>
            <strong>{skippedFiles}</strong>
          </article>
        </div>
        <article className="progress-card" data-testid="job-progress-card">
          <div className="row-between">
            <span>Processing Progress</span>
            <strong data-testid="job-progress-text">
              {processedFiles}/{totalFiles} ({boundedPercent}%)
            </strong>
          </div>
          <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={boundedPercent}>
            <div className="progress-fill" style={{ width: `${boundedPercent}%` }} />
          </div>
        </article>
        <dl className="key-value-list" data-testid="job-runtime-metadata">
          <dt>Created</dt>
          <dd>{formatDateTime(job.created_at)}</dd>
          <dt>Started</dt>
          <dd>{formatDateTime(job.started_at)}</dd>
          <dt>Finished</dt>
          <dd>{formatDateTime(job.finished_at)}</dd>
          <dt>Elapsed</dt>
          <dd>{elapsedDuration}</dd>
          <dt>Format</dt>
          <dd>{job.requested_format.toUpperCase()}</dd>
          <dt>Chunk Size</dt>
          <dd>{job.chunk_size}</dd>
        </dl>
        <p className="next-action" data-testid="job-next-action">
          <strong>Next Action:</strong> {nextAction}
        </p>
      </article>

      <article className="action-card">
        <h3>Actions</h3>
        <div className="actions-inline">
          <button
            onClick={runRetry}
            disabled={retrying || failedFiles.length === 0 || isActive}
            data-testid="job-action-retry"
          >
            {retrying ? "Retrying..." : `Retry Failed (${failedFiles.length})`}
          </button>
          <button
            onClick={runCleanup}
            disabled={cleaning || isActive || hasCleanupEvent}
            className="secondary"
            type="button"
            data-testid="job-action-cleanup"
          >
            {cleaning ? "Cleaning..." : "Cleanup Artifacts"}
          </button>
          <button
            onClick={() => copyOutputPath(job.output_dir)}
            className="secondary"
            type="button"
            data-testid="job-action-copy-output"
          >
            Copy Output Path
          </button>
        </div>
        <p className="help-text" data-testid="job-actions-hint">
          {isActive
            ? "Retry and cleanup stay disabled while the job is queued/running."
            : hasCleanupEvent
              ? "Artifacts are already cleaned."
              : "Use Retry Failed for failures or Cleanup Artifacts once review is complete."}
        </p>
        {copyStatus ? (
          <p
            className={`inline-alert ${copyStatus.kind === "error" ? "is-error" : "is-success"}`}
            aria-live="polite"
            data-testid="job-copy-status"
          >
            {copyStatus.message}
          </p>
        ) : null}
      </article>

      <h3>Lifecycle Timeline</h3>
      {lifecycleEvents.length === 0 ? (
        <p className="muted" data-testid="job-lifecycle-empty">
          No lifecycle events recorded yet.
        </p>
      ) : (
        <ol className="timeline-list" data-testid="job-lifecycle-timeline">
          {lifecycleEvents.map((event, index) => (
            <li
              key={`${event.event_type}-${event.event_time}-${index}`}
              className={`timeline-item ${event.event_type === "error" ? "is-error" : "is-complete"}`}
              data-testid={`job-timeline-item-${index}`}
            >
              <div className="timeline-marker" aria-hidden="true" />
              <div className="timeline-content">
                <div className="row-between timeline-header">
                  <strong>{LIFECYCLE_LABELS[event.event_type] || event.event_type}</strong>
                  <time dateTime={event.event_time}>
                    {new Date(event.event_time).toLocaleString()}
                  </time>
                </div>
                <p>{event.message || "Lifecycle event recorded."}</p>
              </div>
            </li>
          ))}
        </ol>
      )}

      <h3>Stage Timing</h3>
      <div className="stage-grid">
        {stageTotals.map((stage) => (
          <article key={stage.name} className="stage-card">
            <h3>{stage.name}</h3>
            <p>{stage.ms > 0 ? `${stage.ms.toFixed(1)} ms` : "pending"}</p>
          </article>
        ))}
      </div>

      <h3>Failures</h3>
      {failedFiles.length === 0 ? (
        <p className="muted" data-testid="job-failures-empty">
          No failed files.
        </p>
      ) : (
        <div className="failure-stack" data-testid="job-failure-list">
          {failedFiles.map((file) => (
            <article key={file.source_path} className="failure-card">
              <h4>{file.source_path}</h4>
              <dl>
                <dt>Error Type</dt>
                <dd>{file.error_type || "Unknown"}</dd>
                <dt>Error Message</dt>
                <dd>{file.error_message || "Unknown error"}</dd>
                <dt>Retry Count</dt>
                <dd>{file.retry_count ?? 0}</dd>
              </dl>
              <p className="failure-hint">{remediationHint(file)}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
