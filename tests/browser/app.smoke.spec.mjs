import { test, expect, gotoReady } from './fixtures.mjs';

test('@smoke démarre sans Failed to fetch et expose les contrôles principaux', async ({ page }) => {
  await gotoReady(page);

  await expect(page.getByRole('navigation', { name: 'Navigation principale' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Astrolabe' })).toBeVisible();
  await expect(page.getByLabel("Orienter l’Astrolabe")).toBeVisible();
  await expect(page.getByLabel('Perspective')).toBeVisible();
  await expect(page.getByLabel('Politique de lecture')).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByText('Failed to fetch', { exact: true })).toHaveCount(0);

  const count = Number((await page.locator('.result-count').textContent())?.trim());
  expect(count).toBeGreaterThanOrEqual(0);
});

test('@smoke les API vitales répondent en JSON', async ({ request }) => {
  const health = await request.get('/api/health');
  expect(health.ok()).toBeTruthy();
  expect(await health.json()).toMatchObject({ status: 'ok' });

  const bootstrap = await request.get('/api/bootstrap');
  expect(bootstrap.ok()).toBeTruthy();
  const body = await bootstrap.json();
  expect(body.version).toBeTruthy();
  expect(Array.isArray(body.entities)).toBeTruthy();
  expect(body.entities.length).toBeGreaterThan(0);
  expect(Array.isArray(body.lenses)).toBeTruthy();
  expect(body.lenses.length).toBeGreaterThan(0);
});
