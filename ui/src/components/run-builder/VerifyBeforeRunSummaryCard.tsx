import {
  Alert,
  AlertTitle,
  Box,
  Checkbox,
  FormControlLabel,
  Stack,
  Typography
} from "@mui/material";
import { type ReactNode } from "react";

import type { RunReadinessState } from "../../types";
import { GuidanceTip, SectionCard, StatusPill } from "../foundation";

export interface RunSummaryEntry {
  label: ReactNode;
  value: ReactNode;
}

export interface VerifyBeforeRunSummaryCardProps {
  summaryEntries: RunSummaryEntry[];
  blockingIssues: string[];
  acknowledged: boolean;
  staleAcknowledgementMessage?: string;
  onAcknowledgedChange: (checked: boolean) => void;
  acknowledgementDisabled?: boolean;
  acknowledgementLabel?: ReactNode;
  "data-testid"?: string;
}

function getRunReadinessState(args: {
  hasBlockingIssues: boolean;
  acknowledged: boolean;
  staleAcknowledgementMessage?: string;
}): RunReadinessState {
  const { hasBlockingIssues, acknowledged, staleAcknowledgementMessage } = args;
  if (hasBlockingIssues) {
    return "blocked";
  }
  if (acknowledged) {
    return "ready";
  }
  if (staleAcknowledgementMessage) {
    return "stale";
  }
  return "pending";
}

export function VerifyBeforeRunSummaryCard({
  summaryEntries,
  blockingIssues,
  acknowledged,
  staleAcknowledgementMessage,
  onAcknowledgedChange,
  acknowledgementDisabled = false,
  acknowledgementLabel = "I verified source, format, and semantic options for this run.",
  "data-testid": dataTestId = "new-run-summary-card"
}: VerifyBeforeRunSummaryCardProps) {
  const hasBlockingIssues = blockingIssues.length > 0;
  const runReadinessState = getRunReadinessState({
    hasBlockingIssues,
    acknowledged,
    staleAcknowledgementMessage
  });

  const status = runReadinessState === "blocked" ? "warning" : runReadinessState === "ready" ? "success" : "neutral";
  const statusLabel =
    runReadinessState === "blocked"
      ? `Blocked (${blockingIssues.length})`
      : runReadinessState === "ready"
        ? "Verified"
        : "Pending Verify";

  return (
    <SectionCard
      title="Verify Before Run"
      subtitle="Review configuration and acknowledge before starting."
      data-testid={dataTestId}
      action={<StatusPill status={status} label={statusLabel} />}
      sx={{ display: "grid", gap: 2 }}
    >
      <GuidanceTip
        severity={hasBlockingIssues ? "warning" : "info"}
        title="Run Gate"
        what="Run launch is gated by blocking validation and operator acknowledgement."
        why="This prevents invalid submissions and reduces avoidable retries."
        how="Resolve every blocking reason, then check the verify box."
      />

      <Box component="dl" sx={{ m: 0, display: "grid", gap: 1.25 }}>
        {summaryEntries.map((entry, index) => (
          <Box
            key={`summary-entry-${index}`}
            component="div"
            sx={{ display: "grid", gap: 0.5, gridTemplateColumns: { xs: "1fr", sm: "120px 1fr" } }}
          >
            <Typography component="dt" variant="body2" sx={{ m: 0, color: "text.secondary", fontWeight: 700 }}>
              {entry.label}
            </Typography>
            <Typography component="dd" variant="body2" sx={{ m: 0 }}>
              {entry.value}
            </Typography>
          </Box>
        ))}
      </Box>

      {hasBlockingIssues ? (
        <Alert severity="warning" role="alert" aria-live="assertive">
          <AlertTitle>Blocking Reasons</AlertTitle>
          <Stack component="ul" spacing={0.75} sx={{ m: 0, pl: 2 }}>
            {blockingIssues.map((issue) => (
              <Typography component="li" variant="body2" key={issue}>
                {issue}
              </Typography>
            ))}
          </Stack>
        </Alert>
      ) : (
        <Alert severity="success" role="status" aria-live="polite">
          <AlertTitle>Validation Clear</AlertTitle>
          No blocking issues detected.
        </Alert>
      )}

      <Stack spacing={0.5}>
        <FormControlLabel
          control={
            <Checkbox
              checked={acknowledged}
              onChange={(event) => onAcknowledgedChange(event.target.checked)}
              disabled={acknowledgementDisabled}
              inputProps={{ "data-testid": "new-run-verify-ack" } as Record<string, string>}
            />
          }
          label={acknowledgementLabel}
        />
        {staleAcknowledgementMessage ? (
          <Typography variant="body2" color="warning.main" data-testid="new-run-verify-stale-note">
            {staleAcknowledgementMessage}
          </Typography>
        ) : null}
      </Stack>
    </SectionCard>
  );
}
