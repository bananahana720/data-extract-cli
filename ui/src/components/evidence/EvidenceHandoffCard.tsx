import {
  Alert,
  Box,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
  type PaperProps,
} from "@mui/material";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ConstructionOutlinedIcon from "@mui/icons-material/ConstructionOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import SyncOutlinedIcon from "@mui/icons-material/SyncOutlined";
import TaskAltOutlinedIcon from "@mui/icons-material/TaskAltOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import { useId, type ReactNode } from "react";

import type { EvidenceReadinessState } from "../../types";
import type { SemanticStatus } from "../../theme/tokens";
import { SectionCard, StatusPill } from "../foundation";

export type { EvidenceReadinessState } from "../../types";

export interface EvidenceHandoffCardProps extends Omit<PaperProps, "title"> {
  title: ReactNode;
  state: EvidenceReadinessState;
  summary?: ReactNode;
  what: ReactNode;
  why: ReactNode;
  how: ReactNode;
  remediationHints?: ReactNode[];
  actionHints?: ReactNode[];
}

interface ReadinessDescriptor {
  label: string;
  status: SemanticStatus;
  severity: "success" | "warning" | "error" | "info";
  icon: ReactNode;
  defaultSummary: string;
}

const readinessDescriptors: Record<EvidenceReadinessState, ReadinessDescriptor> = {
  ready: {
    label: "Ready",
    status: "success",
    severity: "success",
    icon: <CheckCircleOutlineIcon fontSize="small" />,
    defaultSummary: "Evidence handoff is aligned and ready for execution.",
  },
  missing: {
    label: "Missing",
    status: "error",
    severity: "error",
    icon: <ErrorOutlineIcon fontSize="small" />,
    defaultSummary: "Required evidence inputs are missing and need remediation.",
  },
  stale: {
    label: "Stale",
    status: "warning",
    severity: "warning",
    icon: <WarningAmberOutlinedIcon fontSize="small" />,
    defaultSummary: "Evidence has drifted from current runtime intent.",
  },
  "in-progress": {
    label: "In Progress",
    status: "info",
    severity: "info",
    icon: <SyncOutlinedIcon fontSize="small" />,
    defaultSummary: "Evidence state is being evaluated.",
  },
};

interface EvidenceRowProps {
  label: "What" | "Why" | "How";
  value: ReactNode;
}

function EvidenceRow({ label, value }: EvidenceRowProps) {
  return (
    <Box
      component="div"
      sx={{
        display: "grid",
        gap: 0.75,
        gridTemplateColumns: { xs: "1fr", sm: "68px 1fr" },
      }}
    >
      <Typography component="dt" variant="body2" sx={{ m: 0, fontWeight: 700 }}>
        {label}
      </Typography>
      <Typography component="dd" variant="body2" sx={{ m: 0, color: "text.secondary" }}>
        {value}
      </Typography>
    </Box>
  );
}

interface HintListProps {
  title: string;
  icon: ReactNode;
  hints: ReactNode[];
}

function HintList({ title, icon, hints }: HintListProps) {
  if (hints.length === 0) {
    return null;
  }

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        {title}
      </Typography>
      <List dense disablePadding>
        {hints.map((hint, index) => (
          <ListItem key={`${title}-${index}`} disableGutters sx={{ alignItems: "flex-start", py: 0.25 }}>
            <ListItemIcon sx={{ minWidth: 28, mt: 0.1 }}>{icon}</ListItemIcon>
            <ListItemText
              primaryTypographyProps={{ variant: "body2", color: "text.secondary" }}
              primary={hint}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export function EvidenceHandoffCard(props: EvidenceHandoffCardProps) {
  const {
    title,
    state,
    summary,
    what,
    why,
    how,
    remediationHints = [],
    actionHints = [],
    ...paperProps
  } = props;
  const descriptor = readinessDescriptors[state];
  const headingId = useId();
  const summaryText = summary ?? descriptor.defaultSummary;

  return (
    <SectionCard
      {...paperProps}
      title={title}
      subtitle={summaryText}
      action={<StatusPill status={descriptor.status} label={descriptor.label} />}
      sx={{
        borderLeft: "4px solid",
        borderLeftColor:
          descriptor.status === "success"
            ? "success.main"
            : descriptor.status === "warning"
              ? "warning.main"
              : descriptor.status === "error"
                ? "error.main"
                : "info.main",
      }}
    >
      <Stack spacing={1.75}>
        <Alert
          severity={descriptor.severity}
          icon={descriptor.icon}
          role="note"
          aria-labelledby={headingId}
          sx={{ py: 0.5 }}
        >
          <Typography id={headingId} variant="body2" sx={{ fontWeight: 600 }}>
            Readiness: {descriptor.label}
          </Typography>
        </Alert>

        <Box component="dl" sx={{ m: 0, display: "grid", gap: 1 }}>
          <EvidenceRow label="What" value={what} />
          <EvidenceRow label="Why" value={why} />
          <EvidenceRow label="How" value={how} />
        </Box>

        {remediationHints.length > 0 || actionHints.length > 0 ? <Divider /> : null}
        <HintList
          title="Remediation Hints"
          icon={<ConstructionOutlinedIcon fontSize="small" />}
          hints={remediationHints}
        />
        <HintList title="Action Hints" icon={<TaskAltOutlinedIcon fontSize="small" />} hints={actionHints} />
      </Stack>
    </SectionCard>
  );
}
