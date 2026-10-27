import { test, expect, gotoReady } from './fixtures.mjs';

test('@navigation change de perspective et revient en arrière sans perdre le contexte', async ({ page }) => {
  await gotoReady(page);
  const perspective = page.getByLabel('Perspective');
  const options = await perspective.locator('option').evaluateAll((els) => els.map((e) => ({ value: e.value, text: e.textContent })));
  expect(options.length).toBeGreaterThan(1);

  const target = options.find((option) => option.value === 'biblical-works') || options[1];
  await perspective.selectOption(target.value);
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.getByRole('alert')).toHaveCount(0);

  await page.getByLabel('Revenir').click();
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('@navigation liste, tableau et constellation restent utilisables', async ({ page }) => {
  await gotoReady(page);
  await page.getByRole('button', { name: /Tableau/ }).click();
  await expect(page.locator('table')).toBeVisible();

  await page.getByRole('button', { name: /Constellation/ }).click();
  await expect(page.locator('.graph-view, .constellation-view').first()).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('@navigation inspecter une entité ouvre ses assertions sans erreur', async ({ page }) => {
  await gotoReady(page);
  const inspect = page.locator('.entity-meta button').first();
  await expect(inspect).toBeVisible();
  await inspect.click();
  await expect(page.getByRole('complementary', { name: "Inspecteur d’entité" })).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});
