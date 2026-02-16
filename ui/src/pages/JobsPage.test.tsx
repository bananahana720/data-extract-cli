import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockListJobs = vi.fn();

vi.mock("../api/client", () => ({
  listJobs: (...args: unknown[]) => mockListJobs(...args),
}));

import { JobsPage } from "./JobsPage";

function renderJobsPage(initialPath = "/jobs"): void {
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/jobs" element={<JobsPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("JobsPage", () => {
  beforeEach(() => {
    mockListJobs.mockReset();
  });

  it("shows attention filter links and matches partial + failed statuses", async () => {
    mockListJobs.mockResolvedValue([
      {
        job_id: "job-partial",
        status: "partial",
        input_path: "/tmp/source-partial",
        output_dir: "/tmp/output-partial",
        created_at: "2026-01-01T00:00:00.000Z",
        started_at: "2026-01-01T00:01:00.000Z",
        finished_at: "2026-01-01T00:02:00.000Z",
        session_id: "session-1",
      },
      {
        job_id: "job-failed",
        status: "failed",
        input_path: "/tmp/source-failed",
        output_dir: "/tmp/output-failed",
        created_at: "2026-01-02T00:00:00.000Z",
        started_at: "2026-01-02T00:01:00.000Z",
        finished_at: "2026-01-02T00:02:00.000Z",
        session_id: "session-2",
      },
      {
        job_id: "job-completed",
        status: "completed",
        input_path: "/tmp/source-completed",
        output_dir: "/tmp/output-completed",
        created_at: "2026-01-03T00:00:00.000Z",
        started_at: "2026-01-03T00:01:00.000Z",
        finished_at: "2026-01-03T00:02:00.000Z",
        session_id: "session-3",
      },
    ]);

    renderJobsPage("/jobs?status=needs_attention");

    await waitFor(() => expect(mockListJobs).toHaveBeenCalled());
    expect(screen.getByRole("link", { name: "Needs attention" })).toHaveAttribute(
      "href",
      "/jobs?status=needs_attention"
    );

    expect(screen.getByRole("link", { name: "job-partial" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "job-failed" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "job-completed" })).not.toBeInTheDocument();
  });
});
