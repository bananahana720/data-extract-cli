import { Box, Paper, Stack, Typography, type PaperProps } from "@mui/material";
import { useId, type ReactNode } from "react";

import { mergeSx } from "./sx";

export interface EmptyStatePanelProps extends Omit<PaperProps, "title"> {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
}

export function EmptyStatePanel(props: EmptyStatePanelProps) {
  const {
    title,
    description,
    icon,
    primaryAction,
    secondaryAction,
    sx,
    component = "section",
    variant = "outlined",
    ...paperProps
  } = props;
  const headingId = useId();
  const hasActions = Boolean(primaryAction) || Boolean(secondaryAction);

  return (
    <Paper
      {...paperProps}
      component={component}
      variant={variant}
      role={paperProps.role ?? "status"}
      aria-live={paperProps["aria-live"] ?? "polite"}
      aria-labelledby={headingId}
      sx={mergeSx(
        {
          borderRadius: 3,
          borderStyle: "dashed",
          p: 3,
          textAlign: "center",
        },
        sx
      )}
    >
      <Stack alignItems="center" spacing={1.25}>
        {icon ? (
          <Box aria-hidden="true" sx={{ color: "text.secondary", display: "inline-flex" }}>
            {icon}
          </Box>
        ) : null}
        <Typography id={headingId} component="h3" variant="h6">
          {title}
        </Typography>
        {description ? (
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 540 }}>
            {description}
          </Typography>
        ) : null}
        {hasActions ? (
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25} sx={{ mt: 0.5 }}>
            {primaryAction}
            {secondaryAction}
          </Stack>
        ) : null}
      </Stack>
    </Paper>
  );
}
