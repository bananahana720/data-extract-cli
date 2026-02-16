import {
  Alert,
  Box,
  Button,
  Link,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { type ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { listJobs } from "../api/client";
import { ControlTowerStatusConsole, type ControlTowerActionChip } from "../components/control-tower";
import { EmptyStatePanel, PageSectionHeader, StatusPill } from "../components/foundation";
import type { SemanticStatus } from "../theme/tokens";
import { JobSummary } from "../types";

type StatusFilter = "all" | "needs_attention" | JobSummary["status"];
const VALID_STATUS_FILTERS: StatusFilter[] = [
  "all",
  "needs_attention",
  "queued",
  "running",
  "completed",
  "partial",
  "failed",
];

function asStatusFilter(value: string | null): StatusFilter | null {
  if (!value) {
    return null;
  }
  return VALID_STATUS_FILTERS.includes(value as StatusFilter) ? (value as StatusFilter) : null;
}

function toStatusTone(status: JobSummary["status"]): SemanticStatus {
  if (status === "failed") {
    return "error";
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

function isNeedsAttentionStatus(status: JobSummary["status"]): boolean {
  return status === "partial" || status === "failed";
}

export function JobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const [pollDelayMs, setPollDelayMs] = useState(2000);
  const query = searchParams.get("q") ?? "";
  const rawStatusFilter = searchParams.get("status");
  const parsedStatusFilter = asStatusFilter(rawStatusFilter);
  const statusFilter = parsedStatusFilter ?? "all";
  const inFlightRef = useRef(false);
  const failureStreakRef = useRef(0);

  const refreshJobs = useCallback(async () => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;
    setIsRefreshing(true);
    try {
      const loadedJobs = await listJobs({ limit: 300 });
      const hasActiveJobs = loadedJobs.some((job) => job.status === "queued" || job.status === "running");
      failureStreakRef.current = 0;
      setJobs(loadedJobs);
      setError(null);
      setLastUpdatedAt(new Date().toISOString());
      setPollDelayMs(hasActiveJobs ? 1000 : 4000);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to load jobs";
      failureStreakRef.current += 1;
      setError(message);
      const baseDelay = 2000 * Math.min(8, 2 ** failureStreakRef.current);
      const jitter = Math.floor(Math.random() * 250);
      setPollDelayMs(Math.min(15000, baseDelay + jitter));
    } finally {
      inFlightRef.current = false;
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refreshJobs();
  }, [refreshJobs]);

  useEffect(() => {
    const jitter = Math.floor(Math.random() * 150);
    const timer = window.setTimeout(() => {
      void refreshJobs();
    }, pollDelayMs + jitter);
    return () => {
      window.clearTimeout(timer);
    };
  }, [refreshJobs, pollDelayMs]);

  useEffect(() => {
    if (rawStatusFilter && parsedStatusFilter === null) {
      const corrected = new URLSearchParams(searchParams);
      corrected.delete("status");
      setSearchParams(corrected, { replace: true });
    }
  }, [parsedStatusFilter, rawStatusFilter, searchParams, setSearchParams]);

  const updateFilters = useCallback(
    (next: { query?: string; status?: StatusFilter }) => {
      const nextParams = new URLSearchParams(searchParams);
      const nextQuery = next.query ?? query;
      const nextStatus = next.status ?? statusFilter;
      if (nextQuery.trim().length > 0) {
        nextParams.set("q", nextQuery);
      } else {
        nextParams.delete("q");
      }
      if (nextStatus !== "all") {
        nextParams.set("status", nextStatus);
      } else {
        nextParams.delete("status");
      }
      setSearchParams(nextParams, { replace: true });
    },
    [query, searchParams, setSearchParams, statusFilter]
  );

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
        if (isNeedsAttentionStatus(job.status)) {
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
      const statusMatches =
        statusFilter === "all"
          ? true
          : statusFilter === "needs_attention"
            ? isNeedsAttentionStatus(job.status)
            : job.status === statusFilter;
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
  const summaryStatusTone: SemanticStatus =
    summary.failed > 0 ? "warning" : summary.running > 0 ? "info" : summary.total > 0 ? "success" : "neutral";
  const summaryStatusLabel =
    summary.failed > 0
      ? `${summary.failed} need attention`
      : summary.running > 0
        ? `${summary.running} running`
        : summary.total > 0
          ? "All clear"
          : "No jobs yet";
  const summaryActionChips: ControlTowerActionChip[] = [
    {
      id: "focus-running",
      label: "Focus running",
      tone: "info",
      href: "/jobs?status=running",
      disabled: summary.running === 0,
    },
    {
      id: "focus-failed",
      label: "Needs attention",
      tone: summary.failed > 0 ? "warning" : "neutral",
      href: "/jobs?status=needs_attention",
      disabled: summary.failed === 0,
    },
    {
      id: "clear-filters",
      label: "Clear filters",
      tone: "neutral",
      onClick: () => {
        updateFilters({ query: "", status: "all" });
      },
      disabled: !hasFilters,
    },
    {
      id: "new-run",
      label: "Start new run",
      tone: "success",
      href: "/",
    },
  ];

  return (
    <Stack component="section" spacing={2.5} data-testid="jobs-page">
      <PageSectionHeader
        eyebrow="W4 Control Tower"
        title="Jobs"
        subtitle="Track queue health, in-flight processing, and recovery actions."
        action={
          <Button
            type="button"
            variant="outlined"
            onClick={() => void refreshJobs()}
            disabled={isRefreshing}
            data-testid="jobs-refresh-button"
          >
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" data-testid="jobs-last-updated" aria-live="polite">
        {lastUpdatedAt ? `Last updated ${new Date(lastUpdatedAt).toLocaleTimeString()}` : "Loading jobs..."}
      </Typography>

      <ControlTowerStatusConsole
        title="Operational Signal"
        subtitle="Use quick chips to isolate active work or attention-demanding jobs."
        statusTone={summaryStatusTone}
        statusLabel={summaryStatusLabel}
        metrics={[
          {
            id: "jobs-total",
            label: "Total jobs",
            value: summary.total,
            detail: "Latest 300 jobs",
            tone: "neutral",
            testId: "jobs-summary-total",
          },
          {
            id: "jobs-running",
            label: "Running",
            value: summary.running,
            detail: summary.running > 0 ? "Workers currently active" : "No active workers",
            tone: summary.running > 0 ? "info" : "neutral",
            href: "/jobs?status=running",
            testId: "jobs-summary-running",
          },
          {
            id: "jobs-failed",
            label: "Needs attention",
            value: summary.failed,
            detail: summary.failed > 0 ? "Partial or failed runs detected" : "No failures in list",
            tone: summary.failed > 0 ? "warning" : "success",
            href: "/jobs?status=needs_attention",
            testId: "jobs-summary-failed",
          },
          {
            id: "jobs-completed",
            label: "Completed",
            value: summary.completed,
            detail: "Terminal success",
            tone: summary.completed > 0 ? "success" : "neutral",
            href: "/jobs?status=completed",
            testId: "jobs-summary-completed",
          },
        ]}
        actionChips={summaryActionChips}
        testId="jobs-summary"
      />

      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={1.5}
        alignItems={{ xs: "stretch", md: "flex-end" }}
      >
        <TextField
          id="jobs-filter-search"
          label="Search"
          placeholder="Job id, path, or status"
          value={query}
          onChange={(event) => updateFilters({ query: event.target.value })}
          inputProps={{ "data-testid": "jobs-filter-search" }}
          fullWidth
        />
        <Stack spacing={0.5} sx={{ minWidth: { xs: "100%", md: 240 } }}>
          <Typography component="label" variant="body2" color="text.secondary" htmlFor="jobs-filter-status">
            Status
          </Typography>
          <Box
            component="select"
            id="jobs-filter-status"
            data-testid="jobs-filter-status"
            value={statusFilter}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              updateFilters({ status: event.target.value as StatusFilter })
            }
            sx={{
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 1.5,
              px: 1.5,
              py: 1.1,
              fontFamily: "inherit",
              fontSize: "0.95rem",
              backgroundColor: "background.paper",
              color: "text.primary",
              minHeight: 44,
            }}
          >
            <option value="all">All statuses</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="needs_attention">Needs attention (partial + failed)</option>
            <option value="partial">Partial</option>
            <option value="failed">Failed</option>
          </Box>
        </Stack>
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <TableContainer component={Box} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}>
        <Table size="small" aria-label="Jobs table" data-testid="jobs-table">
          <TableHead>
            <TableRow>
              <TableCell>Job ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Input</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredJobs.map((job) => (
              <TableRow key={job.job_id} hover>
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  <Link component={RouterLink} to={`/jobs/${job.job_id}`} underline="hover" color="inherit">
                    {job.job_id}
                  </Link>
                </TableCell>
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  <StatusPill status={toStatusTone(job.status)} label={job.status} />
                </TableCell>
                <TableCell sx={{ maxWidth: 420 }}>
                  <Typography title={job.input_path} noWrap>
                    {job.input_path}
                  </Typography>
                </TableCell>
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  {new Date(job.created_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
            {sortedJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4}>
                  <Box data-testid="jobs-empty-state" sx={{ py: 1 }}>
                    <EmptyStatePanel
                      title="No jobs yet"
                      description="Kick off your first extraction run to populate the control tower."
                      primaryAction={
                        <Button component={RouterLink} to="/" variant="outlined">
                          Create your first run
                        </Button>
                      }
                    />
                  </Box>
                </TableCell>
              </TableRow>
            ) : null}
            {sortedJobs.length > 0 && filteredJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4}>
                  <Box data-testid="jobs-filter-empty-state" sx={{ py: 1 }}>
                    <EmptyStatePanel
                      title="No jobs match your current filters"
                      description="Adjust search terms or reset filters to recover the full queue view."
                      primaryAction={
                        hasFilters ? (
                          <Button
                            type="button"
                            variant="text"
                            onClick={() => {
                              updateFilters({ query: "", status: "all" });
                            }}
                          >
                            Clear filters
                          </Button>
                        ) : undefined
                      }
                    />
                  </Box>
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
