import type {
  IntegritySeverity,
  IntegrityTimelineEventViewModel,
  JobDetail,
} from "../../types";

const LIFECYCLE_LABELS: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  finished: "Finished",
  completed: "Completed",
  cleanup: "Cleanup",
  partial: "Partial",
  failed: "Failed",
  error: "Error",
};

const TIMELINE_EVENT_TYPES = new Set(Object.keys(LIFECYCLE_LABELS));

function normalizeEventType(eventType: string): string {
  return eventType.trim().toLowerCase();
}

function toEpoch(value: string): number {
  const epoch = Date.parse(value);
  return Number.isNaN(epoch) ? 0 : epoch;
}

function defaultLifecycleDetail(eventType: string): string {
  switch (eventType) {
    case "queued":
      return "Job accepted and waiting for worker capacity.";
    case "running":
      return "Worker is actively processing source files.";
    case "finished":
    case "completed":
      return "Processing completed successfully.";
    case "cleanup":
      return "Artifacts and runtime files were removed.";
    case "partial":
      return "Processing completed with file-level failures.";
    case "failed":
    case "error":
      return "Processing halted due to an integrity-impacting failure.";
    default:
      return "Lifecycle event recorded.";
  }
}

function severityForEventType(eventType: string): IntegritySeverity {
  if (eventType === "error" || eventType === "failed") {
    return "error";
  }
  if (eventType === "partial") {
    return "warning";
  }
  if (eventType === "finished" || eventType === "completed" || eventType === "cleanup") {
    return "success";
  }
  return "info";
}

function remediationForLifecycleEvent(eventType: string, detail: string): string {
  const normalizedDetail = detail.toLowerCase();
  if (eventType === "queued") {
    return "Wait for processing to begin; no intervention is required yet.";
  }
  if (eventType === "running") {
    return "Monitor progress. If failures appear, address root causes before running Retry Failed.";
  }
  if (eventType === "finished" || eventType === "completed") {
    return "Review outputs and semantic artifacts, then run Cleanup Artifacts when validation is complete.";
  }
  if (eventType === "cleanup") {
    return "Artifacts are already cleaned. Start a new run to generate fresh outputs.";
  }
  if (normalizedDetail.includes("database is locked")) {
    return "Retry after lock contention clears. If it repeats, reduce concurrent job activity.";
  }
  if (normalizedDetail.includes("permission")) {
    return "Fix source-file permissions, then run Retry Failed to reprocess only impacted files.";
  }
  if (normalizedDetail.includes("timed out") || normalizedDetail.includes("timeout")) {
    return "Run Retry Failed. If timeouts continue, reduce load or chunk size before rerunning.";
  }
  if (normalizedDetail.includes("not found")) {
    return "Restore missing source paths and then run Retry Failed.";
  }
  if (normalizedDetail.includes("unsupported")) {
    return "Convert inputs to a supported format and rerun the failed files.";
  }
  if (eventType === "partial") {
    return "Inspect failed files below, fix the causes, then run Retry Failed.";
  }
  return "Resolve the reported error and run Retry Failed after verifying the fix.";
}

export function mapLifecycleEventsToIntegrityEntries(
  events: JobDetail["events"]
): IntegrityTimelineEventViewModel[] {
  return [...events]
    .filter((event) => TIMELINE_EVENT_TYPES.has(normalizeEventType(event.event_type)))
    .sort((left, right) => toEpoch(left.event_time) - toEpoch(right.event_time))
    .map((event, index) => {
      const eventType = normalizeEventType(event.event_type);
      const rawDetail = typeof event.message === "string" ? event.message.trim() : "";
      const detail = rawDetail.length > 0 ? rawDetail : defaultLifecycleDetail(eventType);
      return {
        id: `${eventType}-${event.event_time}-${index}`,
        title: LIFECYCLE_LABELS[eventType] || event.event_type,
        occurredAt: event.event_time,
        detail,
        severity: severityForEventType(eventType),
        remediation: remediationForLifecycleEvent(eventType, detail),
      };
    });
}

export function failureRemediationHint(file: JobDetail["files"][number]): string {
  const errorType = (file.error_type || "").toLowerCase();
  const message = (file.error_message || "").toLowerCase();
  if (errorType.includes("permission") || message.includes("permission")) {
    return "Grant read permission for this file, then run Retry Failed.";
  }
  if (errorType.includes("timeout") || message.includes("timed out")) {
    return "Use Retry Failed. If this repeats, reduce system load or chunk size.";
  }
  if (errorType.includes("notfound") || message.includes("not found")) {
    return "Restore this source file path and then run Retry Failed.";
  }
  if (errorType.includes("unsupported") || message.includes("unsupported")) {
    return "Convert this file to a supported format and rerun failed files.";
  }
  return "Inspect this error, correct the root cause, and run Retry Failed.";
}
