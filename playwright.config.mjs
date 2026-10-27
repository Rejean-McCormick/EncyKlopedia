import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PLAYWRIGHT_PORT || 4323);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`;
const localPack = path.join(ROOT, 'data', 'biblical.pack.local.json');
const enrichedPack = path.join(ROOT, 'data', 'theophile-biblical.enriched.pack.json');
const testPack = process.env.KONSTELLATION_TEST_PACK || enrichedPack;
const testLenses = process.env.KONSTELLATION_TEST_LENSES || path.join(ROOT, 'lenses-enriched');
const externalServer = Boolean(process.env.PLAYWRIGHT_BASE_URL);

export default defineConfig({
  testDir: './tests/browser',
  outputDir: './test-results/playwright-artifacts',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  forbidOnly: Boolean(process.env.CI),
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL,
    headless: process.env.PLAYWRIGHT_HEADED !== '1',
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    locale: 'fr-CA',
    colorScheme: 'light',
    launchOptions: {
      ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
        ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
        : {}),
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  ...(externalServer
    ? {}
    : {
        webServer: {
          // Important: le pack est préparé AVANT le démarrage du serveur.
          // Le serveur de test utilise le pack Théophile + graphe biblique livré.
          command: 'node scripts/prepare-playwright-corpus.mjs && npm run build && node server/index.mjs',
          url: `${baseURL}/api/health`,
          reuseExistingServer: false,
          timeout: 180_000,
          env: {
            ...process.env,
            HOST: '127.0.0.1',
            PORT: String(port),
            KONSTELLATION_PACK: testPack,
            KONSTELLATION_LENSES: testLenses,
            KONSTELLATION_SA_CONFIG: '',
          },
        },
      }),
});
