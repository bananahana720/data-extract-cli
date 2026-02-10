import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { cleanupJobArtifacts, getJob, retryJobFailures } from "../api/client";
import { JobDetail } from "../types";

const STAGES = ["extract", "normalize", "chunk", "semantic", "output"];

export function JobDetailPage() {
  const { jobId = "" } = useParams();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [cleaning, setCleaning] = useState(false);

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

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!job) {
    return <p className="muted">Loading job details...</p>;
  }

  const failedFiles = job.files.filter((file) => file.status === "failed");

  return (
    <section className="panel">
      <div className="row-between">
        <h2>Job {job.job_id}</h2>
        <span className={`status ${job.status}`}>{job.status}</span>
      </div>

      <p className="muted">Input: {job.input_path}</p>
      <p className="muted">Output: {job.output_dir}</p>

      <div className="stage-grid">
        {stageTotals.map((stage) => (
          <article key={stage.name} className="stage-card">
            <h3>{stage.name}</h3>
            <p>{stage.ms > 0 ? `${stage.ms.toFixed(1)} ms` : "pending"}</p>
          </article>
        ))}
      </div>

      <div className="actions-inline">
        <button onClick={runRetry} disabled={retrying || failedFiles.length === 0}>
          {retrying ? "Retrying..." : `Retry Failed (${failedFiles.length})`}
        </button>
        <button onClick={runCleanup} disabled={cleaning} className="secondary" type="button">
          {cleaning ? "Cleaning..." : "Cleanup Artifacts"}
        </button>
        <button
          onClick={() => navigator.clipboard.writeText(job.output_dir)}
          className="secondary"
          type="button"
        >
          Copy Output Path
        </button>
      </div>

      <h3>Events</h3>
      <ul className="event-list">
        {job.events.map((event) => (
          <li key={`${event.event_type}-${event.event_time}`}>
            <strong>{event.event_type}</strong> {new Date(event.event_time).toLocaleTimeString()} - {event.message}
          </li>
        ))}
      </ul>

      <h3>Failures</h3>
      {failedFiles.length === 0 ? (
        <p className="muted">No failed files.</p>
      ) : (
        <ul className="error-list">
          {failedFiles.map((file) => (
            <li key={file.source_path}>
              <strong>{file.source_path}</strong>
              <p>{file.error_message || "Unknown error"}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
