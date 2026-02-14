import { useEffect, useState } from "react";

import {
  applyConfigPreset,
  getAuthSessionStatus,
  getEffectiveConfig,
  loginAuthSession,
  listConfigPresets,
  logoutAuthSession,
  previewConfigPreset,
} from "../api/client";
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
    }
  }

  async function runApply() {
    if (!selectedPreset) {
      return;
    }
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
    }
  }

  async function signInWithApiKey() {
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
    }
  }

  async function signOutSession() {
    setError(null);
    setAuthMessage(null);
    try {
      const sessionStatus = await logoutAuthSession();
      setAuthStatus(sessionStatus);
      setAuthMessage("Signed out. Session cookie cleared.");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to sign out";
      setError(message);
    }
  }

  return (
    <section className="panel" data-testid="config-page">
      <h2>Configuration</h2>
      <p className="muted">
        Review the effective runtime config, preview presets, and apply a preset for upcoming runs.
      </p>

      <fieldset className="field-group">
        <legend>Preset Control</legend>
        <label htmlFor="config-preset-select">
          <span>Preset</span>
        </label>
        <select
          id="config-preset-select"
          value={selectedPreset}
          onChange={(event) => setSelectedPreset(event.target.value)}
          data-testid="config-preset-select"
        >
          {presets.map((preset) => (
            <option key={preset.name} value={preset.name}>
              {preset.name}
              {preset.is_builtin ? " (builtin)" : ""}
            </option>
          ))}
        </select>
        <div className="actions-inline">
          <button type="button" className="secondary" onClick={runPreview} disabled={!selectedPreset}>
            Preview Preset
          </button>
          <button type="button" onClick={runApply} disabled={!selectedPreset}>
            Apply Preset
          </button>
        </div>
        {statusMessage ? <p className="help-text">{statusMessage}</p> : null}
      </fieldset>

      <fieldset className="field-group">
        <legend>API Security</legend>
        <label htmlFor="config-api-key-input">
          <span>API Key</span>
        </label>
        <input
          id="config-api-key-input"
          type="password"
          value={apiKeyInput}
          onChange={(event) => setApiKeyInput(event.target.value)}
          placeholder="Enter API key to create session"
          data-testid="config-api-key-input"
          autoComplete="off"
        />
        <div className="actions-inline">
          <button type="button" className="secondary" onClick={signInWithApiKey}>
            Sign In
          </button>
          <button type="button" onClick={signOutSession}>
            Sign Out
          </button>
        </div>
        <p className="help-text">{describeAuthSession(authStatus)}</p>
        {authMessage ? <p className="help-text">{authMessage}</p> : null}
      </fieldset>

      {error ? (
        <p className="inline-alert is-error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="config-grid">
        <article className="config-panel">
          <h3>Effective Config</h3>
          {loading ? (
            <p className="muted">Loading config...</p>
          ) : (
            <pre data-testid="config-effective-json">{prettyJson(effectiveConfig)}</pre>
          )}
        </article>
        <article className="config-panel">
          <h3>Preset Preview</h3>
          <pre data-testid="config-preview-json">{prettyJson(previewConfig)}</pre>
        </article>
      </div>
    </section>
  );
}
