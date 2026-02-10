import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listJobs } from "../api/client";
import { JobSummary } from "../types";

export function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    async function refresh() {
      try {
        setJobs(await listJobs());
        setError(null);
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load jobs";
        setError(message);
      }
      timer = window.setTimeout(refresh, 1000);
    }

    void refresh();
    return () => {
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, []);

  return (
    <section className="panel">
      <h2>Jobs</h2>
      {error ? <p className="error">{error}</p> : null}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Status</th>
              <th>Input</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
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
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted center">
                  No jobs yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
