import { Box, Paper, Stack, Typography, type PaperProps } from "@mui/material";
import { useId, type ReactNode } from "react";

import { shapeTokens, spacingTokens } from "../../theme/tokens";
import { mergeSx } from "./sx";

export interface SectionCardProps extends Omit<PaperProps, "title"> {
  title?: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  noPadding?: boolean;
}

export function SectionCard(props: SectionCardProps) {
  const {
    title,
    subtitle,
    action,
    noPadding = false,
    children,
    sx,
    component = "section",
    variant = "outlined",
    ...paperProps
  } = props;
  const headingId = useId();
  const hasHeader = Boolean(title) || Boolean(subtitle) || Boolean(action);

  return (
    <Paper
      {...paperProps}
      component={component}
      variant={variant}
      role={paperProps.role ?? "region"}
      aria-labelledby={title ? headingId : undefined}
      sx={mergeSx(
        {
          borderRadius: `${shapeTokens.radius.lg}px`,
          p: noPadding ? 0 : `${spacingTokens.lg}px`,
        },
        sx
      )}
    >
      {hasHeader ? (
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={`${spacingTokens.md}px`}
          alignItems={{ xs: "flex-start", md: "center" }}
          justifyContent="space-between"
          sx={{ mb: `${spacingTokens.md}px` }}
        >
          <Box>
            {title ? (
              <Typography
                id={headingId}
                component="h2"
                variant="h6"
                sx={{ mb: subtitle ? `${spacingTokens.xxs}px` : 0 }}
              >
                {title}
              </Typography>
            ) : null}
            {subtitle ? (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {action ? <Box sx={{ flexShrink: 0 }}>{action}</Box> : null}
        </Stack>
      ) : null}
      {children}
    </Paper>
  );
}
