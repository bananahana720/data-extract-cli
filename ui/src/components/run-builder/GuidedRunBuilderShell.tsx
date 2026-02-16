import { Box, Stack, type SxProps, type Theme } from "@mui/material";
import { type ReactNode } from "react";

import { PageSectionHeader } from "../foundation";

export interface GuidedRunBuilderShellProps {
  title: ReactNode;
  subtitle: ReactNode;
  eyebrow?: ReactNode;
  contextPanel: ReactNode;
  builderPanel: ReactNode;
  verifyPanel: ReactNode;
  sx?: SxProps<Theme>;
}

export function GuidedRunBuilderShell({
  title,
  subtitle,
  eyebrow,
  contextPanel,
  builderPanel,
  verifyPanel,
  sx
}: GuidedRunBuilderShellProps) {
  return (
    <Stack spacing={3} sx={sx}>
      <PageSectionHeader title={title} subtitle={subtitle} eyebrow={eyebrow} />
      {contextPanel}
      <Box
        sx={{
          display: "grid",
          gap: 3,
          gridTemplateColumns: {
            xs: "minmax(0, 1fr)",
            lg: "minmax(0, 1.65fr) minmax(300px, 1fr)"
          },
          alignItems: "start"
        }}
      >
        <Box>{builderPanel}</Box>
        <Box sx={{ position: { lg: "sticky" }, top: { lg: 20 } }}>{verifyPanel}</Box>
      </Box>
    </Stack>
  );
}
