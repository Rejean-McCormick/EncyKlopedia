import { test as base, expect } from '@playwright/test';

function interestingConsoleMessage(message) {
  return message.type() === 'error' && !/favicon\.ico/i.test(message.text());
}

export const test = base.extend({
  diagnostics: [
    async ({ page }, use, testInfo) => {
      const pageErrors = [];
      const consoleErrors = [];
      const failedRequests = [];
      const serverErrors = [];
      const apiErrors = [];

      page.on('pageerror', (error) => pageErrors.push(error.message));
      page.on('console', (message) => {
        if (interestingConsoleMessage(message)) consoleErrors.push(message.text());
      });
      page.on('requestfailed', (request) => {
        const reason = request.failure()?.errorText || 'échec réseau';
        if (!/ERR_ABORTED/i.test(reason)) {
          failedRequests.push(`${request.method()} ${request.url()} — ${reason}`);
        }
      });
      page.on('response', async (response) => {
        if (response.status() >= 500) {
          serverErrors.push(`${response.status()} ${response.request().method()} ${response.url()}`);
        }
        if (response.status() >= 400 && response.url().includes('/api/')) {
          let detail = '';
          try {
            detail = (await response.text()).slice(0, 500);
          } catch {
            detail = '<corps indisponible>';
          }
          apiErrors.push(
            `${response.status()} ${response.request().method()} ${response.url()}${detail ? ` — ${detail}` : ''}`,
          );
        }
      });

      await use({ pageErrors, consoleErrors, failedRequests, serverErrors, apiErrors });

      const diagnostics = { pageErrors, consoleErrors, failedRequests, serverErrors, apiErrors };
      await testInfo.attach('diagnostics.json', {
        body: Buffer.from(JSON.stringify(diagnostics, null, 2)),
        contentType: 'application/json',
      });

      if (testInfo.status === testInfo.expectedStatus) {
        expect.soft(pageErrors, 'erreurs JavaScript non gérées').toEqual([]);
        expect.soft(consoleErrors, 'console.error inattendu').toEqual([]);
        expect.soft(failedRequests, 'requêtes réseau échouées').toEqual([]);
        expect.soft(serverErrors, 'réponses HTTP 5xx').toEqual([]);
        expect.soft(apiErrors, 'réponses API HTTP 4xx/5xx').toEqual([]);
      }
    },
    { auto: true },
  ],
});

export { expect };

export async function gotoReady(page) {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1, name: /Suivez le fil des idées/ })).toBeVisible();
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.result-count')).not.toHaveText('—');
  await expect(page.getByRole('alert')).toHaveCount(0);
}

export function normalize(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[_–—-]+/g, ' ')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function entityMatches(entity, term) {
  const needle = normalize(term);
  return [entity.label, ...(entity.aliases || [])].some((value) => normalize(value) === needle);
}
