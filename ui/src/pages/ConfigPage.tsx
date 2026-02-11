import { useEffect, useState } from "react";

import {
  applyConfigPreset,
  getEffectiveConfig,
  listConfigPresets,
  previewConfigPreset
} from "../api/client";
import { ConfigPresetSummary } from "../types";

function prettyJson(payload: Record<string, unknown> | null): string {
  if (!payload) {
    return "{}";
  }
  return JSON.stringify(payload, null, 2);
}

export function ConfigPage() {
  const [presets, setPresets] = useState<ConfigPresetSummary[]>([]);
  const [effectiveConfig, setEffectiveConfig] = useState<Record<string, unknown> | null>(null);
  const [previewConfig, setPreviewConfig] = useState<Record<string, unknown> | null>(null);
  const [selectedPreset, setSelectedPreset] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [effective, presetList] = await Promise.all([
          getEffectiveConfig(),
          listConfigPresets()
        ]);
        setEffectiveConfig(effective);
        setPresets(presetList);
        if (presetList.length > 0) {
          setSelectedPreset((current) => current || presetList[0].name);
        }
      } catch (requestError) {
        const message =
          requestError instanceof Error ? requestError.message : "Unable to load configuration";
        setError(message);
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
      setError(message);
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
