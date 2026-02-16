import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import type { SxProps, Theme } from "@mui/material/styles";
import { type ReactNode } from "react";
import { Link as RouterLink } from "react-router-dom";

import { statusTokens, type SemanticStatus } from "../../theme/tokens";
import { StatusPill } from "../foundation";
import { mergeSx } from "../foundation/sx";

const defaultMetricTone: SemanticStatus = "neutral";

function toneCardSx(tone: SemanticStatus): SxProps<Theme> {
  const token = statusTokens[tone];
  return {
    borderColor: token.border,
    backgroundColor: alpha(token.background, 0.7),
  };
}

function toneChipSx(tone: SemanticStatus): SxProps<Theme> {
  const token = statusTokens[tone];
  return {
    borderColor: token.border,
    backgroundColor: token.background,
    color: token.foreground,
    fontWeight: 600,
    "&.Mui-disabled": {
      borderColor: alpha(token.foreground, 0.3),
      backgroundColor: alpha(token.background, 0.9),
      color: alpha(token.foreground, 0.88),
      opacity: 1,
    },
    "&.Mui-disabled .MuiChip-label": {
      color: "inherit",
    },
  };
}

function resolveActionLinkProps(href: string): Record<string, unknown> {
  if (href.startsWith("/")) {
    return {
      component: RouterLink,
      to: href,
    };
  }

  return {
    component: "a",
    href,
    rel: "noreferrer",
    target: "_blank",
  };
}

export interface ControlTowerStatusMetric {
  id: string;
  label: ReactNode;
  value: ReactNode;
  detail?: ReactNode;
  tone?: SemanticStatus;
  href?: string;
  testId?: string;
}

export interface ControlTowerActionChip {
  id: string;
  label: string;
  tone?: SemanticStatus;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  ariaLabel?: string;
}

export interface ControlTowerStatusConsoleProps {
  title: ReactNode;
  subtitle?: ReactNode;
  statusLabel?: string;
  statusTone?: SemanticStatus;
  metrics: ControlTowerStatusMetric[];
  actionChips?: ControlTowerActionChip[];
  footer?: ReactNode;
  testId?: string;
  sx?: SxProps<Theme>;
}

export function ControlTowerStatusConsole(props: ControlTowerStatusConsoleProps) {
  const {
    title,
    subtitle,
    statusLabel,
    statusTone = "info",
    metrics,
    actionChips = [],
    footer,
    testId,
    sx,
  } = props;
  const metricColumnCount = Math.max(1, Math.min(4, metrics.length));

  return (
    <Paper
      component="section"
      variant="outlined"
      data-testid={testId}
      sx={mergeSx(
        {
          borderRadius: 3,
          p: 3,
        },
        sx
      )}
    >
      <Stack spacing={2}>
        <Stack
          direction={{ xs: "column", md: "row" }}
          alignItems={{ xs: "flex-start", md: "center" }}
          justifyContent="space-between"
          spacing={1.5}
        >
          <Box>
            <Typography component="h3" variant="h6">
              {title}
            </Typography>
            {subtitle ? (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {statusLabel ? <StatusPill status={statusTone} label={statusLabel} /> : null}
        </Stack>

        <Box
          sx={{
            display: "grid",
            gap: 1.5,
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              lg: `repeat(${metricColumnCount}, minmax(0, 1fr))`,
            },
          }}
        >
          {metrics.map((metric) => {
            const tone = metric.tone ?? defaultMetricTone;
            const linkProps = metric.href ? resolveActionLinkProps(metric.href) : {};
            return (
              <Paper
                key={metric.id}
                component="article"
                variant="outlined"
                data-testid={metric.testId}
                sx={mergeSx(
                  {
                    p: 1.75,
                    borderRadius: 2.5,
                  },
                  toneCardSx(tone)
                )}
              >
                <Stack spacing={0.75}>
                  <Typography variant="caption" color="text.secondary">
                    {metric.label}
                  </Typography>
                  <Typography variant="h4" sx={{ lineHeight: 1.1 }}>
                    {metric.value}
                  </Typography>
                  {metric.detail ? (
                    <Typography variant="body2" color="text.secondary">
                      {metric.detail}
                    </Typography>
                  ) : null}
                  {metric.href ? (
                    <Typography
                      variant="body2"
                      {...linkProps}
                      sx={{
                        color: "text.primary",
                        fontWeight: 600,
                        textDecoration: "none",
                        "&:hover": {
                          textDecoration: "underline",
                        },
                      }}
                    >
                      View details
                    </Typography>
                  ) : null}
                </Stack>
              </Paper>
            );
          })}
        </Box>

        {actionChips.length > 0 ? (
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            {actionChips.map((action) => {
              const tone = action.tone ?? defaultMetricTone;
              const canInteract = !action.disabled && (Boolean(action.onClick) || Boolean(action.href));
              const linkProps = canInteract && action.href ? resolveActionLinkProps(action.href) : {};
              return (
                <Chip
                  key={action.id}
                  label={action.label}
                  variant="outlined"
                  size="small"
                  aria-label={action.ariaLabel}
                  onClick={action.disabled ? undefined : action.onClick}
                  disabled={action.disabled}
                  clickable={canInteract}
                  {...linkProps}
                  sx={toneChipSx(tone)}
                />
              );
            })}
          </Stack>
        ) : null}

        {footer ? (
          <Typography variant="body2" color="text.secondary">
            {footer}
          </Typography>
        ) : null}
      </Stack>
    </Paper>
  );
}
