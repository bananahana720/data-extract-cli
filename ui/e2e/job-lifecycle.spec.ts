import { expect, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";

const TERMINAL_STATUSES = new Set(["completed", "partial", "failed"]);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ARTIFACTS_DIR = process.env.DATA_EXTRACT_E2E_ARTIFACTS_DIR || path.join(__dirname, ".artifacts");
const RUNTIME_DIR = path.join(__dirname, ".runtime");
const E2E_UI_HOME = process.env.DATA_EXTRACT_E2E_UI_HOME || path.join(RUNTIME_DIR, "ui-home");

type JobPayload = {
  status: string;
  events: Array<{ event_type: string }>;
};

type WaitForTerminalOptions = {
  minEventCount?: number;
  requireStatusChangeFrom?: string;
};

type TerminalState = {
  payload: JobPayload;
  observedStatuses: string[];
  observedEvents: string[];
};

async function waitForTerminalState(
  request: APIRequestContext,
  jobId: string,
  timeoutMs = 20_000,
  options: WaitForTerminalOptions = {}
): Promise<TerminalState> {
  const started = Date.now();
  const observedStatuses = new Set<string>();
  const observedEvents = new Set<string>();

  while (Date.now() - started <= timeoutMs) {
    const response = await request.get(`/api/v1/jobs/${jobId}`);
    expect(response.ok()).toBeTruthy();
    const payload = (await response.json()) as JobPayload;
    observedStatuses.add(payload.status);
    for (const event of payload.events) {
      observedEvents.add(event.event_type);
    }

    const minimumEventsSatisfied = options.minEventCount ? payload.events.length >= options.minEventCount : true;
    const statusChangeSatisfied = options.requireStatusChangeFrom
      ? payload.status !== options.requireStatusChangeFrom || !TERMINAL_STATUSES.has(payload.status)
      : true;

    if (minimumEventsSatisfied && statusChangeSatisfied && TERMINAL_STATUSES.has(payload.status)) {
      return {
        payload,
        observedStatuses: Array.from(observedStatuses),
        observedEvents: Array.from(observedEvents),
      };
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }

  throw new Error(`Job ${jobId} did not reach terminal status within ${timeoutMs}ms`);
}

async function waitForCleanupEvent(
  request: APIRequestContext,
  jobId: string,
  timeoutMs = 20_000
): Promise<void> {
  const started = Date.now();
  while (Date.now() - started <= timeoutMs) {
    const response = await request.get(`/api/v1/jobs/${jobId}`);
    expect(response.ok()).toBeTruthy();
    const payload = (await response.json()) as JobPayload;
    if (payload.events.some((event) => event.event_type === "cleanup")) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Cleanup event was not observed for job ${jobId}`);
}

test("process -> status -> retry -> cleanup lifecycle", async ({ page, request }, testInfo) => {
  const runRoot = path.join(
    RUNTIME_DIR,
    `run-${testInfo.repeatEachIndex}-${testInfo.retry}-${Date.now().toString(36)}`
  );
  const sourceDir = path.join(runRoot, "inputs");
  const goodFile = path.join(sourceDir, "good.txt");
  const badFile = path.join(sourceDir, "bad.txt");
  const metricsPath = path.join(ARTIFACTS_DIR, `metrics-repeat-${testInfo.repeatEachIndex}.json`);

  await fs.mkdir(sourceDir, { recursive: true });
  await fs.writeFile(goodFile, "clean text payload", "utf8");
  await fs.writeFile(badFile, "unreadable payload", "utf8");
  await fs.chmod(badFile, 0o000);

  try {
    await page.goto("/");
    const sourcePathMode = page.getByTestId("new-run-source-path");
    const sourceUploadMode = page.getByTestId("new-run-source-upload");
    const pathInput = page.getByTestId("new-run-input-path");
    const chunkSizeInput = page.getByTestId("new-run-chunk-size");
    const submitButton = page.getByTestId("new-run-submit");
    const summaryCard = page.getByTestId("new-run-summary-card");

    await expect(sourcePathMode).toBeChecked();
    await expect(sourceUploadMode).not.toBeChecked();
    await expect(page.getByTestId("new-run-source-panel-path")).toBeVisible();
    await expect(page.getByTestId("new-run-source-panel-upload")).toBeVisible();
    await expect(summaryCard).toBeVisible();
    await expect(summaryCard).toContainText("Source Mode");
    await expect(summaryCard).toContainText("Not set");

    await pathInput.fill("   ");
    await submitButton.click();
    await expect(page.locator("#new-run-input-path-error")).toBeVisible();

    await pathInput.fill(sourceDir);
    await chunkSizeInput.fill("12");
    await submitButton.click();
    await expect(page.locator("#new-run-chunk-size-error")).toBeVisible();

    await sourceUploadMode.check();
    await submitButton.click();
    await expect(page.locator("#new-run-upload-error")).toBeVisible();

    await sourcePathMode.check();
    await pathInput.fill(sourceDir);
    await chunkSizeInput.fill("512");
    await expect(summaryCard).toContainText(sourceDir);
    await expect(summaryCard).toContainText("Chunk Size");

    const processStart = performance.now();
    await submitButton.click();
    await page.waitForURL(/\/jobs\/[^/]+$/);

    const match = page.url().match(/\/jobs\/([^/?#]+)/);
    if (!match) {
      throw new Error("Could not derive job id from URL");
    }
    const jobId = match[1];

    const processTerminal = await waitForTerminalState(request, jobId);
    const processTerminalMs = performance.now() - processStart;

    expect(["partial", "failed"]).toContain(processTerminal.payload.status);
    expect(processTerminal.observedEvents).toContain("queued");
    expect(processTerminal.observedEvents).toContain("running");
    await expect(page.getByTestId("job-status-chip")).toHaveText(processTerminal.payload.status);
    await expect(page.getByTestId("job-next-action")).toBeVisible();
    await expect(page.getByTestId("job-lifecycle-timeline")).toBeVisible();
    await expect(page.getByTestId("job-progress-card")).toBeVisible();
    await expect(page.getByTestId("job-runtime-metadata")).toBeVisible();
    await expect(page.getByTestId("job-actions-hint")).toBeVisible();
    await expect
      .poll(async () => page.locator("[data-testid^='job-timeline-item-']").count())
      .toBeGreaterThanOrEqual(2);

    await fs.chmod(badFile, 0o644);

    const retryStart = performance.now();
    const retryButton = page.getByRole("button", { name: /^Retry Failed/ });
    await expect(retryButton).toBeEnabled();
    await retryButton.click();

    const retryTerminal = await waitForTerminalState(request, jobId, 20_000, {
      minEventCount: processTerminal.payload.events.length + 1,
      requireStatusChangeFrom: processTerminal.payload.status,
    });
    const retryTerminalMs = performance.now() - retryStart;

    expect(retryTerminal.payload.status).toBe("completed");
    expect(retryTerminal.observedEvents).toContain("queued");
    expect(retryTerminal.observedEvents).toContain("running");
    await expect(page.getByTestId("job-status-chip")).toHaveText("completed");
    await expect(page.getByTestId("job-next-action")).toContainText("Next Action:");

    const cleanupStart = performance.now();
    await page.getByRole("button", { name: "Cleanup Artifacts" }).click();
    await waitForCleanupEvent(request, jobId);
    const jobArtifacts = path.join(E2E_UI_HOME, "jobs", jobId);
    await expect
      .poll(async () => {
        try {
          await fs.access(jobArtifacts);
          return true;
        } catch {
          return false;
        }
      })
      .toBe(false);
    const cleanupMs = performance.now() - cleanupStart;
    await expect(page.getByTestId("job-next-action")).toContainText("Artifacts are already cleaned");
    await expect(page.getByTestId("job-actions-hint")).toContainText("Artifacts are already cleaned");

    await page.getByRole("link", { name: "Jobs" }).click();
    await expect(page).toHaveURL(/\/jobs$/);
    await expect(page.getByTestId("jobs-page")).toBeVisible();
    await expect(page.getByTestId("jobs-summary-total")).not.toHaveText("0");
    await page.getByTestId("jobs-filter-search").fill(jobId);
    await expect(page.getByRole("link", { name: jobId })).toBeVisible();
    await page.getByTestId("jobs-filter-status").selectOption("completed");
    await expect(page.getByRole("link", { name: jobId })).toBeVisible();
    await page.getByTestId("jobs-filter-search").fill("not-a-real-job-id");
    await expect(page.getByTestId("jobs-filter-empty-state")).toBeVisible();
    await page.getByRole("button", { name: "Clear filters" }).click();
    await page.getByTestId("jobs-refresh-button").click();

    await fs.mkdir(ARTIFACTS_DIR, { recursive: true });
    await fs.writeFile(
      metricsPath,
      JSON.stringify(
        {
          job_id: jobId,
          repeat_each_index: testInfo.repeatEachIndex,
          process_terminal_ms: processTerminalMs,
          retry_terminal_ms: retryTerminalMs,
          cleanup_ms: cleanupMs,
          process_terminal_status: processTerminal.payload.status,
          retry_terminal_status: retryTerminal.payload.status,
          observed_process_events: processTerminal.observedEvents,
          observed_retry_events: retryTerminal.observedEvents,
          failed: false,
        },
        null,
        2
      ),
      "utf8"
    );
  } finally {
    try {
      await fs.chmod(badFile, 0o644);
    } catch {
      // Best effort cleanup for read-only test fixture.
    }
  }
});
