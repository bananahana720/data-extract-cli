import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  FormLabel,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import {
  applyConfigPreset,
  getAuthSessionStatus,
  getEffectiveConfig,
  loginAuthSession,
  listConfigPresets,
  logoutAuthSession,
  previewConfigPreset,
} from "../api/client";
import { EvidenceHandoffCard, type EvidenceReadinessState } from "../components/evidence";
import { GuidanceTip, PageSectionHeader, SectionCard } from "../components/foundation";
import { AuthSessionStatus, ConfigPresetSummary } from "../types";

function prettyJson(payload: Record<string, unknown> | null): string {
  if (!payload) {
    return "{}";
  }
  return JSON.stringify(payload, null, 2);
}

function describeAuthSession(status: AuthSessionStatus | null): string {
  if (!status) {
    return "Session status unavailable.";
  }
  if (!status.api_key_configured) {
    return "Server API key auth is not configured.";
  }
  if (!status.authenticated) {
    return "Session inactive. Sign in with API key to access secured endpoints.";
  }
  if (!status.expires_at) {
    return "Session active.";
  }
  return `Session active until ${new Date(status.expires_at).toLocaleString()}.`;
}

function configsMatch(
  effective: Record<string, unknown> | null,
  preview: Record<string, unknown> | null
): boolean {
  if (!effective || !preview) {
    return false;
  }
  return JSON.stringify(effective) === JSON.stringify(preview);
}

interface EvidenceDetails {
  state: EvidenceReadinessState;
  summary: string;
  remediationHints: string[];
  actionHints: string[];
}

function getPresetEvidenceDetails(args: {
  loading: boolean;
  previewing: boolean;
  applying: boolean;
  selectedPreset: string;
  effectiveConfig: Record<string, unknown> | null;
  previewConfig: Record<string, unknown> | null;
}): EvidenceDetails {
  const { loading, previewing, applying, selectedPreset, effectiveConfig, previewConfig } = args;

  if (loading || previewing || applying) {
    return {
      state: "in-progress",
      summary: "Evaluating preset evidence handoff state.",
      remediationHints: [],
      actionHints: ["Wait for the current request to complete before taking the next action."],
    };
  }

  if (!selectedPreset) {
    return {
      state: "missing",
      summary: "No preset is selected for evidence handoff.",
      remediationHints: ["Select a preset to define intended extraction behavior."],
      actionHints: ["Run Preview Preset first, then apply only after validation."],
    };
  }

  if (!previewConfig) {
    return {
      state: "missing",
      summary: "Preset preview evidence is missing.",
      remediationHints: ["Generate a preview to capture expected runtime values."],
      actionHints: ["Review preview JSON for chunking, semantic, and output impacts."],
    };
  }

  if (!configsMatch(effectiveConfig, previewConfig)) {
    return {
      state: "stale",
      summary: "Preview and effective config are out of sync.",
      remediationHints: ["Apply the preset or regenerate preview if the preset changed."],
      actionHints: ["Use Effective Config and Preset Preview panes to confirm drift is resolved."],
    };
  }

  return {
    state: "ready",
    summary: "Preview and effective config are aligned for handoff.",
    remediationHints: ["Capture this state as runbook evidence before the next config change."],
    actionHints: ["Proceed with new runs using the validated preset configuration."],
  };
}

function getAuthEvidenceDetails(args: {
  loading: boolean;
  authBusy: boolean;
  authStatus: AuthSessionStatus | null;
}): EvidenceDetails {
  const { loading, authBusy, authStatus } = args;

  if (loading || authBusy) {
    return {
      state: "in-progress",
      summary: "Session readiness is still being evaluated.",
      remediationHints: [],
      actionHints: ["Wait for session status to finish loading before secure actions."],
    };
  }

  if (!authStatus) {
    return {
      state: "missing",
      summary: "Session status is unavailable.",
      remediationHints: ["Check API connectivity and reload configuration controls."],
      actionHints: ["Re-authenticate once the status endpoint responds."],
    };
  }

  if (!authStatus.api_key_configured) {
    return {
      state: "missing",
      summary: "Server API key auth is not configured.",
      remediationHints: ["Enable server-side API key auth before using secured endpoints."],
      actionHints: ["Coordinate config changes with infrastructure ownership."],
    };
  }

  if (!authStatus.authenticated) {
    return {
      state: "stale",
      summary: "Session is inactive for secured config operations.",
      remediationHints: ["Sign in with API key to establish an active session cookie."],
      actionHints: ["Sign out after completing sensitive config changes."],
    };
  }

  return {
    state: "ready",
    summary: "Session is authenticated for secured preset actions.",
    remediationHints: ["Rotate API keys periodically and monitor expiry timestamps."],
    actionHints: ["Apply and validate presets while the authenticated session is active."],
  };
}

function getSnapshotEvidenceDetails(args: {
  loading: boolean;
  effectiveConfig: Record<string, unknown> | null;
  previewConfig: Record<string, unknown> | null;
}): EvidenceDetails {
  const { loading, effectiveConfig, previewConfig } = args;

  if (loading) {
    return {
      state: "in-progress",
      summary: "Effective config snapshot is loading.",
      remediationHints: [],
      actionHints: ["Wait for effective runtime values before handing off evidence."],
    };
  }

  if (!effectiveConfig) {
    return {
      state: "missing",
      summary: "Effective config snapshot is not available.",
      remediationHints: ["Reload configuration to fetch active runtime settings."],
      actionHints: ["Avoid applying new presets until effective config is visible."],
    };
  }

  if (previewConfig && !configsMatch(effectiveConfig, previewConfig)) {
    return {
      state: "stale",
      summary: "Effective runtime snapshot differs from latest preview.",
      remediationHints: ["Apply the validated preview or regenerate it to remove drift."],
      actionHints: ["Confirm JSON parity in both panels before run execution."],
    };
  }

  return {
    state: "ready",
    summary: "Effective runtime snapshot is current and handoff-ready.",
    remediationHints: ["Archive this snapshot when documenting release evidence."],
    actionHints: ["Proceed to execution with confidence in current runtime settings."],
  };
}

export function ConfigPage() {
  const [presets, setPresets] = useState<ConfigPresetSummary[]>([]);
  const [effectiveConfig, setEffectiveConfig] = useState<Record<string, unknown> | null>(null);
  const [previewConfig, setPreviewConfig] = useState<Record<string, unknown> | null>(null);
  const [selectedPreset, setSelectedPreset] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [authStatus, setAuthStatus] = useState<AuthSessionStatus | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [effective, presetList, sessionStatus] = await Promise.all([
          getEffectiveConfig(),
          listConfigPresets(),
          getAuthSessionStatus()
        ]);
        setEffectiveConfig(effective);
        setPresets(presetList);
        setAuthStatus(sessionStatus);
        if (presetList.length > 0) {
          setSelectedPreset((current) => current || presetList[0].name);
        }
      } catch (requestError) {
        const message =
          requestError instanceof Error ? requestError.message : "Unable to load configuration";
        setError(
          /Unauthorized/i.test(message)
            ? "Unauthorized. Sign in below to access secured API endpoints."
            : message
        );
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function runPreview() {
    if (!selectedPreset) {
      return;
    }
    setPreviewing(true);
    setStatusMessage(null);
    setError(null);
    try {
      const preview = await previewConfigPreset(selectedPreset);
      setPreviewConfig(preview);
      setStatusMessage(`Preview loaded for preset "${selectedPreset}".`);
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Unable to preview preset";
      setError(
        /Unauthorized/i.test(message)
          ? "Unauthorized. Sign in below to preview secured endpoints."
          : message
      );
    } finally {
      setPreviewing(false);
    }
  }

  async function runApply() {
    if (!selectedPreset) {
      return;
    }
    setApplying(true);
    setStatusMessage(null);
    setError(null);
    try {
      const appliedConfig = await applyConfigPreset(selectedPreset);
      setEffectiveConfig(appliedConfig);
      setPreviewConfig(appliedConfig);
      setStatusMessage(`Applied preset "${selectedPreset}".`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to apply preset";
      setError(
        /Unauthorized/i.test(message)
          ? "Unauthorized. Sign in below to apply secured endpoints."
          : message
      );
    } finally {
      setApplying(false);
    }
  }

  async function signInWithApiKey() {
    setAuthBusy(true);
    setError(null);
    setAuthMessage(null);
    try {
      const sessionStatus = await loginAuthSession(apiKeyInput);
      setAuthStatus(sessionStatus);
      setApiKeyInput("");
      setAuthMessage("Signed in. Session cookie is active.");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to sign in";
      setError(/Unauthorized/i.test(message) ? "Unauthorized. API key is invalid." : message);
    } finally {
      setAuthBusy(false);
    }
  }

  async function signOutSession() {
    setAuthBusy(true);
    setError(null);
    setAuthMessage(null);
    try {
      const sessionStatus = await logoutAuthSession();
      setAuthStatus(sessionStatus);
      setAuthMessage("Signed out. Session cookie cleared.");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to sign out";
      setError(message);
    } finally {
      setAuthBusy(false);
    }
  }

  const presetEvidence = useMemo(
    () =>
      getPresetEvidenceDetails({
        loading,
        previewing,
        applying,
        selectedPreset,
        effectiveConfig,
        previewConfig,
      }),
    [loading, previewing, applying, selectedPreset, effectiveConfig, previewConfig]
  );
  const authEvidence = useMemo(
    () =>
      getAuthEvidenceDetails({
        loading,
        authBusy,
        authStatus,
      }),
    [loading, authBusy, authStatus]
  );
  const snapshotEvidence = useMemo(
    () =>
      getSnapshotEvidenceDetails({
        loading,
        effectiveConfig,
        previewConfig,
      }),
    [loading, effectiveConfig, previewConfig]
  );

  return (
    <Box component="section" data-testid="config-page" sx={{ display: "grid", gap: 2.5, py: { xs: 2, md: 3 } }}>
      <PageSectionHeader
        eyebrow="Evidence + Config"
        title="Configuration"
        subtitle="Review runtime configuration, verify preset previews, and hand off validated config states."
      />

      <GuidanceTip
        title="Evidence-Readiness Workflow"
        what="Treat each config change as an evidence handoff from intent to runtime."
        why="Preview and effective config alignment prevents drift and unclear execution behavior."
        how="Select a preset, preview the expected JSON, apply only when validated, then confirm effective config parity."
      />

      {error ? (
        <Alert severity="error" role="alert">
          {error}
        </Alert>
      ) : null}

      <Box
        sx={{
          display: "grid",
          gap: 2.5,
          alignItems: "start",
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1.35fr) minmax(0, 1fr)" },
        }}
      >
        <Stack spacing={2.5}>
          <SectionCard
            title="Preset Control"
            subtitle="Preview and apply preset changes with clear evidence handoff checkpoints."
          >
            <Stack spacing={2}>
              <GuidanceTip
                title="Preset Action Tip"
                what="Generate preview evidence before applying a preset."
                why="Applying unreviewed presets can alter extraction behavior for upcoming runs."
                how="Preview first, review the JSON impact, then apply once readiness is confirmed."
              />
              <FormControl fullWidth>
                <FormLabel htmlFor="config-preset-select" sx={{ mb: 0.75, fontWeight: 600 }}>
                  Preset
                </FormLabel>
                <Box
                  component="select"
                  id="config-preset-select"
                  value={selectedPreset}
                  onChange={(event) => setSelectedPreset(event.target.value)}
                  data-testid="config-preset-select"
                  aria-label="Preset"
                  sx={{
                    width: "100%",
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 2,
                    px: 1.5,
                    py: 1,
                    backgroundColor: "background.paper",
                    color: "text.primary",
                    fontFamily: "inherit",
                    fontSize: "0.95rem",
                    lineHeight: 1.45,
                    "&:focus-visible": {
                      outline: "2px solid",
                      outlineColor: "primary.light",
                      outlineOffset: 1,
                    },
                  }}
                >
                  {presets.map((preset) => (
                    <option key={preset.name} value={preset.name}>
                      {preset.name}
                      {preset.is_builtin ? " (builtin)" : ""}
                    </option>
                  ))}
                </Box>
              </FormControl>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25}>
                <Button
                  type="button"
                  variant="outlined"
                  onClick={() => void runPreview()}
                  disabled={!selectedPreset || previewing || applying}
                >
                  {previewing ? "Previewing..." : "Preview Preset"}
                </Button>
                <Button
                  type="button"
                  variant="contained"
                  onClick={() => void runApply()}
                  disabled={!selectedPreset || previewing || applying}
                >
                  {applying ? "Applying..." : "Apply Preset"}
                </Button>
              </Stack>
              {statusMessage ? <Alert severity="success">{statusMessage}</Alert> : null}
            </Stack>
          </SectionCard>

          <SectionCard
            title="API Security"
            subtitle="Use authenticated sessions for secured configuration endpoints."
          >
            <Stack spacing={2}>
              <GuidanceTip
                title="Session Action Tip"
                severity={authStatus?.authenticated ? "success" : "info"}
                what="API key sign-in creates a session cookie for protected config operations."
                why="Session-based auth keeps credentials out of requests and supports auditable access."
                how="Enter API key, sign in, complete secured actions, and sign out after finishing."
              />
              <TextField
                id="config-api-key-input"
                label="API Key"
                type="password"
                value={apiKeyInput}
                onChange={(event) => setApiKeyInput(event.target.value)}
                placeholder="Enter API key to create session"
                autoComplete="off"
                inputProps={{ "data-testid": "config-api-key-input" }}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25}>
                <Button
                  type="button"
                  variant="outlined"
                  onClick={() => void signInWithApiKey()}
                  disabled={authBusy}
                >
                  Sign In
                </Button>
                <Button
                  type="button"
                  variant="contained"
                  color="secondary"
                  onClick={() => void signOutSession()}
                  disabled={authBusy}
                >
                  Sign Out
                </Button>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                {describeAuthSession(authStatus)}
              </Typography>
              {authMessage ? <Alert severity="info">{authMessage}</Alert> : null}
            </Stack>
          </SectionCard>
        </Stack>

        <Stack spacing={2.5}>
          <EvidenceHandoffCard
            title="Preset Evidence Handoff"
            state={presetEvidence.state}
            summary={presetEvidence.summary}
            what="Preset selection and preview output represent intended extraction behavior."
            why="Validated handoff ensures downstream jobs inherit explicit, reviewed configuration."
            how="Use preview/apply controls and verify JSON alignment before executing runs."
            remediationHints={presetEvidence.remediationHints}
            actionHints={presetEvidence.actionHints}
          />
          <EvidenceHandoffCard
            title="Session Readiness Handoff"
            state={authEvidence.state}
            summary={authEvidence.summary}
            what="Session state controls access to secured config and preset endpoints."
            why="Authentication readiness prevents blocked updates and untracked configuration changes."
            how="Sign in with API key when required, complete changes, then sign out."
            remediationHints={authEvidence.remediationHints}
            actionHints={authEvidence.actionHints}
          />
          <EvidenceHandoffCard
            title="Runtime Snapshot Handoff"
            state={snapshotEvidence.state}
            summary={snapshotEvidence.summary}
            what="Effective config is the runtime source of truth for upcoming jobs."
            why="Snapshot parity with preview confirms intended behavior is actually active."
            how="Compare effective and preview JSON panels before handing off execution."
            remediationHints={snapshotEvidence.remediationHints}
            actionHints={snapshotEvidence.actionHints}
          />
        </Stack>
      </Box>

      <Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" } }}>
        <SectionCard title="Effective Config" subtitle="Currently active runtime configuration values.">
          {loading ? (
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                Loading config...
              </Typography>
            </Stack>
          ) : (
            <Box
              component="pre"
              data-testid="config-effective-json"
              tabIndex={0}
              aria-label="Effective configuration JSON"
              sx={{
                mt: 0,
                mb: 0,
                p: 1.5,
                borderRadius: 2,
                border: "1px solid",
                borderColor: "divider",
                backgroundColor: "background.default",
                color: "text.primary",
                fontFamily: '"IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace',
                fontSize: "0.8rem",
                lineHeight: 1.45,
                overflow: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                maxHeight: 440,
              }}
            >
              {prettyJson(effectiveConfig)}
            </Box>
          )}
        </SectionCard>

        <SectionCard title="Preset Preview" subtitle="Expected values before promoting to runtime.">
          <Box
            component="pre"
            data-testid="config-preview-json"
            tabIndex={0}
            aria-label="Preset preview JSON"
            sx={{
              mt: 0,
              mb: 0,
              p: 1.5,
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              backgroundColor: "background.default",
              color: "text.primary",
              fontFamily: '"IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace',
              fontSize: "0.8rem",
              lineHeight: 1.45,
              overflow: "auto",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              maxHeight: 440,
            }}
          >
            {prettyJson(previewConfig)}
          </Box>
        </SectionCard>
      </Box>
    </Box>
  );
}
