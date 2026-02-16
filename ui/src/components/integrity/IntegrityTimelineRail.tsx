import { Box, Stack, Typography } from "@mui/material";
import type { SxProps, Theme } from "@mui/material/styles";

import type { IntegritySeverity, IntegrityTimelineEventViewModel } from "../../types";
import { StatusPill } from "../foundation/StatusPill";
import { mergeSx } from "../foundation/sx";

export type IntegrityTimelineEntry = IntegrityTimelineEventViewModel;

export interface IntegrityTimelineRailProps {
  events: IntegrityTimelineEntry[];
  testId?: string;
  itemTestIdPrefix?: string;
  sx?: SxProps<Theme>;
}

type TimelineChipStatus = "info" | "success" | "warning" | "error";

const severityMeta: Record<
  IntegritySeverity,
  { label: string; chipStatus: TimelineChipStatus; markerColor: string; remediationColor: string }
> = {
  info: {
    label: "Info",
    chipStatus: "info",
    markerColor: "info.main",
    remediationColor: "info.dark",
  },
  success: {
    label: "Healthy",
    chipStatus: "success",
    markerColor: "success.main",
    remediationColor: "success.dark",
  },
  warning: {
    label: "Needs Review",
    chipStatus: "warning",
    markerColor: "warning.main",
    remediationColor: "warning.dark",
  },
  error: {
    label: "Failure",
    chipStatus: "error",
    markerColor: "error.main",
    remediationColor: "error.dark",
  },
};

function formatTimestamp(value: string): string {
  const epoch = Date.parse(value);
  if (Number.isNaN(epoch)) {
    return value;
  }
  return new Date(epoch).toLocaleString();
}

export function IntegrityTimelineRail(props: IntegrityTimelineRailProps) {
  const { events, testId = "integrity-timeline-rail", itemTestIdPrefix, sx } = props;
  const baseSx = {
    listStyle: "none",
    m: 0,
    p: 0,
    display: "grid",
    gap: 1.25,
  };

  return (
    <Box component="ol" data-testid={testId} sx={mergeSx(baseSx, sx)}>
      {events.map((event, index) => {
        const meta = severityMeta[event.severity];
        return (
          <Box
            key={event.id}
            component="li"
            data-testid={itemTestIdPrefix ? `${itemTestIdPrefix}${index}` : undefined}
            sx={{
              display: "grid",
              gridTemplateColumns: "18px minmax(0, 1fr)",
              columnGap: 1.5,
            }}
          >
            <Box aria-hidden="true" sx={{ position: "relative", pt: 0.7 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  bgcolor: meta.markerColor,
                  border: "2px solid",
                  borderColor: "background.paper",
                  boxSizing: "border-box",
                }}
              />
              {index < events.length - 1 ? (
                <Box
                  sx={{
                    position: "absolute",
                    top: 14,
                    left: 5,
                    bottom: -18,
                    width: 2,
                    bgcolor: "divider",
                  }}
                />
              ) : null}
            </Box>
            <Stack spacing={0.75} sx={{ pb: 2 }}>
              <Stack
                direction={{ xs: "column", sm: "row" }}
                spacing={1}
                justifyContent="space-between"
                alignItems={{ xs: "flex-start", sm: "center" }}
              >
                <Typography component="h4" variant="subtitle2" sx={{ fontWeight: 700 }}>
                  {event.title}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <StatusPill size="small" status={meta.chipStatus} label={meta.label} />
                  <Typography component="time" dateTime={event.occurredAt} variant="caption" color="text.secondary">
                    {formatTimestamp(event.occurredAt)}
                  </Typography>
                </Stack>
              </Stack>
              <Typography variant="body2">{event.detail}</Typography>
              <Typography variant="body2" sx={{ color: meta.remediationColor }}>
                <Box component="span" sx={{ fontWeight: 700 }}>
                  Remediation:
                </Box>{" "}
                {event.remediation}
              </Typography>
            </Stack>
          </Box>
        );
      })}
    </Box>
  );
}
