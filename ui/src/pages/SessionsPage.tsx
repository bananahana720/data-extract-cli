import { useEffect, useState } from "react";

import { listSessions } from "../api/client";
import { SessionSummary } from "../types";

export function SessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function refresh() {
      try {
        setSessions(await listSessions());
        setError(null);
      } catch (requestError) {
        const message =
          requestError instanceof Error ? requestError.message : "Unable to load sessions";
        setError(message);
      }
    }

    void refresh();
  }, []);

  return (
    <section className="panel">
      <h2>Sessions</h2>
      {error ? <p className="error">{error}</p> : null}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Session ID</th>
              <th>Status</th>
              <th>Processed</th>
              <th>Failed</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.session_id}>
                <td>{session.session_id}</td>
                <td>{session.status}</td>
                <td>{session.processed_count}/{session.total_files}</td>
                <td>{session.failed_count}</td>
                <td>{new Date(session.updated_at).toLocaleString()}</td>
              </tr>
            ))}
            {sessions.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted center">
                  No sessions found.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
