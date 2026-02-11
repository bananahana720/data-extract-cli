import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createProcessJob, createProcessJobWithFiles, listConfigPresets } from "../api/client";
import { ConfigPresetSummary } from "../types";

type SourceMode = "path" | "upload";
type FieldErrors = {
  path?: string;
  upload?: string;
  chunkSize?: string;
};

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export function NewRunPage() {
  const navigate = useNavigate();
  const filesInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [sourceMode, setSourceMode] = useState<SourceMode>("path");
  const [inputPath, setInputPath] = useState("");
  const [chunkSizeInput, setChunkSizeInput] = useState("512");
  const [outputFormat, setOutputFormat] = useState("json");
  const [preset, setPreset] = useState("");
  const [availablePresets, setAvailablePresets] = useState<ConfigPresetSummary[]>([]);
  const [recursive, setRecursive] = useState(true);
  const [incremental, setIncremental] = useState(false);
  const [semanticEnabled, setSemanticEnabled] = useState(false);
  const [semanticReport, setSemanticReport] = useState(false);
  const [semanticExportGraph, setSemanticExportGraph] = useState(false);
  const [semanticReportFormat, setSemanticReportFormat] = useState("json");
  const [semanticGraphFormat, setSemanticGraphFormat] = useState("json");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitFeedback, setSubmitFeedback] = useState("");

  const fileNames = useMemo(() => selectedFiles.map((file) => file.name), [selectedFiles]);
  const totalUploadBytes = useMemo(
    () => selectedFiles.reduce((total, file) => total + file.size, 0),
    [selectedFiles]
  );

  useEffect(() => {
    async function loadPresets() {
      try {
        const presets = await listConfigPresets();
        setAvailablePresets(presets);
      } catch {
        setAvailablePresets([]);
      }
    }

    void loadPresets();
  }, []);

  function resetUploads() {
    setSelectedFiles([]);
    if (filesInputRef.current) {
      filesInputRef.current.value = "";
    }
    if (folderInputRef.current) {
      folderInputRef.current.value = "";
    }
    setFieldErrors((current) => ({ ...current, upload: undefined }));
  }

  function switchSourceMode(nextMode: SourceMode) {
    setSourceMode(nextMode);
    setError(null);
    setSubmitFeedback("");
    setFieldErrors((current) => ({ ...current, path: undefined, upload: undefined }));
  }

  function addFiles(nextList: FileList | null) {
    if (!nextList || nextList.length === 0) {
      return;
    }
    const next = Array.from(nextList);
    setSelectedFiles((prev) => {
      const known = new Set(prev.map((file) => `${file.name}-${file.size}`));
      const merged = [...prev];
      for (const file of next) {
        const key = `${file.name}-${file.size}`;
        if (!known.has(key)) {
          merged.push(file);
          known.add(key);
        }
      }
      return merged;
    });
    setFieldErrors((current) => ({ ...current, upload: undefined }));
    switchSourceMode("upload");
  }

  function validateForm(): { chunkSize: number } | null {
    const nextErrors: FieldErrors = {};
    const parsedChunkSize = Number(chunkSizeInput);
    if (!Number.isFinite(parsedChunkSize) || parsedChunkSize < 32) {
      nextErrors.chunkSize = "Chunk size must be a numeric value greater than or equal to 32.";
    }

    if (sourceMode === "path" && !inputPath.trim()) {
      nextErrors.path = "Path mode requires a non-empty local input path.";
    }

    if (sourceMode === "upload" && selectedFiles.length === 0) {
      nextErrors.upload = "Upload mode requires at least one selected file.";
    }

    setFieldErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      setSubmitFeedback("Fix validation errors before starting the run.");
      return null;
    }

    return { chunkSize: parsedChunkSize };
  }

  function onDropzoneKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      filesInputRef.current?.click();
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const validated = validateForm();
    if (!validated) {
      return;
    }
    const trimmedPath = inputPath.trim();
    setSubmitFeedback("Starting run...");

    setIsSubmitting(true);
    try {
      let jobId: string;

      if (sourceMode === "upload") {
        const formData = new FormData();
        for (const file of selectedFiles) {
          const relativePath =
            (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
          formData.append("files", file, relativePath);
        }
        formData.append("output_format", outputFormat);
        formData.append("chunk_size", String(validated.chunkSize));
        formData.append("recursive", String(recursive));
        formData.append("incremental", String(incremental));
        formData.append("preset", preset);
        formData.append("semantic", String(semanticEnabled));
        formData.append("semantic_report", String(semanticEnabled && semanticReport));
        formData.append("semantic_report_format", semanticReportFormat);
        formData.append("semantic_export_graph", String(semanticEnabled && semanticExportGraph));
        formData.append("semantic_graph_format", semanticGraphFormat);
        jobId = await createProcessJobWithFiles(formData);
      } else {
        jobId = await createProcessJob({
          input_path: trimmedPath,
          output_format: outputFormat,
          chunk_size: validated.chunkSize,
          recursive,
          incremental,
          preset: preset || undefined,
          include_semantic: semanticEnabled,
          semantic_report: semanticEnabled ? semanticReport : false,
          semantic_report_format: semanticReportFormat,
          semantic_export_graph: semanticEnabled ? semanticExportGraph : false,
          semantic_graph_format: semanticGraphFormat,
          non_interactive: true
        });
      }

      navigate(`/jobs/${jobId}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Job submission failed";
      setError(message);
      setSubmitFeedback(`Submission failed: ${message}`);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <h2>Create A New Processing Run</h2>
      <p className="muted">
        Choose your submission source, then tune advanced settings as needed.
      </p>

      <form onSubmit={onSubmit} className="form-grid" noValidate data-testid="new-run-form">
        <fieldset className="field-group">
          <legend>Input Source</legend>
          <p className="help-text" id="source-mode-help">
            Both sections remain visible below. Only the selected source is submitted.
          </p>
          <div className="source-toggle" role="radiogroup" aria-describedby="source-mode-help">
            <label className={`source-choice ${sourceMode === "path" ? "is-selected" : ""}`}>
              <input
                type="radio"
                name="source-mode"
                value="path"
                checked={sourceMode === "path"}
                onChange={() => switchSourceMode("path")}
                data-testid="new-run-source-path"
              />
              <span>Local Path</span>
            </label>
            <label className={`source-choice ${sourceMode === "upload" ? "is-selected" : ""}`}>
              <input
                type="radio"
                name="source-mode"
                value="upload"
                checked={sourceMode === "upload"}
                onChange={() => switchSourceMode("upload")}
                data-testid="new-run-source-upload"
              />
              <span>Upload Files/Folder</span>
            </label>
          </div>
        </fieldset>

        <section
          className={`source-panel ${sourceMode === "path" ? "is-active" : "is-inactive"}`}
          data-testid="new-run-source-panel-path"
          aria-label="Local path source"
        >
          <div className="row-between">
            <h3>Local Path</h3>
            <span className={`status-chip ${sourceMode === "path" ? "active" : "inactive"}`}>
              {sourceMode === "path" ? "Selected Source" : "Not Selected"}
            </span>
          </div>
          <label htmlFor="new-run-input-path">
            <span>Input Path</span>
          </label>
          <input
            id="new-run-input-path"
            data-testid="new-run-input-path"
            value={inputPath}
            onChange={(event) => {
              setInputPath(event.target.value);
              setFieldErrors((current) => ({ ...current, path: undefined }));
            }}
            placeholder="/path/to/documents"
            aria-describedby="new-run-input-path-help new-run-input-path-error"
            aria-invalid={Boolean(fieldErrors.path)}
            required={sourceMode === "path"}
          />
          <p className="help-text" id="new-run-input-path-help">
            Required when Local Path is selected. The value is trimmed before submit.
          </p>
          {fieldErrors.path ? (
            <p className="field-error" id="new-run-input-path-error" role="alert">
              {fieldErrors.path}
            </p>
          ) : null}
        </section>

        <div
          className={`source-panel ${sourceMode === "upload" ? "is-active" : "is-inactive"}`}
          data-testid="new-run-source-panel-upload"
          aria-label="Upload source"
        >
          <div className="row-between">
            <h3>Upload Files/Folder</h3>
            <span className={`status-chip ${sourceMode === "upload" ? "active" : "inactive"}`}>
              {sourceMode === "upload" ? "Selected Source" : "Not Selected"}
            </span>
          </div>
          <p className="help-text" id="new-run-upload-help">
            Required when Upload Files/Folder is selected. You can drop files or use file picker
            controls.
          </p>
          <div
            className="dropzone"
            role="button"
            tabIndex={0}
            data-testid="new-run-upload-dropzone"
            aria-label="Upload dropzone"
            aria-describedby="new-run-upload-help new-run-upload-error"
            aria-invalid={Boolean(fieldErrors.upload)}
            onKeyDown={onDropzoneKeyDown}
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                filesInputRef.current?.click();
              }
            }}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              addFiles(event.dataTransfer.files);
            }}
          >
            <p>Drop files here</p>
            <small>Press Enter/Space to choose files</small>
            <div className="actions-inline">
              <button
                type="button"
                className="button-like"
                onClick={() => filesInputRef.current?.click()}
                data-testid="new-run-upload-choose-files"
              >
                Choose Files
              </button>
              <button
                type="button"
                className="button-like secondary"
                onClick={() => folderInputRef.current?.click()}
                data-testid="new-run-upload-choose-folder"
              >
                Choose Folder
              </button>
            </div>
            <input
              ref={filesInputRef}
              type="file"
              multiple
              hidden
              onChange={(event) => addFiles(event.target.files)}
            />
            <input
              ref={folderInputRef}
              type="file"
              hidden
              // @ts-expect-error webkitdirectory is non-standard but widely supported.
              webkitdirectory=""
              onChange={(event) => addFiles(event.target.files)}
            />
          </div>
          {fieldErrors.upload ? (
            <p className="field-error" id="new-run-upload-error" role="alert">
              {fieldErrors.upload}
            </p>
          ) : null}

          {fileNames.length > 0 ? (
            <div className="file-list" data-testid="new-run-upload-file-list">
              <strong data-testid="new-run-upload-file-count">{fileNames.length} file(s) ready</strong>
              <small>{formatBytes(totalUploadBytes)} total</small>
              <ul>
                {selectedFiles.slice(0, 8).map((file, index) => (
                  <li key={`${file.name}-${file.size}`}>
                    <span>{file.name}</span>
                    <button
                      type="button"
                      className="link"
                      onClick={() => {
                        setSelectedFiles((prev) =>
                          prev.filter(
                            (candidate) =>
                              !(candidate.name === file.name && candidate.size === file.size)
                          )
                        );
                        setFieldErrors((current) => ({ ...current, upload: undefined }));
                      }}
                      data-testid={`new-run-upload-remove-${index}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
              {fileNames.length > 8 ? <small>and {fileNames.length - 8} more</small> : null}
              <button
                type="button"
                className="link"
                onClick={resetUploads}
                data-testid="new-run-upload-clear"
              >
                Clear uploads
              </button>
            </div>
          ) : null}
        </div>

        <fieldset className="field-group">
          <legend>Advanced Settings</legend>
          <label htmlFor="new-run-output-format">
            <span>Output Format</span>
          </label>
          <select
            id="new-run-output-format"
            value={outputFormat}
            onChange={(event) => setOutputFormat(event.target.value)}
            aria-describedby="new-run-output-format-help"
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="txt">TXT</option>
          </select>
          <p className="help-text" id="new-run-output-format-help">
            Default is JSON.
          </p>

          <label htmlFor="new-run-preset">
            <span>Preset</span>
          </label>
          <select
            id="new-run-preset"
            value={preset}
            onChange={(event) => setPreset(event.target.value)}
            aria-describedby="new-run-preset-help"
            data-testid="new-run-preset"
          >
            <option value="">No preset</option>
            {availablePresets.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
                {item.is_builtin ? " (builtin)" : ""}
              </option>
            ))}
          </select>
          <p className="help-text" id="new-run-preset-help">
            Optional. Preset settings are merged with request overrides.
          </p>

          <label htmlFor="new-run-chunk-size">
            <span>Chunk Size</span>
          </label>
          <input
            id="new-run-chunk-size"
            data-testid="new-run-chunk-size"
            type="number"
            min={32}
            inputMode="numeric"
            value={chunkSizeInput}
            onChange={(event) => {
              setChunkSizeInput(event.target.value);
              setFieldErrors((current) => ({ ...current, chunkSize: undefined }));
            }}
            aria-describedby="new-run-chunk-size-help new-run-chunk-size-error"
            aria-invalid={Boolean(fieldErrors.chunkSize)}
          />
          <p className="help-text" id="new-run-chunk-size-help">
            Must be numeric and at least 32. Default is 512.
          </p>
          {fieldErrors.chunkSize ? (
            <p className="field-error" id="new-run-chunk-size-error" role="alert">
              {fieldErrors.chunkSize}
            </p>
          ) : null}

          <div className="check-row">
            <input
              id="new-run-recursive"
              type="checkbox"
              checked={recursive}
              onChange={(event) => setRecursive(event.target.checked)}
            />
            <label htmlFor="new-run-recursive">
              <span>Recursive file discovery</span>
            </label>
          </div>

          <div className="check-row">
            <input
              id="new-run-incremental"
              type="checkbox"
              checked={incremental}
              onChange={(event) => setIncremental(event.target.checked)}
            />
            <label htmlFor="new-run-incremental">
              <span>Incremental mode (new/changed only)</span>
            </label>
          </div>

          <div className="check-row">
            <input
              id="new-run-semantic"
              type="checkbox"
              checked={semanticEnabled}
              onChange={(event) => setSemanticEnabled(event.target.checked)}
              data-testid="new-run-semantic"
            />
            <label htmlFor="new-run-semantic">
              <span>Enable semantic analysis</span>
            </label>
          </div>

          <div className="check-row">
            <input
              id="new-run-semantic-report"
              type="checkbox"
              checked={semanticReport}
              disabled={!semanticEnabled}
              onChange={(event) => setSemanticReport(event.target.checked)}
            />
            <label htmlFor="new-run-semantic-report">
              <span>Generate semantic report artifact</span>
            </label>
          </div>

          <div className="check-row">
            <input
              id="new-run-semantic-graph"
              type="checkbox"
              checked={semanticExportGraph}
              disabled={!semanticEnabled}
              onChange={(event) => setSemanticExportGraph(event.target.checked)}
            />
            <label htmlFor="new-run-semantic-graph">
              <span>Export semantic graph artifact</span>
            </label>
          </div>

          <label htmlFor="new-run-semantic-report-format">
            <span>Semantic Report Format</span>
          </label>
          <select
            id="new-run-semantic-report-format"
            value={semanticReportFormat}
            onChange={(event) => setSemanticReportFormat(event.target.value)}
            disabled={!semanticEnabled}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="html">HTML</option>
          </select>

          <label htmlFor="new-run-semantic-graph-format">
            <span>Semantic Graph Format</span>
          </label>
          <select
            id="new-run-semantic-graph-format"
            value={semanticGraphFormat}
            onChange={(event) => setSemanticGraphFormat(event.target.value)}
            disabled={!semanticEnabled}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="dot">DOT</option>
          </select>
        </fieldset>

        <article className="summary-card" data-testid="new-run-summary-card">
          <h3>Submission Summary</h3>
          <dl className="key-value-list">
            <dt>Source Mode</dt>
            <dd>{sourceMode === "path" ? "Local Path" : "Upload Files/Folder"}</dd>
            <dt>Source Value</dt>
            <dd>
              {sourceMode === "path"
                ? inputPath.trim() || "Not set"
                : `${selectedFiles.length} file(s), ${formatBytes(totalUploadBytes)}`}
            </dd>
            <dt>Output Format</dt>
            <dd>{outputFormat.toUpperCase()}</dd>
            <dt>Chunk Size</dt>
            <dd>{chunkSizeInput || "Not set"}</dd>
            <dt>Preset</dt>
            <dd>{preset || "None"}</dd>
            <dt>Discovery</dt>
            <dd>{recursive ? "Recursive" : "Top-level only"}</dd>
            <dt>Incremental</dt>
            <dd>{incremental ? "Enabled" : "Disabled"}</dd>
            <dt>Semantic</dt>
            <dd>{semanticEnabled ? "Enabled" : "Disabled"}</dd>
            <dt>Semantic Report</dt>
            <dd>{semanticEnabled && semanticReport ? semanticReportFormat.toUpperCase() : "Off"}</dd>
            <dt>Semantic Graph</dt>
            <dd>{semanticEnabled && semanticExportGraph ? semanticGraphFormat.toUpperCase() : "Off"}</dd>
          </dl>
        </article>

        <p className="help-text submit-feedback" aria-live="polite" data-testid="new-run-submit-feedback">
          {isSubmitting ? "Submitting job..." : submitFeedback}
        </p>

        {error ? (
          <p className="error" role="alert" aria-live="assertive">
            {error}
          </p>
        ) : null}

        <button className="primary" type="submit" disabled={isSubmitting} data-testid="new-run-submit">
          {isSubmitting ? "Starting..." : "Start Run"}
        </button>
      </form>
    </section>
  );
}
