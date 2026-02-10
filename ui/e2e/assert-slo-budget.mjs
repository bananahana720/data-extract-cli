#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const MIN_SAMPLE_SIZE = 3;
const TERMINAL_WITHIN_MS = 20_000;
const THRESHOLDS = {
  process_terminal_ms: 15_000,
  retry_terminal_ms: 15_000,
  cleanup_ms: 2_000,
};

function p95(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.max(0, Math.ceil(sorted.length * 0.95) - 1);
  return sorted[index];
}

function toNumber(value, field, filePath) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Invalid numeric field ${field} in ${filePath}`);
  }
  return parsed;
}

async function loadMetrics(metricsDir) {
  const entries = await fs.readdir(metricsDir, { withFileTypes: true });
  const metricFiles = entries
    .filter((entry) => entry.isFile() && /^metrics-repeat-\d+\.json$/.test(entry.name))
    .map((entry) => path.join(metricsDir, entry.name))
    .sort();

  const payloads = [];
  for (const metricFile of metricFiles) {
    const raw = await fs.readFile(metricFile, "utf8");
    const parsed = JSON.parse(raw);
    payloads.push({
      file: metricFile,
      process_terminal_ms: toNumber(parsed.process_terminal_ms, "process_terminal_ms", metricFile),
      retry_terminal_ms: toNumber(parsed.retry_terminal_ms, "retry_terminal_ms", metricFile),
      cleanup_ms: toNumber(parsed.cleanup_ms, "cleanup_ms", metricFile),
      process_terminal_status: String(parsed.process_terminal_status || ""),
      retry_terminal_status: String(parsed.retry_terminal_status || ""),
      failed: Boolean(parsed.failed),
    });
  }

  return payloads;
}

function evaluate(metrics) {
  const failures = [];
  if (metrics.length < MIN_SAMPLE_SIZE) {
    failures.push(
      `Minimum sample size violation: required ${MIN_SAMPLE_SIZE}, found ${metrics.length}`
    );
    return failures;
  }

  const failureRuns = metrics.filter((entry) => {
    if (entry.failed) {
      return true;
    }
    if (!["partial", "failed"].includes(entry.process_terminal_status)) {
      return true;
    }
    if (entry.retry_terminal_status !== "completed") {
      return true;
    }
    return false;
  });

  if (failureRuns.length > 0) {
    failures.push(
      `Failure budget exceeded: expected 0 failed runs, observed ${failureRuns.length}`
    );
  }

  for (const [field, threshold] of Object.entries(THRESHOLDS)) {
    const values = metrics.map((entry) => entry[field]);
    const currentP95 = p95(values);
    if (currentP95 > threshold) {
      failures.push(`SLO breach for ${field}: p95=${currentP95.toFixed(2)}ms > ${threshold}ms`);
    }
  }

  for (const entry of metrics) {
    if (entry.process_terminal_ms > TERMINAL_WITHIN_MS) {
      failures.push(
        `Terminal bound breach (${entry.file}): process_terminal_ms=${entry.process_terminal_ms.toFixed(2)}ms`
      );
    }
    if (entry.retry_terminal_ms > TERMINAL_WITHIN_MS) {
      failures.push(
        `Terminal bound breach (${entry.file}): retry_terminal_ms=${entry.retry_terminal_ms.toFixed(2)}ms`
      );
    }
    if (entry.cleanup_ms > TERMINAL_WITHIN_MS) {
      failures.push(
        `Terminal bound breach (${entry.file}): cleanup_ms=${entry.cleanup_ms.toFixed(2)}ms`
      );
    }
  }

  return failures;
}

async function main() {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const metricsDir =
    process.argv[2] ||
    process.env.DATA_EXTRACT_E2E_ARTIFACTS_DIR ||
    path.resolve(scriptDir, ".artifacts");

  let metrics;
  try {
    metrics = await loadMetrics(metricsDir);
  } catch (error) {
    console.error(`Unable to load metrics from ${metricsDir}: ${error}`);
    process.exit(1);
  }

  const failures = evaluate(metrics);
  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(`FAIL ${failure}`);
    }
    process.exit(1);
  }

  const summary = {
    samples: metrics.length,
    p95: {
      process_terminal_ms: p95(metrics.map((entry) => entry.process_terminal_ms)),
      retry_terminal_ms: p95(metrics.map((entry) => entry.retry_terminal_ms)),
      cleanup_ms: p95(metrics.map((entry) => entry.cleanup_ms)),
    },
  };
  console.log(JSON.stringify(summary, null, 2));
}

main();
