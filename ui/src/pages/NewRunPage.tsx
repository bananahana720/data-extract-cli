import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  FormLabel,
  InputLabel,
  NativeSelect,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import {
  createProcessJob,
  createProcessJobWithFiles,
  getCurrentPreset,
  listConfigPresets
} from "../api/client";
import { GuidanceTip, SectionCard, StatusPill } from "../components/foundation";
import { GuidedRunBuilderShell, VerifyBeforeRunSummaryCard } from "../components/run-builder";
import { type RunSummaryEntry } from "../components/run-builder";
import { ConfigPresetSummary } from "../types";

type SourceMode = "path" | "upload";
type FieldErrors = {
  path?: string;
  upload?: string;
  chunkSize?: string;
  semantic?: string;
};

type IndustryContextKey = "governance" | "cybersecurity" | "financial_services";

type IndustryContextGuide = {
  id: IndustryContextKey;
  title: string;
  description: string;
  learningPrompt: string;
  checklist: string[];
  recommendedChunkSize: number;
  recommendedPreset: string;
};

type ValidationSnapshot = {
  chunkSize: number | null;
  errors: FieldErrors;
  blockingIssues: string[];
};

const INDUSTRY_CONTEXT_GUIDES: IndustryContextGuide[] = [
  {
    id: "governance",
    title: "Governance, Risk & Controls",
    description:
      "Prepare policy, control, and risk artifacts so entities become consistently structured.",
    learningPrompt:
      "Task: Normalize context into policy objects with owners, controls, risks, and review cadence.\n\nOutput columns: domain_area, control_id, control_statement, control_owner, risk_tier, implementation_status, evidence_ref, due_date.\n\nRules: retain original policy language when important; normalize synonyms (e.g., SOX/PCI/ISO/NIST references) into canonical tags.",
    checklist: [
      "Identify every policy ID, control ID, and ownership field",
      "Split dense legal prose into requirements + test criteria",
      "Standardize date and schedule fields (due_date, review_date, refresh_date)",
      "Map confidence levels to a small fixed scale (High / Medium / Low)"
    ],
    recommendedChunkSize: 500,
    recommendedPreset: "quality"
  },
  {
    id: "cybersecurity",
    title: "Cybersecurity",
    description:
      "Keep attack-paths, assets, and controls machine-readable for security playbooks and evidence collection.",
    learningPrompt:
      "Task: Normalize security context into controls and threat-mitigation units.\n\nOutput columns: asset, threat_scenario, control, control_type, owner_team, priority, residual_risk, monitoring_signal, evidence_reference.\n\nRules: preserve framework mapping (NIST, MITRE, CIS), keep mitigation and detection references separate from prevention controls.",
    checklist: [
      "Extract explicit asset ownership and environment context first",
      "Normalize framework references to canonical labels (NIST CSF, CIS, MITRE, ISO)",
      "Separate preventive, detective, and recovery controls",
      "Add explicit monitoring signal fields for each control"
    ],
    recommendedChunkSize: 450,
    recommendedPreset: "balanced"
  },
  {
    id: "financial_services",
    title: "Financial Services",
    description:
      "Prioritize entity linkage: customer, account, product, and compliance checkpoints with auditability.",
    learningPrompt:
      "Task: Structure finance context for downstream QA and model-grounded workflows.\n\nOutput columns: policy_name, control_family, data_domain, account_type, customer_impact, required_evidence, reviewer, approval_state, exception_reason.\n\nRules: keep transaction-related constraints explicit, normalize GL/GLBA/FFIEC naming variants, and add exception_reason whenever control is bypassed.",
    checklist: [
      "Normalize account/product terminology and map to canonical business terms",
      "Extract decision points, approvals, and exception workflow explicitly",
      "Normalize time windows (T+0, T+1, month/quarter end)",
      "Link each control to evidence and responsible role"
    ],
    recommendedChunkSize: 550,
    recommendedPreset: "quality"
  }
];

function getIndustryContext(id: IndustryContextKey): IndustryContextGuide {
  return INDUSTRY_CONTEXT_GUIDES.find((context) => context.id === id) ?? INDUSTRY_CONTEXT_GUIDES[0];
}

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

function getRelativePath(file: File): string {
  return (file as File & { webkitRelativePath?: string }).webkitRelativePath || "";
}

function getFileSignature(file: File): string {
  const relativePath = getRelativePath(file);
  return `${relativePath}:${file.name}:${file.size}:${file.lastModified}:${file.type}`;
}

function buildValidationSnapshot(params: {
  sourceMode: SourceMode;
  inputPath: string;
  chunkSizeInput: string;
  selectedFiles: File[];
  semanticEnabled: boolean;
  outputFormat: string;
}): ValidationSnapshot {
  const { sourceMode, inputPath, chunkSizeInput, selectedFiles, semanticEnabled, outputFormat } = params;
  const errors: FieldErrors = {};
  const blockingIssues: string[] = [];

  const parsedChunkSize = Number(chunkSizeInput);
  const hasValidChunkSize = Number.isFinite(parsedChunkSize) && parsedChunkSize >= 32;

  if (!hasValidChunkSize) {
    errors.chunkSize = "Chunk size must be a numeric value greater than or equal to 32.";
    blockingIssues.push("Chunk Size must be numeric and at least 32.");
  }

  if (sourceMode === "path" && !inputPath.trim()) {
    errors.path = "Path mode requires a non-empty local input path.";
    blockingIssues.push("Local Path is selected but Input Path is empty.");
  }

  if (sourceMode === "upload" && selectedFiles.length === 0) {
    errors.upload = "Upload mode requires at least one selected file.";
    blockingIssues.push("Upload Files/Folder is selected but no files are attached.");
  }

  if (semanticEnabled && outputFormat !== "json") {
    errors.semantic = "Semantic analysis requires JSON output format.";
    blockingIssues.push("Semantic analysis can only run when Output Format is JSON.");
  }

  return {
    chunkSize: hasValidChunkSize ? parsedChunkSize : null,
    errors,
    blockingIssues
  };
}

function getContextReadinessStatus(progressPercent: number): "success" | "info" | "warning" {
  if (progressPercent >= 100) {
    return "success";
  }
  if (progressPercent >= 50) {
    return "info";
  }
  return "warning";
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
  const [industryContext, setIndustryContext] = useState<IndustryContextKey>("governance");
  const [availablePresets, setAvailablePresets] = useState<ConfigPresetSummary[]>([]);
  const [presetLoadWarning, setPresetLoadWarning] = useState<string | null>(null);
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
  const [contextChecklistChecks, setContextChecklistChecks] = useState<Record<string, boolean>>({});

  const [verifyAcknowledged, setVerifyAcknowledged] = useState(false);
  const [verifiedSnapshotKey, setVerifiedSnapshotKey] = useState<string | null>(null);
  const [staleAcknowledgementMessage, setStaleAcknowledgementMessage] = useState("");

  const selectedIndustryContext = useMemo(
    () => getIndustryContext(industryContext),
    [industryContext]
  );

  const contextChecklistProgress = useMemo(() => {
    const total = selectedIndustryContext.checklist.length;
    const done = selectedIndustryContext.checklist.reduce((count, _, index) => {
      const key = `${industryContext}:${index}`;
      return contextChecklistChecks[key] ? count + 1 : count;
    }, 0);

    return {
      done,
      total,
      percent: total === 0 ? 0 : Math.round((done / total) * 100)
    };
  }, [selectedIndustryContext.checklist, industryContext, contextChecklistChecks]);

  const fileNames = useMemo(() => selectedFiles.map((file) => file.name), [selectedFiles]);
  const totalUploadBytes = useMemo(
    () => selectedFiles.reduce((total, file) => total + file.size, 0),
    [selectedFiles]
  );

  const validationSnapshot = useMemo(
    () =>
      buildValidationSnapshot({
        sourceMode,
        inputPath,
        chunkSizeInput,
        selectedFiles,
        semanticEnabled,
        outputFormat
      }),
    [sourceMode, inputPath, chunkSizeInput, selectedFiles, semanticEnabled, outputFormat]
  );

  const verificationSnapshotKey = useMemo(
    () =>
      JSON.stringify({
        sourceMode,
        inputPath: inputPath.trim(),
        selectedFiles: selectedFiles.map(getFileSignature).sort(),
        chunkSizeInput,
        outputFormat,
        preset,
        recursive,
        incremental,
        semanticEnabled,
        semanticReport: semanticEnabled ? semanticReport : false,
        semanticExportGraph: semanticEnabled ? semanticExportGraph : false,
        semanticReportFormat,
        semanticGraphFormat,
        industryContext,
        contextChecklistDone: contextChecklistProgress.done,
        contextChecklistTotal: contextChecklistProgress.total
      }),
    [
      sourceMode,
      inputPath,
      selectedFiles,
      chunkSizeInput,
      outputFormat,
      preset,
      recursive,
      incremental,
      semanticEnabled,
      semanticReport,
      semanticExportGraph,
      semanticReportFormat,
      semanticGraphFormat,
      industryContext,
      contextChecklistProgress.done,
      contextChecklistProgress.total
    ]
  );

  const summaryEntries = useMemo<RunSummaryEntry[]>(
    () => [
      {
        label: "Source Mode",
        value: sourceMode === "path" ? "Local Path" : "Upload Files/Folder"
      },
      {
        label: "Source Value",
        value:
          sourceMode === "path"
            ? inputPath.trim() || "Not set"
            : `${selectedFiles.length} file(s), ${formatBytes(totalUploadBytes)}`
      },
      {
        label: "Industry Context",
        value: selectedIndustryContext.title
      },
      {
        label: "Context Prep",
        value: `${contextChecklistProgress.done}/${contextChecklistProgress.total} checks complete (${contextChecklistProgress.percent}%)`
      },
      {
        label: "Output Format",
        value: outputFormat.toUpperCase()
      },
      {
        label: "Chunk Size",
        value: chunkSizeInput || "Not set"
      },
      {
        label: "Preset",
        value: preset || "None"
      },
      {
        label: "Discovery",
        value: recursive ? "Recursive" : "Top-level only"
      },
      {
        label: "Incremental",
        value: incremental ? "Enabled" : "Disabled"
      },
      {
        label: "Semantic",
        value: semanticEnabled ? "Enabled" : "Disabled"
      },
      {
        label: "Semantic Report",
        value: semanticEnabled && semanticReport ? semanticReportFormat.toUpperCase() : "Off"
      },
      {
        label: "Semantic Graph",
        value: semanticEnabled && semanticExportGraph ? semanticGraphFormat.toUpperCase() : "Off"
      }
    ],
    [
      sourceMode,
      inputPath,
      selectedFiles.length,
      totalUploadBytes,
      selectedIndustryContext.title,
      contextChecklistProgress.done,
      contextChecklistProgress.total,
      contextChecklistProgress.percent,
      outputFormat,
      chunkSizeInput,
      preset,
      recursive,
      incremental,
      semanticEnabled,
      semanticReport,
      semanticReportFormat,
      semanticExportGraph,
      semanticGraphFormat
    ]
  );

  const hasBlockingIssues = validationSnapshot.blockingIssues.length > 0;
  const isSubmitDisabled = isSubmitting || hasBlockingIssues || !verifyAcknowledged;

  const gateReason = hasBlockingIssues
    ? "Resolve all blocking reasons in Verify Before Run to enable Start Run."
    : !verifyAcknowledged
      ? "Check the verification acknowledgement to enable Start Run."
      : "Ready to start the run.";

  const submitStatusMessage = isSubmitting
    ? "Submitting job..."
    : submitFeedback || gateReason;

  useEffect(() => {
    async function loadPresets() {
      try {
        const [presets, currentPreset] = await Promise.all([listConfigPresets(), getCurrentPreset()]);
        setAvailablePresets(presets);
        setPresetLoadWarning(null);
        if (currentPreset && presets.some((item) => item.name === currentPreset)) {
          setPreset((current) => current || currentPreset);
        }
      } catch {
        setAvailablePresets([]);
        setPresetLoadWarning(
          "Could not load presets right now. Continue with No preset or refresh the page to try again."
        );
      }
    }

    void loadPresets();
  }, []);

  useEffect(() => {
    if (verifyAcknowledged && verifiedSnapshotKey && verifiedSnapshotKey !== verificationSnapshotKey) {
      setVerifyAcknowledged(false);
      setVerifiedSnapshotKey(null);
      setStaleAcknowledgementMessage(
        "Verification reset because run inputs changed. Review updates and acknowledge again."
      );
    }
  }, [verifyAcknowledged, verifiedSnapshotKey, verificationSnapshotKey]);

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

  function applyIndustryDefaults() {
    setOutputFormat("json");
    setChunkSizeInput(String(selectedIndustryContext.recommendedChunkSize));
    setPreset(selectedIndustryContext.recommendedPreset);
    setSemanticEnabled(false);
    setSemanticReport(false);
    setSemanticExportGraph(false);
    setFieldErrors((current) => ({ ...current, semantic: undefined }));
    setSubmitFeedback(`Applied ${selectedIndustryContext.title} guidance defaults.`);
  }

  function toggleContextChecklist(index: number) {
    const key = `${industryContext}:${index}`;
    setContextChecklistChecks((current) => ({
      ...current,
      [key]: !current[key]
    }));
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
      const known = new Set(prev.map(getFileSignature));
      const merged = [...prev];
      for (const file of next) {
        const key = getFileSignature(file);
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

  function handleVerifyAcknowledgementChange(checked: boolean) {
    setVerifyAcknowledged(checked);
    setStaleAcknowledgementMessage("");
    setVerifiedSnapshotKey(checked ? verificationSnapshotKey : null);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    setFieldErrors(validationSnapshot.errors);

    if (validationSnapshot.blockingIssues.length > 0 || validationSnapshot.chunkSize == null) {
      setSubmitFeedback("Fix validation errors before starting the run.");
      return;
    }

    if (!verifyAcknowledged) {
      setSubmitFeedback("Review and acknowledge Verify Before Run before starting.");
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
          const relativePath = getRelativePath(file) || file.name;
          formData.append("files", file, relativePath);
        }
        formData.append("output_format", outputFormat);
        formData.append("chunk_size", String(validationSnapshot.chunkSize));
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
          chunk_size: validationSnapshot.chunkSize,
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
    <GuidedRunBuilderShell
      eyebrow="Guided Run Builder"
      title="Create A New Processing Run"
      subtitle="Choose your submission source, then tune advanced settings and verify before launch."
      contextPanel={
        <SectionCard
          title="Context Cleansing Guidance"
          subtitle="Choose your domain and use the checklist to structure raw context before extraction."
        >
          <Stack spacing={2}>
            <GuidanceTip
              title="Context Prep"
              what="Pick the closest domain profile before configuring extraction settings."
              why="Context alignment improves consistency of extracted entities and controls."
              how="Select a domain card, complete checklist items, and optionally apply recommended defaults."
            />

            <Box
              sx={{
                display: "grid",
                gap: 1.5,
                gridTemplateColumns: {
                  xs: "minmax(0, 1fr)",
                  md: "repeat(3, minmax(0, 1fr))"
                }
              }}
            >
              {INDUSTRY_CONTEXT_GUIDES.map((context) => {
                const isActive = industryContext === context.id;
                return (
                  <Button
                    type="button"
                    key={context.id}
                    variant={isActive ? "contained" : "outlined"}
                    onClick={() => {
                      setIndustryContext(context.id);
                      setSubmitFeedback("");
                    }}
                    sx={{
                      borderRadius: 2,
                      p: 1.75,
                      textAlign: "left",
                      textTransform: "none",
                      justifyContent: "flex-start"
                    }}
                  >
                    <Stack alignItems="flex-start" spacing={0.75}>
                      <Typography variant="subtitle2">{context.title}</Typography>
                      <Typography variant="body2" color={isActive ? "primary.contrastText" : "text.secondary"}>
                        {context.description}
                      </Typography>
                      <Typography variant="caption" color={isActive ? "primary.contrastText" : "text.secondary"}>
                        Recommended chunk size: <strong>{context.recommendedChunkSize}</strong> • Preset:{" "}
                        <strong>{context.recommendedPreset}</strong>
                      </Typography>
                    </Stack>
                  </Button>
                );
              })}
            </Box>

            <Box
              role="status"
              aria-live="polite"
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 1,
                flexWrap: "wrap"
              }}
            >
              <Typography variant="body2">
                Context Readiness: {contextChecklistProgress.done}/{contextChecklistProgress.total} checks complete
              </Typography>
              <StatusPill
                status={getContextReadinessStatus(contextChecklistProgress.percent)}
                label={`${contextChecklistProgress.percent}% Ready`}
              />
            </Box>

            <Divider />

            <Stack spacing={0.75}>
              {selectedIndustryContext.checklist.map((item, index) => {
                const key = `${industryContext}:${index}`;
                return (
                  <FormControlLabel
                    key={key}
                    control={
                      <Checkbox
                        checked={Boolean(contextChecklistChecks[key])}
                        onChange={() => toggleContextChecklist(index)}
                      />
                    }
                    label={item}
                  />
                );
              })}
            </Stack>

            <Box
              sx={{
                backgroundColor: "background.default",
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
                p: 2
              }}
            >
              <Typography component="h3" variant="subtitle1" sx={{ mb: 1 }}>
                Learning Prompt Template
              </Typography>
              <Typography
                component="pre"
                sx={{
                  m: 0,
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                  fontSize: "0.82rem",
                  lineHeight: 1.5
                }}
              >
                {selectedIndustryContext.learningPrompt}
              </Typography>
            </Box>

            <Box>
              <Button type="button" variant="outlined" onClick={applyIndustryDefaults}>
                Apply Recommended Defaults
              </Button>
            </Box>
          </Stack>
        </SectionCard>
      }
      builderPanel={
        <Box component="form" id="new-run-form" onSubmit={onSubmit} noValidate data-testid="new-run-form">
          <Stack spacing={2.5}>
            <SectionCard title="Input Source" subtitle="Only the selected source is submitted.">
              <FormControl component="fieldset">
                <FormLabel id="source-mode-help">Choose source mode</FormLabel>
                <RadioGroup
                  row
                  aria-describedby="source-mode-help"
                  value={sourceMode}
                  onChange={(event) => switchSourceMode(event.target.value as SourceMode)}
                >
                  <FormControlLabel
                    value="path"
                    control={
                      <Radio inputProps={{ "data-testid": "new-run-source-path" } as Record<string, string>} />
                    }
                    label="Local Path"
                  />
                  <FormControlLabel
                    value="upload"
                    control={
                      <Radio inputProps={{ "data-testid": "new-run-source-upload" } as Record<string, string>} />
                    }
                    label="Upload Files/Folder"
                  />
                </RadioGroup>
              </FormControl>
            </SectionCard>

            <SectionCard
              title="Local Path"
              data-testid="new-run-source-panel-path"
              action={
                <StatusPill
                  status={sourceMode === "path" ? "success" : "neutral"}
                  label={sourceMode === "path" ? "Selected Source" : "Not Selected"}
                />
              }
              sx={{ opacity: sourceMode === "path" ? 1 : 0.8 }}
            >
              <Stack spacing={1}>
                <TextField
                  id="new-run-input-path"
                  label="Input Path"
                  placeholder="/path/to/documents"
                  value={inputPath}
                  onChange={(event) => {
                    setInputPath(event.target.value);
                    setFieldErrors((current) => ({ ...current, path: undefined }));
                  }}
                  inputProps={{ "data-testid": "new-run-input-path" }}
                  required={sourceMode === "path"}
                  error={Boolean(fieldErrors.path)}
                  aria-describedby="new-run-input-path-help new-run-input-path-error"
                />
                <FormHelperText id="new-run-input-path-help">
                  Required when Local Path is selected. The value is trimmed before submit.
                </FormHelperText>
                {fieldErrors.path ? (
                  <FormHelperText error id="new-run-input-path-error" role="alert">
                    {fieldErrors.path}
                  </FormHelperText>
                ) : null}
              </Stack>
            </SectionCard>

            <SectionCard
              title="Upload Files/Folder"
              data-testid="new-run-source-panel-upload"
              action={
                <StatusPill
                  status={sourceMode === "upload" ? "success" : "neutral"}
                  label={sourceMode === "upload" ? "Selected Source" : "Not Selected"}
                />
              }
              sx={{ opacity: sourceMode === "upload" ? 1 : 0.8 }}
            >
              <Stack spacing={1.25}>
                <Typography variant="body2" id="new-run-upload-help" color="text.secondary">
                  Required when Upload Files/Folder is selected. You can drop files or use file picker controls.
                </Typography>
                <Box
                  role="group"
                  data-testid="new-run-upload-dropzone"
                  aria-label="Upload dropzone"
                  aria-describedby="new-run-upload-help new-run-upload-error"
                  aria-invalid={Boolean(fieldErrors.upload)}
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
                  sx={{
                    border: 1,
                    borderStyle: "dashed",
                    borderColor: fieldErrors.upload ? "error.main" : "divider",
                    borderRadius: 2,
                    p: 2,
                    display: "grid",
                    gap: 1,
                    cursor: "pointer"
                  }}
                >
                  <Typography variant="body1">Drop files here</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Drag files into this area, or use the chooser buttons.
                  </Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                    <Button
                      type="button"
                      variant="contained"
                      onClick={() => filesInputRef.current?.click()}
                      data-testid="new-run-upload-choose-files"
                    >
                      Choose Files
                    </Button>
                    <Button
                      type="button"
                      variant="outlined"
                      onClick={() => folderInputRef.current?.click()}
                      data-testid="new-run-upload-choose-folder"
                    >
                      Choose Folder
                    </Button>
                  </Stack>
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
                </Box>

                {fieldErrors.upload ? (
                  <FormHelperText error id="new-run-upload-error" role="alert">
                    {fieldErrors.upload}
                  </FormHelperText>
                ) : null}

                {fileNames.length > 0 ? (
                  <Box
                    data-testid="new-run-upload-file-list"
                    sx={{
                      border: 1,
                      borderColor: "divider",
                      borderRadius: 2,
                      p: 1.5,
                      display: "grid",
                      gap: 1
                    }}
                  >
                    <Typography variant="subtitle2" data-testid="new-run-upload-file-count">
                      {fileNames.length} file(s) ready
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatBytes(totalUploadBytes)} total
                    </Typography>
                    <Box component="ul" sx={{ m: 0, pl: 2, display: "grid", gap: 0.5 }}>
                      {selectedFiles.slice(0, 8).map((file, index) => (
                        <Box
                          component="li"
                          key={getFileSignature(file)}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: 1
                          }}
                        >
                          <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
                            {getRelativePath(file) || file.name}
                          </Typography>
                          <Button
                            type="button"
                            size="small"
                            onClick={() => {
                              const fileSignature = getFileSignature(file);
                              setSelectedFiles((prev) =>
                                prev.filter((candidate) => getFileSignature(candidate) !== fileSignature)
                              );
                              setFieldErrors((current) => ({ ...current, upload: undefined }));
                            }}
                            data-testid={`new-run-upload-remove-${index}`}
                          >
                            Remove
                          </Button>
                        </Box>
                      ))}
                    </Box>
                    {fileNames.length > 8 ? (
                      <Typography variant="caption" color="text.secondary">
                        and {fileNames.length - 8} more
                      </Typography>
                    ) : null}
                    <Box>
                      <Button
                        type="button"
                        size="small"
                        onClick={resetUploads}
                        data-testid="new-run-upload-clear"
                      >
                        Clear uploads
                      </Button>
                    </Box>
                  </Box>
                ) : null}
              </Stack>
            </SectionCard>

            <SectionCard title="Advanced Settings" subtitle="Tune extraction behavior and semantic artifacts.">
              <Stack spacing={1.5}>
                {presetLoadWarning ? (
                  <Alert severity="warning" role="status">
                    {presetLoadWarning}
                  </Alert>
                ) : null}

                <Box
                  sx={{
                    display: "grid",
                    gap: 2,
                    gridTemplateColumns: {
                      xs: "minmax(0, 1fr)",
                      md: "repeat(2, minmax(0, 1fr))"
                    }
                  }}
                >
                <FormControl variant="standard" fullWidth>
                  <InputLabel htmlFor="new-run-output-format">Output Format</InputLabel>
                  <NativeSelect
                    id="new-run-output-format"
                    value={outputFormat}
                    onChange={(event) => {
                      setOutputFormat(event.target.value);
                      setSubmitFeedback("");
                    }}
                    inputProps={{ "aria-describedby": "new-run-output-format-help" }}
                  >
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="txt">TXT</option>
                  </NativeSelect>
                  <FormHelperText id="new-run-output-format-help">Default is JSON.</FormHelperText>
                </FormControl>

                <FormControl variant="standard" fullWidth>
                  <InputLabel htmlFor="new-run-preset">Preset</InputLabel>
                  <NativeSelect
                    id="new-run-preset"
                    value={preset}
                    onChange={(event) => setPreset(event.target.value)}
                    inputProps={
                      {
                        "aria-describedby": "new-run-preset-help",
                        "data-testid": "new-run-preset"
                      } as Record<string, string>
                    }
                  >
                    <option value="">No preset</option>
                    {availablePresets.map((item) => (
                      <option key={item.name} value={item.name}>
                        {item.name}
                        {item.is_builtin ? " (builtin)" : ""}
                      </option>
                    ))}
                  </NativeSelect>
                  <FormHelperText id="new-run-preset-help">
                    Optional. Preset settings are merged with request overrides.
                  </FormHelperText>
                </FormControl>

                <TextField
                  id="new-run-chunk-size"
                  label="Chunk Size"
                  type="number"
                  inputMode="numeric"
                  inputProps={{ min: 32, "data-testid": "new-run-chunk-size" }}
                  value={chunkSizeInput}
                  onChange={(event) => {
                    setChunkSizeInput(event.target.value);
                    setFieldErrors((current) => ({ ...current, chunkSize: undefined }));
                  }}
                  error={Boolean(fieldErrors.chunkSize)}
                  aria-describedby="new-run-chunk-size-help new-run-chunk-size-error"
                />
                <Box>
                  <FormHelperText id="new-run-chunk-size-help">
                    Must be numeric and at least 32. Default is 512.
                  </FormHelperText>
                  {fieldErrors.chunkSize ? (
                    <FormHelperText error id="new-run-chunk-size-error" role="alert">
                      {fieldErrors.chunkSize}
                    </FormHelperText>
                  ) : null}
                </Box>

                <Stack spacing={0.5}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        id="new-run-recursive"
                        checked={recursive}
                        onChange={(event) => setRecursive(event.target.checked)}
                      />
                    }
                    label="Recursive file discovery"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        id="new-run-incremental"
                        checked={incremental}
                        onChange={(event) => setIncremental(event.target.checked)}
                      />
                    }
                    label="Incremental mode (new/changed only)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        id="new-run-semantic"
                        checked={semanticEnabled}
                        onChange={(event) => {
                          setSemanticEnabled(event.target.checked);
                          setFieldErrors((current) => ({ ...current, semantic: undefined }));
                        }}
                        inputProps={{ "data-testid": "new-run-semantic" } as Record<string, string>}
                      />
                    }
                    label="Enable semantic analysis"
                  />
                  {fieldErrors.semantic ? (
                    <FormHelperText error role="alert">
                      {fieldErrors.semantic}
                    </FormHelperText>
                  ) : null}
                  <FormControlLabel
                    control={
                      <Checkbox
                        id="new-run-semantic-report"
                        checked={semanticReport}
                        disabled={!semanticEnabled}
                        onChange={(event) => setSemanticReport(event.target.checked)}
                      />
                    }
                    label="Generate semantic report artifact"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        id="new-run-semantic-graph"
                        checked={semanticExportGraph}
                        disabled={!semanticEnabled}
                        onChange={(event) => setSemanticExportGraph(event.target.checked)}
                      />
                    }
                    label="Export semantic graph artifact"
                  />
                </Stack>

                <FormControl variant="standard" fullWidth disabled={!semanticEnabled}>
                  <InputLabel htmlFor="new-run-semantic-report-format">Semantic Report Format</InputLabel>
                  <NativeSelect
                    id="new-run-semantic-report-format"
                    value={semanticReportFormat}
                    onChange={(event) => setSemanticReportFormat(event.target.value)}
                  >
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="html">HTML</option>
                  </NativeSelect>
                </FormControl>

                <FormControl variant="standard" fullWidth disabled={!semanticEnabled}>
                  <InputLabel htmlFor="new-run-semantic-graph-format">Semantic Graph Format</InputLabel>
                  <NativeSelect
                    id="new-run-semantic-graph-format"
                    value={semanticGraphFormat}
                    onChange={(event) => setSemanticGraphFormat(event.target.value)}
                  >
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                    <option value="dot">DOT</option>
                  </NativeSelect>
                </FormControl>
                </Box>
              </Stack>
            </SectionCard>
          </Stack>
        </Box>
      }
      verifyPanel={
        <Stack spacing={2}>
          <VerifyBeforeRunSummaryCard
            summaryEntries={summaryEntries}
            blockingIssues={validationSnapshot.blockingIssues}
            acknowledged={verifyAcknowledged}
            staleAcknowledgementMessage={staleAcknowledgementMessage}
            onAcknowledgedChange={handleVerifyAcknowledgementChange}
            acknowledgementDisabled={isSubmitting}
            data-testid="new-run-summary-card"
          />

          <Typography
            variant="body2"
            color={hasBlockingIssues || !verifyAcknowledged ? "warning.main" : "text.secondary"}
            data-testid="new-run-submit-feedback"
            aria-live="polite"
          >
            {submitStatusMessage}
          </Typography>

          {error ? (
            <Alert severity="error" role="alert" aria-live="assertive">
              {error}
            </Alert>
          ) : null}

          <Button
            variant="contained"
            type="submit"
            form="new-run-form"
            disabled={isSubmitDisabled}
            data-testid="new-run-submit"
          >
            {isSubmitting ? "Starting..." : "Start Run"}
          </Button>
        </Stack>
      }
    />
  );
}
