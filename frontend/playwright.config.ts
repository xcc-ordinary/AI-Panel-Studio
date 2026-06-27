import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 120_000,
  expect: { timeout: 15_000 },
  retries: 1,
  workers: 1,

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  webServer: [
    {
      command: 'cd ../backend && .venv\\Scripts\\python -m uvicorn app.main:app --port 8767 --log-level warning',
      port: 8767,
      cwd: '../backend',
      reuseExistingServer: false,
      timeout: 15_000,
      env: { APANEL_TEST: 'false', DEFAULT_MAX_ROUNDS: '6' },
    },
    {
      command: 'npx vite --port 5173 --strictPort',
      port: 5173,
      reuseExistingServer: true,
      timeout: 15_000,
    },
  ],

  globalSetup: './tests/fixtures/global-setup.ts',
});
