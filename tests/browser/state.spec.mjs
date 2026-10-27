import { test, expect, gotoReady } from './fixtures.mjs';

test('@state enregistre puis restaure une exploration locale', async ({ page }) => {
  await gotoReady(page);
  await page.getByRole('button', { name: /Enregistrer/ }).first().click();
  await page.getByLabel("Nom de l’exploration").fill('Test Playwright');
  await page.getByRole('button', { name: 'Enregistrer ici' }).click();
  await expect(page.locator('.saved-list')).toContainText('Test Playwright');

  await page.reload();
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await page.getByRole('button', { name: /Mes explorations/ }).click();
  await expect(page.locator('.saved-list')).toContainText('Test Playwright');
});

test('@state exporte et réimporte le QuerySpec complet', async ({ page }) => {
  await gotoReady(page);
  await page.getByRole('button', { name: /Enregistrer/ }).first().click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exporter JSON' }).click();
  const download = await downloadPromise;
  const path = await download.path();
  expect(path).toBeTruthy();

  await page.locator('input[type=file]').setInputFiles(path);
  await expect(page.getByRole('status')).toContainText('Exploration restaurée');
});
