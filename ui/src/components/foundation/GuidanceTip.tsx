import { Alert, AlertTitle, Box, Stack, Typography, type AlertProps } from "@mui/material";
import { useId, type ReactNode } from "react";

import { mergeSx } from "./sx";

export interface GuidanceTipProps extends Omit<AlertProps, "title"> {
  title?: ReactNode;
  what: ReactNode;
  why?: ReactNode;
  how?: ReactNode;
  action?: ReactNode;
}

interface GuidanceRowProps {
  label: "What" | "Why" | "How";
  value: ReactNode;
}

function GuidanceRow({ label, value }: GuidanceRowProps) {
  return (
    <Box component="div" sx={{ display: "grid", gap: 0.75, gridTemplateColumns: { xs: "1fr", sm: "72px 1fr" } }}>
      <Typography component="dt" variant="body2" sx={{ m: 0, fontWeight: 700, color: "text.primary" }}>
        {label}
      </Typography>
      <Typography component="dd" variant="body2" sx={{ m: 0, color: "text.secondary" }}>
        {value}
      </Typography>
    </Box>
  );
}

export function GuidanceTip(props: GuidanceTipProps) {
  const { title = "Guidance", what, why, how, action, severity = "info", role, sx, ...alertProps } = props;
  const headingId = useId();

  return (
    <Alert
      {...alertProps}
      severity={severity}
      role={role ?? "note"}
      aria-labelledby={headingId}
      sx={mergeSx(
        {
          "& .MuiAlert-message": {
            width: "100%",
          },
        },
        sx
      )}
    >
      <AlertTitle id={headingId} sx={{ mb: 1 }}>
        {title}
      </AlertTitle>
      <Box component="dl" sx={{ m: 0, display: "grid", gap: 1 }}>
        <GuidanceRow label="What" value={what} />
        {why ? <GuidanceRow label="Why" value={why} /> : null}
        {how ? <GuidanceRow label="How" value={how} /> : null}
      </Box>
      {action ? <Stack sx={{ mt: 2 }}>{action}</Stack> : null}
    </Alert>
  );
}
