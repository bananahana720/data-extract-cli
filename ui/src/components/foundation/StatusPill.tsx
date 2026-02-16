import { Chip, type ChipProps } from "@mui/material";

import { statusTokens, type SemanticStatus } from "../../theme/tokens";
import { mergeSx } from "./sx";

const defaultLabels: Record<SemanticStatus, string> = {
  neutral: "Neutral",
  info: "Info",
  success: "Success",
  warning: "Warning",
  error: "Error",
};

export interface StatusPillProps extends Omit<ChipProps, "color" | "label"> {
  status: SemanticStatus;
  label?: string;
}

export function StatusPill(props: StatusPillProps) {
  const { status, label, size = "small", sx, ...chipProps } = props;
  const resolvedLabel = label ?? defaultLabels[status];
  const statusColor = statusTokens[status];

  return (
    <Chip
      {...chipProps}
      size={size}
      label={resolvedLabel}
      aria-label={chipProps["aria-label"] ?? `Status: ${resolvedLabel}`}
      sx={mergeSx(
        {
          backgroundColor: statusColor.background,
          color: statusColor.foreground,
          border: "1px solid",
          borderColor: statusColor.border,
          fontWeight: 600,
          "& .MuiChip-label": {
            px: 1.25,
            lineHeight: 1.25,
          },
        },
        sx
      )}
    />
  );
}
