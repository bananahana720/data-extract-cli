import { Box, Stack, Typography } from "@mui/material";
import type { SxProps, Theme } from "@mui/material/styles";
import { useId, type ReactNode } from "react";

import { mergeSx } from "./sx";

export interface PageSectionHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  eyebrow?: ReactNode;
  action?: ReactNode;
  sx?: SxProps<Theme>;
}

export function PageSectionHeader({ title, subtitle, eyebrow, action, sx }: PageSectionHeaderProps) {
  const titleId = useId();

  return (
    <Box
      component="header"
      aria-labelledby={titleId}
      sx={mergeSx(
        {
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
          alignItems: { xs: "flex-start", md: "center" },
          justifyContent: "space-between",
          gap: 2,
          mb: 2,
        },
        sx
      )}
    >
      <Stack spacing={0.5}>
        {eyebrow ? (
          <Typography variant="overline" color="text.secondary">
            {eyebrow}
          </Typography>
        ) : null}
        <Typography id={titleId} component="h2" variant="h5" sx={{ lineHeight: 1.15 }}>
          {title}
        </Typography>
        {subtitle ? (
          <Typography variant="body1" color="text.secondary">
            {subtitle}
          </Typography>
        ) : null}
      </Stack>
      {action ? <Box sx={{ flexShrink: 0 }}>{action}</Box> : null}
    </Box>
  );
}
