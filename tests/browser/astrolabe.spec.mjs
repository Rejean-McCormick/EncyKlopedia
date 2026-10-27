import { test, expect, gotoReady } from './fixtures.mjs';

const cases = [
  ['Moïse', /Moïse|Moses/i],
  ['Joseph', /Joseph/i],
  ['ressurection', /Résurrection/i],
  ['Saint-Esprit', /Saint-Esprit/i],
  ['parousie', /Parousie/i],
  ['iconoclaste', /Images et iconoclasme|Iconoclasme/i],
  ['eudiste', /Spiritualité eudiste/i],
];

for (const [term, title] of cases) {
  test(`@astrolabe oriente « ${term} » sans erreur réseau`, async ({ page }) => {
    await gotoReady(page);
    const input = page.getByLabel("Orienter l’Astrolabe");
    await input.fill(term);

    const reading = page.locator('.astrolabe-reading');
    await expect(reading).toBeVisible();
    await expect(reading).toContainText(title);
    await expect(page.getByRole('alert')).toHaveCount(0);

    const capButton = page.getByRole('button', { name: 'Prendre le cap →' });
    if (term !== 'eudiste') {
      await expect(capButton).toBeEnabled();
      await expect(page.locator('.astrolabe-cap').first()).toBeVisible();
    } else {
      await expect(reading).toContainText(/orientation par proximité|Piste voisine/i);
    }
  });
}

test('@astrolabe prendre un cap transforme le mot en sélection Konstellation', async ({ page }) => {
  await gotoReady(page);
  await page.getByLabel("Orienter l’Astrolabe").fill('Moïse');
  await expect(page.locator('.astrolabe-cap').first()).toBeVisible();
  await page.getByRole('button', { name: 'Prendre le cap →' }).click();

  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.active-filters')).toContainText(/1 identit/);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.locator('.result-count')).not.toHaveText('—');
});


test('@astrolabe Joseph expose les personnages bibliques homonymes avec désambiguïsation', async ({ page }) => {
  await gotoReady(page);
  await page.getByLabel("Orienter l’Astrolabe").fill('Joseph');

  const reading = page.locator('.astrolabe-reading');
  await expect(reading).toContainText(/12 correspondances/i);
  await expect(page.locator('.astrolabe-cap')).toHaveCount(12);
  await expect(reading).toContainText(/Joseph — fils de Jacob et Rachel/i);
  await expect(reading).toContainText(/Joseph — époux de Marie/i);
  await expect(reading).toContainText(/Joseph — d’Arimathie/i);
  await expect(reading).toContainText(/Joseph — Barnabé/i);
});

test('@astrolabe la recherche de liste cherche aussi dans tout le corpus', async ({ page }) => {
  await gotoReady(page);
  await page.getByLabel('Chercher dans le corpus').fill('Joseph');
  const global = page.locator('.catalog-search-results');
  await expect(global).toBeVisible();
  await expect(global).toContainText(/Joseph — époux de Marie/i);
  await expect(global).toContainText(/Personnage biblique/i);
});


test('@astrolabe un Joseph ouvre la perspective des personnages bibliques', async ({ page }) => {
  await gotoReady(page);
  await page.getByLabel("Orienter l’Astrolabe").fill('Joseph');
  await page.locator('.astrolabe-cap').filter({ hasText: 'époux de Marie' }).click();
  await expect(page.locator('.results-body')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.results-heading h2')).toContainText(/Personnages bibliques/i);
  await expect(page.locator('.active-filters')).toContainText(/1 identit/i);
});
