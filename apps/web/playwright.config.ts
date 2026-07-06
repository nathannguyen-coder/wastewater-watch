import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: process.env.CI
        ? "cd ../.. && python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8010"
        : "cd ../.. && .venv/bin/python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8010",
      url: "http://127.0.0.1:8010/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "SENTINEL_API_TARGET=http://127.0.0.1:8010 npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
})
