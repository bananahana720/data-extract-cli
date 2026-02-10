import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createProcessJob, createProcessJobWithFiles } from "../api/client";

export function NewRunPage() {
  const navigate = useNavigate();
  const [inputPath, setInputPath] = useState("");
  const [chunkSize, setChunkSize] = useState(512);
  const [outputFormat, setOutputFormat] = useState("json");
  const [recursive, setRecursive] = useState(true);
  const [incremental, setIncremental] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const fileNames = useMemo(() => selectedFiles.map((file) => file.name), [selectedFiles]);

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
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (selectedFiles.length === 0 && !inputPath.trim()) {
      setError("Provide an input path or upload files.");
      return;
    }

    setIsSubmitting(true);
    try {
      let jobId: string;

      if (selectedFiles.length > 0) {
        const formData = new FormData();
        for (const file of selectedFiles) {
          const relativePath =
            (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
          formData.append("files", file, relativePath);
        }
        formData.append("output_format", outputFormat);
        formData.append("chunk_size", String(chunkSize));
        formData.append("recursive", String(recursive));
        formData.append("incremental", String(incremental));
        jobId = await createProcessJobWithFiles(formData);
      } else {
        jobId = await createProcessJob({
          input_path: inputPath,
          output_format: outputFormat,
          chunk_size: chunkSize,
          recursive,
          incremental,
          non_interactive: true
        });
      }

      navigate(`/jobs/${jobId}`);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Job submission failed";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <h2>Create A New Processing Run</h2>
      <p className="muted">
        Drag files for quick intake, or provide a local path for large directory processing.
      </p>

      <form onSubmit={onSubmit} className="form-grid">
        <label>
          <span>Input Path (optional when uploading files)</span>
          <input
            value={inputPath}
            onChange={(event) => setInputPath(event.target.value)}
            placeholder="/path/to/documents"
          />
        </label>

        <div
          className="dropzone"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            addFiles(event.dataTransfer.files);
          }}
        >
          <p>Drop files here</p>
          <small>or select files/folder</small>
          <div className="actions-inline">
            <label className="button-like">
              Choose Files
              <input
                type="file"
                multiple
                hidden
                onChange={(event) => addFiles(event.target.files)}
              />
            </label>
            <label className="button-like secondary">
              Choose Folder
              <input
                type="file"
                // @ts-expect-error webkitdirectory is non-standard but widely supported.
                webkitdirectory=""
                hidden
                onChange={(event) => addFiles(event.target.files)}
              />
            </label>
          </div>
        </div>

        {fileNames.length > 0 ? (
          <div className="file-list">
            <strong>{fileNames.length} file(s) ready</strong>
            <ul>
              {fileNames.slice(0, 8).map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
            {fileNames.length > 8 ? <small>and {fileNames.length - 8} more</small> : null}
            <button type="button" className="link" onClick={() => setSelectedFiles([])}>
              Clear uploads
            </button>
          </div>
        ) : null}

        <details>
          <summary>Advanced Settings</summary>
          <label>
            <span>Output Format</span>
            <select value={outputFormat} onChange={(event) => setOutputFormat(event.target.value)}>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="txt">TXT</option>
            </select>
          </label>

          <label>
            <span>Chunk Size</span>
            <input
              type="number"
              min={32}
              value={chunkSize}
              onChange={(event) => setChunkSize(Number(event.target.value))}
            />
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={recursive}
              onChange={(event) => setRecursive(event.target.checked)}
            />
            <span>Recursive file discovery</span>
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={incremental}
              onChange={(event) => setIncremental(event.target.checked)}
            />
            <span>Incremental mode (new/changed only)</span>
          </label>
        </details>

        {error ? <p className="error">{error}</p> : null}

        <button className="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Starting..." : "Start Run"}
        </button>
      </form>
    </section>
  );
}
