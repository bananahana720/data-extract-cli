import {
  Alert,
  Box,
  Button,
  Link,
  LinearProgress,
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
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";

import { listSessions } from "../api/client";
import { ControlTowerStatusConsole, type ControlTowerActionChip } from "../components/control-tower";
import { EmptyStatePanel, PageSectionHeader, StatusPill } from "../components/foundation";
import type { SemanticStatus } from "../theme/tokens";
import { SessionSummary } from "../types";

type SessionFilter = "all" | "active" | "needs_attention" | "completed";
const VALID_SESSION_FILTERS: SessionFilter[] = ["all", "active", "needs_attention", "completed"];

function asSessionFilter(value: string | null): SessionFilter | null {
  if (!value) {
    return null;
  }
  return VALID_SESSION_FILTERS.includes(value as SessionFilter) ? (value as SessionFilter) : null;
}

function normalizeStatus(status: string): string {
  return status.trim().toLowerCase();
}

function isActiveStatus(status: string): boolean {
  const normalized = normalizeStatus(status);
  return (
    normalized === "queued" ||
    normalized === "running" ||
    normalized === "processing" ||
    normalized === "pending" ||
    normalized === "in_progress"
  );
}

function isCompletedStatus(status: string): boolean {
  const normalized = normalizeStatus(status);
  return normalized === "completed" || normalized === "done" || normalized === "succeeded";
}

function needsAttention(session: SessionSummary): boolean {
  return (
    session.failed_count > 0 ||
    normalizeStatus(session.status).includes("fail") ||
    normalizeStatus(session.status).includes("error")
  );
}

function toProgressPercent(session: SessionSummary): number {
  if (session.total_files <= 0) {
    return 0;
  }
  const value = Math.round((session.processed_count / session.total_files) * 100);
  return Math.max(0, Math.min(100, value));
}

function toSessionTone(session: SessionSummary): SemanticStatus {
  if (needsAttention(session)) {
    return "error";
  }
  if (isActiveStatus(session.status)) {
    return "info";
  }
  if (isCompletedStatus(session.status)) {
    return "success";
  }
  return "neutral";
}

function mapSessionFilterToJobsFilter(status: SessionFilter): "running" | "needs_attention" | "completed" | null {
  if (status === "active") {
    return "running";
  }
  if (status === "needs_attention") {
    return "needs_attention";
  }
  if (status === "completed") {
    return "completed";
  }
  return null;
}

function toJobsContextHref(params: { query?: string; status?: SessionFilter; sessionId?: string }): string {
  const nextParams = new URLSearchParams();
  const normalizedQuery = (params.sessionId ?? params.query ?? "").trim();
  const mappedStatus = params.status ? mapSessionFilterToJobsFilter(params.status) : null;
  if (normalizedQuery) {
    nextParams.set("q", normalizedQuery);
  }
  if (mappedStatus) {
    nextParams.set("status", mappedStatus);
  }
  const suffix = nextParams.toString();
  return suffix ? `/jobs?${suffix}` : "/jobs";
}

export function SessionsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const [pollDelayMs, setPollDelayMs] = useState(4000);
  const query = searchParams.get("q") ?? "";
  const rawStatusFilter = searchParams.get("status");
  const parsedStatusFilter = asSessionFilter(rawStatusFilter);
  const statusFilter = parsedStatusFilter ?? "all";
  const inFlightRef = useRef(false);
  const failureStreakRef = useRef(0);
  const staleThresholdMs = 15 * 60 * 1000;

  const refresh = useCallback(async () => {
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;
    setIsRefreshing(true);
    try {
      const loaded = await listSessions();
      const hasActiveSessions = loaded.some((session) => isActiveStatus(session.status));
      failureStreakRef.current = 0;
      setSessions(loaded);
      setError(null);
      setLastUpdatedAt(new Date().toISOString());
      setPollDelayMs(hasActiveSessions ? 2000 : 5000);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to load sessions";
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
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const jitter = Math.floor(Math.random() * 150);
    const timer = window.setTimeout(() => {
      void refresh();
    }, pollDelayMs + jitter);
    return () => {
      window.clearTimeout(timer);
    };
  }, [pollDelayMs, refresh]);

  useEffect(() => {
    if (rawStatusFilter && parsedStatusFilter === null) {
      const corrected = new URLSearchParams(searchParams);
      corrected.delete("status");
      setSearchParams(corrected, { replace: true });
    }
  }, [parsedStatusFilter, rawStatusFilter, searchParams, setSearchParams]);

  const updateFilters = useCallback(
    (next: { query?: string; status?: SessionFilter }) => {
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

  const sortedSessions = useMemo(() => {
    return [...sessions].sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at));
  }, [sessions]);

  const filteredSessions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return sortedSessions.filter((session) => {
      const statusMatches =
        statusFilter === "all"
          ? true
          : statusFilter === "active"
            ? isActiveStatus(session.status)
            : statusFilter === "needs_attention"
              ? needsAttention(session)
              : isCompletedStatus(session.status);
      const queryMatches =
        normalizedQuery.length === 0
          ? true
          : session.session_id.toLowerCase().includes(normalizedQuery) ||
            session.source_directory.toLowerCase().includes(normalizedQuery) ||
            session.status.toLowerCase().includes(normalizedQuery);
      return statusMatches && queryMatches;
    });
  }, [query, sortedSessions, statusFilter]);

  const hasFilters = query.trim().length > 0 || statusFilter !== "all";
  const summary = useMemo(() => {
    const now = Date.now();
    return sortedSessions.reduce(
      (counts, session) => {
        counts.total += 1;
        counts.processed += session.processed_count;
        counts.fileTotal += session.total_files;
        if (isActiveStatus(session.status)) {
          counts.active += 1;
          if (now - Date.parse(session.updated_at) > staleThresholdMs) {
            counts.stale += 1;
          }
        }
        if (needsAttention(session)) {
          counts.attention += 1;
        }
        return counts;
      },
      { total: 0, active: 0, attention: 0, stale: 0, processed: 0, fileTotal: 0 }
    );
  }, [sortedSessions]);
  const completionText =
    summary.fileTotal > 0 ? `${summary.processed}/${summary.fileTotal}` : `${summary.processed}/0`;
  const summaryStatusTone: SemanticStatus =
    summary.attention > 0 ? "warning" : summary.active > 0 ? "info" : summary.total > 0 ? "success" : "neutral";
  const summaryStatusLabel =
    summary.attention > 0
      ? `${summary.attention} flagged`
      : summary.active > 0
        ? `${summary.active} active`
        : summary.total > 0
          ? "Stable"
          : "No sessions";
  const contextualJobsHref = toJobsContextHref({ query, status: statusFilter });
  const hasContextualJobsHref = contextualJobsHref !== "/jobs";
  const summaryActionChips: ControlTowerActionChip[] = [
    {
      id: "focus-active",
      label: "Focus active",
      tone: "info",
      onClick: () => updateFilters({ status: "active" }),
      disabled: summary.active === 0,
    },
    {
      id: "focus-attention",
      label: "Needs attention",
      tone: summary.attention > 0 ? "warning" : "neutral",
      onClick: () => updateFilters({ status: "needs_attention" }),
      disabled: summary.attention === 0,
    },
    {
      id: "focus-completed",
      label: "Show completed",
      tone: "success",
      onClick: () => updateFilters({ status: "completed" }),
      disabled: summary.total === 0,
    },
    {
      id: "clear-sessions-filters",
      label: "Clear filters",
      tone: "neutral",
      onClick: () => {
        updateFilters({ query: "", status: "all" });
      },
      disabled: !hasFilters,
    },
    {
      id: "open-jobs",
      label: hasContextualJobsHref ? "Open matching jobs" : "Open jobs board",
      tone: "neutral",
      href: contextualJobsHref,
    },
  ];

  return (
    <Stack component="section" spacing={2.5}>
      <PageSectionHeader
        eyebrow="W4 Control Tower"
        title="Sessions"
        subtitle="Track session throughput, stale activity, and follow-up signals."
        action={
          <Button variant="outlined" onClick={() => void refresh()} disabled={isRefreshing}>
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <Typography variant="body2" color="text.secondary" aria-live="polite">
        {lastUpdatedAt
          ? `Last updated ${new Date(lastUpdatedAt).toLocaleTimeString()}`
          : "Loading sessions..."}
      </Typography>

      <ControlTowerStatusConsole
        title="Session Signal Console"
        subtitle="Pinpoint active or at-risk sessions before they impact run reliability."
        statusTone={summaryStatusTone}
        statusLabel={summaryStatusLabel}
        metrics={[
          {
            id: "sessions-total",
            label: "Total sessions",
            value: summary.total,
            tone: "neutral",
          },
          {
            id: "sessions-active",
            label: "Active",
            value: summary.active,
            detail: summary.stale > 0 ? `${summary.stale} stale active sessions` : "No stale active sessions",
            tone: summary.active > 0 ? "info" : "neutral",
          },
          {
            id: "sessions-attention",
            label: "Needs attention",
            value: summary.attention,
            detail:
              summary.attention > 0 ? "Failures or error states detected" : "No failures currently flagged",
            tone: summary.attention > 0 ? "warning" : "success",
          },
          {
            id: "sessions-progress",
            label: "Files processed",
            value: completionText,
            detail: "Aggregate across listed sessions",
            tone: summary.fileTotal > 0 ? "success" : "neutral",
          },
        ]}
        actionChips={summaryActionChips}
      />

      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={1.5}
        alignItems={{ xs: "stretch", md: "flex-end" }}
      >
        <TextField
          id="sessions-filter-search"
          label="Search"
          placeholder="Session id, source, or status"
          value={query}
          onChange={(event) => updateFilters({ query: event.target.value })}
          fullWidth
        />
        <Stack spacing={0.5} sx={{ minWidth: { xs: "100%", md: 260 } }}>
          <Typography component="label" variant="body2" color="text.secondary" htmlFor="sessions-filter-status">
            View
          </Typography>
          <Box
            component="select"
            id="sessions-filter-status"
            value={statusFilter}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              updateFilters({ status: event.target.value as SessionFilter })
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
            <option value="all">All sessions</option>
            <option value="active">Active only</option>
            <option value="needs_attention">Needs attention</option>
            <option value="completed">Completed only</option>
          </Box>
        </Stack>
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <TableContainer
        component={Box}
        tabIndex={0}
        aria-label="Sessions table"
        sx={{ border: "1px solid", borderColor: "divider", borderRadius: 3 }}
      >
        <Table size="small" aria-label="Sessions table">
          <TableHead>
            <TableRow>
              <TableCell>Session ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Failed</TableCell>
              <TableCell>Updated</TableCell>
              <TableCell>Source</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredSessions.map((session) => {
              const progressPercent = toProgressPercent(session);
              const progressLabel = `${session.processed_count}/${session.total_files} (${progressPercent}%)`;
              const sessionJobsHref = toJobsContextHref({
                sessionId: session.session_id,
                status: statusFilter !== "all" ? statusFilter : undefined,
              });
              return (
                <TableRow
                  key={session.session_id}
                  hover
                  tabIndex={0}
                  role="button"
                  onClick={() => navigate(sessionJobsHref)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      navigate(sessionJobsHref);
                    }
                  }}
                  sx={{ cursor: "pointer" }}
                >
                  <TableCell sx={{ whiteSpace: "nowrap", fontFamily: "monospace", fontSize: 13 }}>
                    <Link
                      component={RouterLink}
                      to={sessionJobsHref}
                      underline="hover"
                      color="inherit"
                      onClick={(event) => event.stopPropagation()}
                    >
                      {session.session_id}
                    </Link>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    <StatusPill status={toSessionTone(session)} label={session.status} />
                  </TableCell>
                  <TableCell sx={{ minWidth: 220 }}>
                    <Stack spacing={0.5}>
                      <Typography variant="body2">{progressLabel}</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={progressPercent}
                        aria-label={`Progress for session ${session.session_id}`}
                        aria-valuetext={progressLabel}
                        sx={{ height: 8, borderRadius: 999 }}
                      />
                    </Stack>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>{session.failed_count}</TableCell>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    {new Date(session.updated_at).toLocaleString()}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 320 }}>
                    <Typography title={session.source_directory} noWrap>
                      {session.source_directory}
                    </Typography>
                  </TableCell>
                </TableRow>
              );
            })}
            {sortedSessions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>
                  <EmptyStatePanel
                    title="No sessions found"
                    description="Sessions appear once runs are started and processed."
                    primaryAction={
                      <Button component={RouterLink} to="/" variant="outlined">
                        Start a run
                      </Button>
                    }
                  />
                </TableCell>
              </TableRow>
            ) : null}
            {sortedSessions.length > 0 && filteredSessions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6}>
                  <EmptyStatePanel
                    title="No sessions match this view"
                    description={
                      query.trim().length > 0
                        ? `No sessions match "${query.trim()}". Try broadening the query or switch to related jobs.`
                        : "Adjust filters to recover the operational list, or inspect related jobs for drill-down."
                    }
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
                      ) : (
                        <Button component={RouterLink} to="/" variant="text">
                          Start a new run
                        </Button>
                      )
                    }
                    secondaryAction={
                      <Button component={RouterLink} to={contextualJobsHref} variant="outlined">
                        {hasContextualJobsHref ? "Open matching jobs" : "Inspect jobs"}
                      </Button>
                    }
                  />
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="body2" color="text.secondary">
        Need a deeper view? Track job-level timeline and retries in{" "}
        <Link component={RouterLink} to={contextualJobsHref} underline="hover">
          {hasContextualJobsHref ? "matching jobs context" : "Jobs"}
        </Link>
        .
      </Typography>
    </Stack>
  );
}
