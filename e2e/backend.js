// Shared by playwright.config.js and the tests: where the servers run and how to reseed the database.
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BACKEND_DIR = path.join(__dirname, "..", "backend");
const FRONTEND_DIR = path.join(__dirname, "..", "frontend");

// Port 8000 is what CI uses. Set E2E_API_PORT to run next to a dev backend that already has 8000.
const API_PORT = process.env.E2E_API_PORT || "8000";
const API_URL = `http://localhost:${API_PORT}`;
const FRONTEND_PORT = "4173";
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

// A throwaway database in the temp folder, so the tests never touch backend/aipulse.db.
const DB_PATH = path.join(os.tmpdir(), "ai-pulse-e2e.db");

// Locally use the venv from `make setup`; in CI use the Python that setup-python installed.
const VENV_PYTHON = path.join(BACKEND_DIR, ".venv", "bin", "python");
const PYTHON = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : "python";

const BACKEND_ENV = {
  ...process.env,
  APP_ENV: "test",
  AI_MODE: "mock",
  DATABASE_URL: `sqlite:///${DB_PATH}`,
  CORS_ORIGINS: FRONTEND_URL,
  // Every test logs in from the same IP (localhost). The default of 30 logins a minute
  // would start refusing them partway through the run, so allow far more here.
  LOGIN_MAX_PER_IP: "1000",
};

// Wipe the database and load the demo data again, so every test starts from the same state.
function reseed() {
  execFileSync(PYTHON, ["-m", "app.seed"], { cwd: BACKEND_DIR, env: BACKEND_ENV, stdio: "ignore" });
}

module.exports = { BACKEND_DIR, FRONTEND_DIR, API_PORT, API_URL, FRONTEND_PORT, FRONTEND_URL, PYTHON, BACKEND_ENV, reseed };
