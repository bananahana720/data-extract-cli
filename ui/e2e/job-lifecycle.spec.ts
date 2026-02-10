import { expect, test } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { performance } from "node:perf_hooks";

const TERMINAL_STATUSES = new Set(["completed", "partial", "failed"]);
const ARTIFACTS_DIR = process.env.DATA_EXTRACT_E2E_ARTIFACTS_DIR || path.join(__dirname, ".artifacts");
const RUNTIME_DIR = path.join(__dirname, ".runtime");
const E2E_UI_HOME = process.env.DATA_EXTRACT_E2E_UI_HOME || path.join(RUNTIME_DIR, "ui-home");

type JobPayload = {
  status: string;
  events: Array<{ event_type: string }>;
};

type TerminalState = {
  payload: JobPayload;
  observedStatuses: string[];
  observedEvents: string[];
};

async function waitForTerminalState(
  request: APIRequestContext,
  jobId: string,
  timeoutMs = 20_000
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

    if (TERMINAL_STATUSES.has(payload.status)) {
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
    await page.getByLabel("Input Path (optional when uploading files)").fill(sourceDir);

    const processStart = performance.now();
    await page.getByRole("button", { name: "Start Run" }).click();
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
    await expect(page.locator(".status")).toHaveText(processTerminal.payload.status);

    await fs.chmod(badFile, 0o644);

    const retryStart = performance.now();
    const retryButton = page.getByRole("button", { name: /^Retry Failed/ });
    await expect(retryButton).toBeEnabled();
    await retryButton.click();

    const retryTerminal = await waitForTerminalState(request, jobId);
    const retryTerminalMs = performance.now() - retryStart;

    expect(retryTerminal.payload.status).toBe("completed");
    expect(retryTerminal.observedEvents).toContain("queued");
    expect(retryTerminal.observedEvents).toContain("running");
    await expect(page.locator(".status")).toHaveText("completed");

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
