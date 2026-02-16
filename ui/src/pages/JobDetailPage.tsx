import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import { Alert, Box, Button, Card, CardContent, LinearProgress, Stack, Typography } from "@mui/material";

import {
  cleanupJobArtifacts,
  getJob,
  getJobArtifactDownloadUrl,
  listJobArtifacts,
  retryJobFailures,
} from "../api/client";
import { StatusPill } from "../components/foundation";
import { IntegrityTimelineRail, failureRemediationHint, mapLifecycleEventsToIntegrityEntries } from "../components/integrity";
import type { SemanticStatus } from "../theme/tokens";
import { JobArtifactEntry, JobDetail, SemanticArtifact, SemanticOutcome } from "../types";

const STAGES = ["extract", "normalize", "chunk", "semantic", "output"];
const LIFECYCLE_EVENT_TYPES = new Set([
  "queued",
  "running",
  "finished",
  "completed",
  "cleanup",
  "partial",
  "failed",
  "error",
]);

type CopyStatus =
  | { kind: "success"; message: string }
  | { kind: "error"; message: string }
  | null;

function toStatusTone(status: JobDetail["status"]): SemanticStatus {
  if (status === "failed") {
    return "error";
  }
  if (status === "queued") {
    return "warning";
  }
  if (status === "partial") {
    return "warning";
  }
  if (status === "completed") {
    return "success";
  }
  if (status === "running") {
    return "info";
  }
  return "neutral";
}

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

export function JobDetailPage() {
  const { jobId = "" } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollVersion, setPollVersion] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>(null);
  const [artifactEntries, setArtifactEntries] = useState<JobArtifactEntry[]>([]);
  const [artifactWarning, setArtifactWarning] = useState<string | null>(null);
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
            setArtifactWarning(null);
          } catch (artifactError) {
            const message =
              artifactError instanceof Error ? artifactError.message : "Unable to refresh artifact list.";
            setArtifactEntries([]);
            setArtifactWarning(
              `Artifact list refresh failed (${message}). Downloads may be temporarily unavailable. ` +
                "Verify API access and wait for the next refresh or reload this page."
            );
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
      ms: Number(stageMap[name] || 0),
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
    return [...job.events]
      .filter(
        (event) =>
          typeof event.event_type === "string" &&
          LIFECYCLE_EVENT_TYPES.has(event.event_type.toLowerCase())
      )
      .sort((left, right) => Date.parse(left.event_time) - Date.parse(right.event_time));
  }, [job]);

  const timelineEntries = useMemo(() => {
    return mapLifecycleEventsToIntegrityEntries(lifecycleEvents);
  }, [lifecycleEvents]);

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
        message: "Unable to copy output path. Copy it manually from the summary.",
      });
    }
  }

  if (error && !job) {
    return (
      <Alert severity="error" role="alert">
        {error}
      </Alert>
    );
  }

  if (!job) {
    return <Typography color="text.secondary">Loading job details...</Typography>;
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
  const hasCleanupEvent = lifecycleEvents.some((event) => event.event_type.toLowerCase() === "cleanup");
  const hasLifecycleFailureSignal = lifecycleEvents.some((event) => {
    const eventType = event.event_type.toLowerCase();
    return eventType === "error" || eventType === "failed" || eventType === "partial";
  });
  const hasIntegrityFailures =
    failedFiles.length > 0 || hasLifecycleFailureSignal || job.status === "failed" || job.status === "partial";
  const isActive = job.status === "queued" || job.status === "running";
  const startedAtMs = job.started_at ? Date.parse(job.started_at) : Number.NaN;
  const finishedAtMs = job.finished_at ? Date.parse(job.finished_at) : Number.NaN;
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
          ? "Fix failed file issues and use Retry Failed to reprocess only failed files."
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
    <Box component="section" data-testid="job-detail-page" sx={{ display: "grid", gap: 3 }}>
      <Card variant="outlined" data-testid="job-summary-card">
        <CardContent>
          <Stack spacing={2.5}>
            <Stack
              direction={{ xs: "column", md: "row" }}
              spacing={1.5}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
            >
              <Box>
                <Typography variant="h5" component="h2">
                  Job {job.job_id}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-word" }}>
                  Input: {job.input_path}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-word" }}>
                  Output: {job.output_dir}
                </Typography>
              </Box>
              <StatusPill
                data-testid="job-status-chip"
                status={toStatusTone(job.status)}
                label={job.status}
                sx={{ fontWeight: 700, textTransform: "none" }}
              />
            </Stack>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" },
                gap: 1.5,
              }}
            >
              {[
                { testId: "job-metric-total", label: "Total Files", value: totalFiles },
                { testId: "job-metric-processed", label: "Processed", value: processedFiles },
                { testId: "job-metric-failed", label: "Failed", value: failedFiles.length },
                { testId: "job-metric-skipped", label: "Skipped", value: skippedFiles },
              ].map((metric) => (
                <Card key={metric.testId} variant="outlined" data-testid={metric.testId}>
                  <CardContent sx={{ "&:last-child": { pb: 2 } }}>
                    <Typography variant="body2" color="text.secondary">
                      {metric.label}
                    </Typography>
                    <Typography variant="h6" component="strong" sx={{ display: "block" }}>
                      {metric.value}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>

            <Card variant="outlined" data-testid="job-progress-card">
              <CardContent sx={{ "&:last-child": { pb: 2 } }}>
                <Stack spacing={1.25}>
                  <Stack direction="row" justifyContent="space-between" spacing={1}>
                    <Typography variant="body2">Processing Progress</Typography>
                    <Typography variant="body2" fontWeight={700} data-testid="job-progress-text">
                      {processedFiles}/{totalFiles} ({boundedPercent}%)
                    </Typography>
                  </Stack>
                  <Box>
                    <LinearProgress
                      variant="determinate"
                      value={boundedPercent}
                      aria-label="Job processing progress"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={boundedPercent}
                      aria-valuetext={`${processedFiles} of ${totalFiles} files processed (${boundedPercent}%)`}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            <Box
              component="dl"
              data-testid="job-runtime-metadata"
              sx={{
                m: 0,
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
                gap: 1.25,
              }}
            >
              {[
                { label: "Created", value: formatDateTime(job.created_at) },
                { label: "Started", value: formatDateTime(job.started_at) },
                { label: "Finished", value: formatDateTime(job.finished_at) },
                { label: "Elapsed", value: elapsedDuration },
                { label: "Format", value: job.requested_format.toUpperCase() },
                { label: "Chunk Size", value: String(job.chunk_size) },
              ].map((entry) => (
                <Box key={entry.label}>
                  <Typography
                    component="dt"
                    variant="caption"
                    color="text.secondary"
                    sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}
                  >
                    {entry.label}
                  </Typography>
                  <Typography component="dd" variant="body2" sx={{ m: 0, fontWeight: 500 }}>
                    {entry.value}
                  </Typography>
                </Box>
              ))}
            </Box>

            <Alert severity={hasIntegrityFailures ? "warning" : "info"} variant="outlined" data-testid="job-next-action">
              <Typography variant="body2">
                <Box component="span" sx={{ fontWeight: 700 }}>
                  Next Action:
                </Box>{" "}
                {nextAction}
              </Typography>
            </Alert>
          </Stack>
        </CardContent>
      </Card>

      {hasIntegrityFailures ? (
        <Alert severity="error" data-testid="job-integrity-failure-summary">
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            Integrity failures require remediation.
          </Typography>
          <Typography variant="body2">
            {failedFiles.length > 0
              ? `${failedFiles.length} file(s) failed integrity checks. Resolve the file-level cause, then run Retry Failed.`
              : "Lifecycle signals indicate integrity failure. Review timeline details, fix root causes, then retry."}
          </Typography>
        </Alert>
      ) : null}

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6" component="h3">
              Actions
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25} useFlexGap flexWrap="wrap">
              <Button
                onClick={runRetry}
                disabled={retrying || failedFiles.length === 0 || isActive}
                data-testid="job-action-retry"
                variant="contained"
              >
                {retrying ? "Retrying..." : `Retry Failed (${failedFiles.length})`}
              </Button>
              <Button
                onClick={runCleanup}
                disabled={cleaning || isActive || hasCleanupEvent}
                type="button"
                data-testid="job-action-cleanup"
                variant="outlined"
              >
                {cleaning ? "Cleaning..." : "Cleanup Artifacts"}
              </Button>
              <Button
                onClick={() => copyOutputPath(job.output_dir)}
                type="button"
                data-testid="job-action-copy-output"
                variant="outlined"
              >
                Copy Output Path
              </Button>
            </Stack>
            <Typography variant="body2" color="text.secondary" data-testid="job-actions-hint">
              {isActive
                ? "Retry and cleanup stay disabled while the job is queued/running."
                : hasCleanupEvent
                  ? "Artifacts are already cleaned."
                  : "Use Retry Failed for failures or Cleanup Artifacts once review is complete."}
            </Typography>
            {copyStatus ? (
              <Alert
                severity={copyStatus.kind === "error" ? "error" : "success"}
                aria-live="polite"
                data-testid="job-copy-status"
              >
                {copyStatus.message}
              </Alert>
            ) : null}
            {error ? (
              <Alert severity="error" role="alert" data-testid="job-action-error">
                Action failed: {error}. Resolve the issue, then retry.
              </Alert>
            ) : null}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.5}>
            <Typography variant="h6" component="h3">
              Lifecycle Timeline
            </Typography>
            {timelineEntries.length === 0 ? (
              <Typography color="text.secondary" data-testid="job-lifecycle-empty">
                No lifecycle events recorded yet.
              </Typography>
            ) : (
              <IntegrityTimelineRail
                events={timelineEntries}
                testId="job-lifecycle-timeline"
                itemTestIdPrefix="job-timeline-item-"
              />
            )}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.5}>
            <Typography variant="h6" component="h3">
              Stage Timing
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "repeat(2, minmax(0, 1fr))", md: "repeat(5, minmax(0, 1fr))" },
                gap: 1.25,
              }}
            >
              {stageTotals.map((stage) => (
                <Card key={stage.name} variant="outlined">
                  <CardContent sx={{ "&:last-child": { pb: 2 } }}>
                    <Typography variant="subtitle2">{stage.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stage.ms > 0 ? `${stage.ms.toFixed(1)} ms` : "pending"}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.5}>
            <Typography variant="h6" component="h3">
              Semantic Reporting
            </Typography>
            {artifactWarning ? (
              <Alert severity="warning" role="status">
                {artifactWarning}
              </Alert>
            ) : null}
            {semanticOutcome ? (
              <Box data-testid="job-semantic-card">
                <Box
                  component="dl"
                  sx={{
                    m: 0,
                    display: "grid",
                    gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
                    gap: 1.25,
                  }}
                >
                  <Box>
                    <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                      Status
                    </Typography>
                    <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                      {semanticOutcome.status}
                    </Typography>
                  </Box>
                  {semanticOutcome.reason_code ? (
                    <Box>
                      <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                        Reason
                      </Typography>
                      <Typography component="dd" variant="body2" sx={{ m: 0 }} data-testid="job-semantic-reason-code">
                        {formatReasonCode(semanticOutcome.reason_code)}
                      </Typography>
                    </Box>
                  ) : null}
                  <Box>
                    <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                      Total Chunks
                    </Typography>
                    <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                      {toNumber(semanticOutcome.summary?.total_chunks)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                      Vocabulary
                    </Typography>
                    <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                      {toNumber(semanticOutcome.summary?.vocabulary_size)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                      Components
                    </Typography>
                    <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                      {toNumber(semanticOutcome.summary?.n_components)}
                    </Typography>
                  </Box>
                </Box>

                {semanticOutcome.message ? (
                  <Alert severity="error" role="alert" sx={{ mt: 1.5 }}>
                    {semanticOutcome.message}
                  </Alert>
                ) : null}

                {semanticArtifacts.length > 0 ? (
                  <Box component="ul" data-testid="job-semantic-artifact-list" sx={{ mb: 0, mt: 1.5, pl: 2.5 }}>
                    {semanticArtifacts.map((artifact) => {
                      const downloadablePath = resolveArtifactDownloadPath(artifact.path);
                      return (
                        <Box component="li" key={`${artifact.artifact_type}-${artifact.path}`} sx={{ mb: 0.75 }}>
                          <Typography component="span" variant="body2" sx={{ fontWeight: 700 }}>
                            {artifact.name}
                          </Typography>{" "}
                          <Typography component="span" variant="body2" color="text.secondary">
                            ({artifact.format || "unknown"})
                          </Typography>
                          {downloadablePath ? (
                            <Typography
                              component="a"
                              variant="body2"
                              href={getJobArtifactDownloadUrl(job.job_id, downloadablePath)}
                              target="_blank"
                              rel="noreferrer"
                              sx={{ ml: 1 }}
                            >
                              Download
                            </Typography>
                          ) : null}
                        </Box>
                      );
                    })}
                  </Box>
                ) : (
                  <Typography color="text.secondary" data-testid="job-semantic-empty" sx={{ mt: 1.5 }}>
                    No semantic artifacts recorded.
                  </Typography>
                )}
              </Box>
            ) : (
              <Typography color="text.secondary" data-testid="job-semantic-empty">
                Semantic processing was not requested for this job.
              </Typography>
            )}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.5}>
            <Typography variant="h6" component="h3">
              Failures
            </Typography>
            {failedFiles.length === 0 ? (
              <Typography color="text.secondary" data-testid="job-failures-empty">
                No failed files.
              </Typography>
            ) : (
              <Stack spacing={1.25} data-testid="job-failure-list">
                {failedFiles.map((file) => (
                  <Card key={file.source_path} variant="outlined">
                    <CardContent sx={{ "&:last-child": { pb: 2 } }}>
                      <Stack spacing={1}>
                        <Typography variant="subtitle2" sx={{ wordBreak: "break-word" }}>
                          {file.source_path}
                        </Typography>
                        <Box
                          component="dl"
                          sx={{
                            m: 0,
                            display: "grid",
                            gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" },
                            gap: 1,
                          }}
                        >
                          <Box>
                            <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                              Error Type
                            </Typography>
                            <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                              {file.error_type || "Unknown"}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                              Error Message
                            </Typography>
                            <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                              {file.error_message || "Unknown error"}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography component="dt" variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.6 }}>
                              Retry Count
                            </Typography>
                            <Typography component="dd" variant="body2" sx={{ m: 0 }}>
                              {file.retry_count ?? 0}
                            </Typography>
                          </Box>
                        </Box>
                        <Alert severity="warning" variant="outlined">
                          <Typography variant="body2">
                            <Box component="span" sx={{ fontWeight: 700 }}>
                              Remediation:
                            </Box>{" "}
                            {failureRemediationHint(file)}
                          </Typography>
                        </Alert>
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
