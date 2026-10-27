import { test, expect } from '@playwright/test';

async function ready(page) {
  await page.goto('/');
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.result-count')).not.toHaveText('—');
  return Number(await page.locator('.result-count').innerText());
}

async function waitResults(page) {
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.result-count')).not.toHaveText('—');
}

test('load, refine, preserve filters across lenses, inspect and restore', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const initialCount = await ready(page);
  expect(initialCount).toBeGreaterThan(0);
  await expect(page.getByText(/entités au catalogue/i)).toBeVisible();

  await page.getByRole('checkbox', { name: 'Philosophie', exact: false }).first().check();
  await waitResults(page);
  await expect(page.locator('.active-filters')).toContainText('Philosophie');

  await page.getByLabel('Perspective', { exact: true }).selectOption('sociodemography');
  await waitResults(page);
  await expect(page.locator('.hidden-filters-note')).toContainText('1 critère');
  await expect(page.locator('.active-filters')).toContainText('Philosophie');

  await page.getByRole('button', { name: 'Inspecter Augustin d’Hippone', exact: true }).click();
  await expect(page.getByRole('complementary', { name: 'Inspecteur d’entité' })).toBeVisible();
  await expect(page.locator('.assertion-card').first()).toBeVisible();

  await page
    .getByLabel('Politique de lecture', { exact: true })
    .selectOption({ label: 'Recherche avec divergences' });
  await waitResults(page);
  await page.getByRole('button', { name: 'Inspecter Augustin d’Hippone', exact: true }).click();
  await expect(page.locator('.status-pill.disputed')).toBeVisible();
  await page.getByLabel('Fermer l’inspecteur').click();

  await page.getByRole('button', { name: '＋ Enregistrer', exact: true }).click();
  await page.getByLabel('Nom de l’exploration').fill('Parcours philosophie');
  await page.getByRole('button', { name: 'Enregistrer ici', exact: true }).click();
  await expect(page.locator('.saved-list')).toContainText('Parcours philosophie');

  await page.reload();
  await waitResults(page);
  await page.getByRole('button', { name: /Mes explorations/ }).click();
  await page.getByRole('button', { name: /^Parcours philosophie/ }).click();
  await waitResults(page);
  await expect(page.locator('.active-filters')).toContainText('Philosophie');
  expect(errors).toEqual([]);
});

test('pivot includes entities beyond the first page, undo and table/constellation modes', async ({
  page,
}) => {
  const baseCount = await ready(page);
  await page.getByLabel('Explorer une relation', { exact: true }).selectOption('authored_work');
  await waitResults(page);
  expect(Number(await page.locator('.result-count').innerText())).toBeGreaterThan(0);
  await expect(page.locator('.query-panel')).toContainText('Auteur');

  await page.getByRole('button', { name: /Tableau/ }).click();
  await expect(page.locator('table')).toBeVisible();
  await page.getByRole('button', { name: /Constellation/ }).click();
  await expect(page.locator('.constellation-view')).toBeVisible();

  await page.getByLabel('Revenir', { exact: true }).click();
  await waitResults(page);
  await expect(page.locator('.result-count')).toHaveText(String(baseCount));

  await page.getByRole('button', { name: 'Suivante →', exact: true }).click();
  await waitResults(page);
  await expect(page.locator('.entity-list')).not.toContainText('Augustin d’Hippone');
});

test('mobile navigation has no horizontal overflow and period filter works', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  await page.getByLabel('Année de début', { exact: true }).fill('300');
  await page.getByLabel('Année de fin', { exact: true }).fill('500');
  await page.getByRole('button', { name: 'Appliquer la période →', exact: true }).click();
  await expect(page.locator('.active-filters')).toContainText('300–500');
  await waitResults(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test('export and import exploration JSON round trips', async ({ page }) => {
  await ready(page);
  await page.getByRole('button', { name: '＋ Enregistrer', exact: true }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exporter JSON', exact: true }).click();
  const file = await download;
  const filePath = await file.path();
  await page.locator('input[type=file]').setInputFiles(filePath);
  await expect(page.getByRole('status')).toContainText('Exploration restaurée');
});
