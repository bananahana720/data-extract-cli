import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { listJobs } from "../api/client";
import { JobSummary } from "../types";

type StatusFilter = "all" | JobSummary["status"];

export function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const [pollDelayMs, setPollDelayMs] = useState(2000);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const inFlightRef = useRef(false);

  const refreshJobs = useCallback(async () => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;
    setIsRefreshing(true);
    try {
      const loadedJobs = await listJobs({ limit: 300 });
      const hasActiveJobs = loadedJobs.some((job) => job.status === "queued" || job.status === "running");
      setJobs(loadedJobs);
      setError(null);
      setLastUpdatedAt(new Date().toISOString());
      setPollDelayMs(hasActiveJobs ? 1000 : 4000);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to load jobs";
      setError(message);
      setPollDelayMs((current) => Math.min(15000, Math.max(2000, current * 2)));
    } finally {
      inFlightRef.current = false;
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refreshJobs();
  }, [refreshJobs]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshJobs();
    }, pollDelayMs);
    return () => {
      window.clearTimeout(timer);
    };
  }, [refreshJobs, pollDelayMs]);

  const sortedJobs = useMemo(() => {
    return [...jobs].sort((left, right) => {
      return Date.parse(right.created_at) - Date.parse(left.created_at);
    });
  }, [jobs]);

  const summary = useMemo(() => {
    return sortedJobs.reduce(
      (counts, job) => {
        counts.total += 1;
        if (job.status === "running") {
          counts.running += 1;
        }
        if (job.status === "partial" || job.status === "failed") {
          counts.failed += 1;
        }
        if (job.status === "completed") {
          counts.completed += 1;
        }
        return counts;
      },
      { total: 0, running: 0, failed: 0, completed: 0 }
    );
  }, [sortedJobs]);

  const filteredJobs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return sortedJobs.filter((job) => {
      const statusMatches = statusFilter === "all" ? true : job.status === statusFilter;
      const queryMatches =
        normalizedQuery.length === 0
          ? true
          : job.job_id.toLowerCase().includes(normalizedQuery) ||
            job.input_path.toLowerCase().includes(normalizedQuery) ||
            job.status.toLowerCase().includes(normalizedQuery);
      return statusMatches && queryMatches;
    });
  }, [sortedJobs, query, statusFilter]);

  const hasFilters = query.trim().length > 0 || statusFilter !== "all";

  return (
    <section className="panel jobs-page" data-testid="jobs-page">
      <div className="row-between jobs-header">
        <h2>Jobs</h2>
        <button
          type="button"
          className="secondary"
          onClick={() => void refreshJobs()}
          disabled={isRefreshing}
          data-testid="jobs-refresh-button"
        >
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      <p className="help-text" data-testid="jobs-last-updated" aria-live="polite">
        {lastUpdatedAt ? `Last updated ${new Date(lastUpdatedAt).toLocaleTimeString()}` : "Loading jobs..."}
      </p>

      <div className="summary-metrics jobs-summary" data-testid="jobs-summary">
        <article className="metric-card" data-testid="jobs-summary-total">
          <span>Total</span>
          <strong>{summary.total}</strong>
        </article>
        <article className="metric-card" data-testid="jobs-summary-running">
          <span>Running</span>
          <strong>{summary.running}</strong>
        </article>
        <article className="metric-card" data-testid="jobs-summary-failed">
          <span>Needs Attention</span>
          <strong>{summary.failed}</strong>
        </article>
        <article className="metric-card" data-testid="jobs-summary-completed">
          <span>Completed</span>
          <strong>{summary.completed}</strong>
        </article>
      </div>

      <div className="jobs-filters">
        <label htmlFor="jobs-filter-search">
          <span>Search</span>
        </label>
        <input
          id="jobs-filter-search"
          data-testid="jobs-filter-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Job id, path, or status"
        />
        <label htmlFor="jobs-filter-status">
          <span>Status</span>
        </label>
        <select
          id="jobs-filter-status"
          data-testid="jobs-filter-status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
        >
          <option value="all">All statuses</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="partial">Partial</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="table-wrap">
        <table data-testid="jobs-table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Status</th>
              <th>Input</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {filteredJobs.map((job) => (
              <tr key={job.job_id}>
                <td>
                  <Link to={`/jobs/${job.job_id}`}>{job.job_id}</Link>
                </td>
                <td>
                  <span className={`status ${job.status}`}>{job.status}</span>
                </td>
                <td className="truncate" title={job.input_path}>
                  {job.input_path}
                </td>
                <td>{new Date(job.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {sortedJobs.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted center">
                  <div className="empty-state" data-testid="jobs-empty-state">
                    <p>No jobs yet.</p>
                    <Link to="/">Create your first run</Link>
                  </div>
                </td>
              </tr>
            ) : null}
            {sortedJobs.length > 0 && filteredJobs.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted center">
                  <div className="empty-state" data-testid="jobs-filter-empty-state">
                    <p>No jobs match your current filters.</p>
                    {hasFilters ? (
                      <button
                        type="button"
                        className="link"
                        onClick={() => {
                          setQuery("");
                          setStatusFilter("all");
                        }}
                      >
                        Clear filters
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
