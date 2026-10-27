import { test, expect, gotoReady } from './fixtures.mjs';

test('@responsive aucun débordement horizontal majeur en mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoReady(page);
  const dimensions = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(dimensions.document).toBeLessThanOrEqual(dimensions.viewport + 2);
});

test('@responsive Astrolabe reste utilisable en mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoReady(page);
  await page.getByLabel("Orienter l’Astrolabe").fill('parousie');
  await expect(page.locator('.astrolabe-reading')).toBeVisible();
  await expect(page.locator('.astrolabe-cap').first()).toBeVisible();
});
