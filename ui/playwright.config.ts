import path from "node:path";
import { defineConfig } from "@playwright/test";

const UI_DIR = path.resolve(__dirname);
const PROJECT_ROOT = path.resolve(UI_DIR, "..");
const PORT = process.env.DATA_EXTRACT_E2E_PORT || "4173";
const E2E_UI_HOME = process.env.DATA_EXTRACT_E2E_UI_HOME || path.join(UI_DIR, "e2e", ".runtime", "ui-home");
const PYTHONPATH = process.env.PYTHONPATH
  ? `${path.join(PROJECT_ROOT, "src")}:${process.env.PYTHONPATH}`
  : path.join(PROJECT_ROOT, "src");
const pythonCommand = [
  "PYTHON_BIN='python'",
  "if [ -x .venv/bin/python ]; then PYTHON_BIN='.venv/bin/python';",
  "elif command -v python3 >/dev/null 2>&1; then PYTHON_BIN='python3'; fi",
  "\"$PYTHON_BIN\" -m uvicorn data_extract.api.main:app --host 127.0.0.1 --port " + PORT,
].join("; ");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "on-first-retry",
  },
  webServer: {
    command: pythonCommand,
    cwd: PROJECT_ROOT,
    env: {
      ...process.env,
      PYTHONPATH,
      DATA_EXTRACT_UI_HOME: E2E_UI_HOME,
    },
    url: `http://127.0.0.1:${PORT}/`,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
});
