import { test, expect } from '@playwright/test';

test('has title and can start generation', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/LabGen/);

  // Check if Generate button is present
  const generateButton = page.getByRole('button', { name: /INITIATE GENERATION/i });
  await expect(generateButton).toBeVisible();

  // We won't actually click it to avoid starting the heavy backend process,
  // but we will verify the UI is rendering the left pane correctly
  await expect(page.getByText('Experiment Config')).toBeVisible();
});
