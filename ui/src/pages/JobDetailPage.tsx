import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import {
  cleanupJobArtifacts,
  getJob,
  getJobArtifactDownloadUrl,
  listJobArtifacts,
  retryJobFailures
} from "../api/client";
import { JobArtifactEntry, JobDetail, SemanticArtifact, SemanticOutcome } from "../types";

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

function isDatabaseLockedMessage(message: string): boolean {
  return /database is locked/i.test(message);
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function runWithDatabaseLockRetry<T>(operation: () => Promise<T>, attempts = 3): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      const message = error instanceof Error ? error.message : String(error);
      if (!isDatabaseLockedMessage(message) || attempt === attempts - 1) {
        throw error;
      }
      await wait(200 * (attempt + 1));
    }
  }
  throw lastError;
}

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

function formatReasonCode(reasonCode: string): string {
  return reasonCode
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
  const [pollVersion, setPollVersion] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(null);
  const [artifactEntries, setArtifactEntries] = useState<JobArtifactEntry[]>([]);
  const artifactPollRef = useRef(0);
  const errorStreakRef = useRef(0);

  useEffect(() => {
    let timer: number | undefined;

    async function refresh() {
      if (!jobId) {
        return;
      }

      try {
        const detail = await getJob(jobId, { fileLimit: 2000, eventLimit: 2000 });
        errorStreakRef.current = 0;
        setJob(detail);
        setError(null);
        const active = detail.status === "queued" || detail.status === "running";
        const shouldFetchArtifacts = !active || artifactPollRef.current % 5 === 0;
        if (shouldFetchArtifacts) {
          try {
            const artifactPayload = await listJobArtifacts(jobId);
            setArtifactEntries(artifactPayload.artifacts);
          } catch {
            setArtifactEntries([]);
          }
        }
        artifactPollRef.current = active ? artifactPollRef.current + 1 : 0;

        if (active) {
          timer = window.setTimeout(refresh, 1000 + Math.floor(Math.random() * 120));
        }
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load job";
        if (isDatabaseLockedMessage(message) && job) {
          return;
        }
        errorStreakRef.current += 1;
        setError(message);
        const delayMs = Math.min(10000, 1000 * (2 ** Math.min(4, errorStreakRef.current)));
        timer = window.setTimeout(refresh, delayMs + Math.floor(Math.random() * 200));
      }
    }

    void refresh();
    return () => {
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [jobId, pollVersion]);

  const stageTotals = useMemo(() => {
    const stageMap = (job?.result_payload?.stage_totals_ms as Record<string, number>) || {};
    const ordered = [...STAGES, ...Object.keys(stageMap).filter((name) => !STAGES.includes(name))];
    return ordered.map((name) => ({
      name,
      ms: Number(stageMap[name] || 0)
    }));
  }, [job]);
  const semanticOutcome = useMemo<SemanticOutcome | null>(() => {
    const payload = job?.result_payload;
    if (!payload || typeof payload !== "object") {
      return null;
    }
    const semantic = payload.semantic;
    if (!semantic || typeof semantic !== "object") {
      return null;
    }
    return semantic as SemanticOutcome;
  }, [job]);
  const semanticArtifacts = useMemo<SemanticArtifact[]>(() => {
    return semanticOutcome?.artifacts || [];
  }, [semanticOutcome]);
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
    setError(null);
    setRetrying(true);
    try {
      await runWithDatabaseLockRetry(() => retryJobFailures(jobId));
      const detail = await runWithDatabaseLockRetry(() =>
        getJob(jobId, { fileLimit: 2000, eventLimit: 2000 })
      );
      setJob(detail);
      if (detail.status === "queued" || detail.status === "running") {
        setPollVersion((current) => current + 1);
      }
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
    setError(null);
    setCleaning(true);
    try {
      await runWithDatabaseLockRetry(() => cleanupJobArtifacts(jobId));
      const detail = await runWithDatabaseLockRetry(() =>
        getJob(jobId, { fileLimit: 2000, eventLimit: 2000 })
      );
      setJob(detail);
      if (detail.status === "queued" || detail.status === "running") {
        setPollVersion((current) => current + 1);
      }
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

  if (error && !job) {
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

  function resolveArtifactDownloadPath(artifactPath: string): string | null {
    const normalized = artifactPath.replace(/\\/g, "/");
    const bySuffix = artifactEntries.find((entry) => normalized.endsWith(entry.path));
    if (bySuffix) {
      return bySuffix.path;
    }
    const fileName = normalized.split("/").pop() || "";
    const byName = artifactEntries.find((entry) => entry.path.endsWith(fileName));
    return byName ? byName.path : null;
  }

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
        {error ? (
          <p className="inline-alert is-error" role="alert" data-testid="job-action-error">
            {error}
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

      <h3>Semantic Reporting</h3>
      {semanticOutcome ? (
        <article className="semantic-card" data-testid="job-semantic-card">
          <dl className="key-value-list">
            <dt>Status</dt>
            <dd>{semanticOutcome.status}</dd>
            {semanticOutcome.reason_code ? (
              <>
                <dt>Reason</dt>
                <dd data-testid="job-semantic-reason-code">
                  {formatReasonCode(semanticOutcome.reason_code)}
                </dd>
              </>
            ) : null}
            <dt>Total Chunks</dt>
            <dd>{toNumber(semanticOutcome.summary?.total_chunks)}</dd>
            <dt>Vocabulary</dt>
            <dd>{toNumber(semanticOutcome.summary?.vocabulary_size)}</dd>
            <dt>Components</dt>
            <dd>{toNumber(semanticOutcome.summary?.n_components)}</dd>
          </dl>
          {semanticOutcome.message ? (
            <p className="inline-alert is-error" role="alert">
              {semanticOutcome.message}
            </p>
          ) : null}
          {semanticArtifacts.length > 0 ? (
            <ul className="event-list" data-testid="job-semantic-artifact-list">
              {semanticArtifacts.map((artifact) => {
                const downloadablePath = resolveArtifactDownloadPath(artifact.path);
                return (
                  <li key={`${artifact.artifact_type}-${artifact.path}`}>
                    <strong>{artifact.name}</strong>{" "}
                    <span className="muted">({artifact.format || "unknown"})</span>
                    {downloadablePath ? (
                      <>
                        {" "}
                        <a
                          href={getJobArtifactDownloadUrl(job.job_id, downloadablePath)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Download
                        </a>
                      </>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="muted" data-testid="job-semantic-empty">
              No semantic artifacts recorded.
            </p>
          )}
        </article>
      ) : (
        <p className="muted" data-testid="job-semantic-empty">
          Semantic processing was not requested for this job.
        </p>
      )}

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
