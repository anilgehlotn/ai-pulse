const { defineConfig, devices } = require("@playwright/test");
const { BACKEND_DIR, FRONTEND_DIR, API_PORT, API_URL, FRONTEND_PORT, FRONTEND_URL, PYTHON, BACKEND_ENV } = require("./backend");

module.exports = defineConfig({
  testDir: "./tests",
  // All tests share one backend and one database, and each test reseeds it, so run them one at a time.
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: FRONTEND_URL,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  // Playwright starts both servers, waits until each URL answers, and stops them at the end.
  webServer: [
    {
      name: "backend",
      command: `"${PYTHON}" -m app.seed && "${PYTHON}" -m uvicorn app.main:app --port ${API_PORT}`,
      cwd: BACKEND_DIR,
      env: BACKEND_ENV,
      url: `${API_URL}/health`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      name: "frontend",
      // A production build, as users get it, pointed at the E2E backend.
      command: `npm run build && npm run preview -- --port ${FRONTEND_PORT} --strictPort`,
      cwd: FRONTEND_DIR,
      env: { VITE_API_URL: API_URL },
      url: FRONTEND_URL,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
