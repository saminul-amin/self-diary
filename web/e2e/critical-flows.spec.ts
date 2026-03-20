/**
 * E2E tests for SelfDiary web client — critical user flows.
 *
 * Prerequisites:
 *   1. Backend running at http://localhost:8000
 *   2. `npx playwright install chromium` (one-time)
 *   3. `npx playwright test` (starts dev server automatically)
 *
 * These tests cover the core user journey:
 *   Register → Create entry → Search → Edit → Delete → Tags → Logout
 */

import { test, expect, type Page } from '@playwright/test';

const TEST_EMAIL = `e2e_${Date.now()}@test.com`;
const TEST_PASSWORD = 'SecurePass123!';

/** Helper: register a new user and navigate to entries. */
async function registerUser(page: Page) {
  await page.goto('/register');
  await page.getByLabel('Email').fill(TEST_EMAIL);
  await page.getByLabel('Password').first().fill(TEST_PASSWORD);
  await page.getByLabel('Display Name').fill('E2E Tester');
  await page.getByRole('button', { name: /sign up|register/i }).click();
  await page.waitForURL('**/entries');
}

/** Helper: log in with the test user. */
async function loginUser(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(TEST_EMAIL);
  await page.getByLabel('Password').fill(TEST_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL('**/entries');
}

test.describe.serial('SelfDiary E2E — Critical Flows', () => {
  test('1. Register new account', async ({ page }) => {
    await registerUser(page);
    await expect(page).toHaveURL(/\/entries/);
  });

  test('2. Login with registered account', async ({ page }) => {
    await loginUser(page);
    await expect(page).toHaveURL(/\/entries/);
  });

  test('3. Create a diary entry', async ({ page }) => {
    await loginUser(page);
    await page.getByRole('link', { name: /new entry|create/i }).click();
    await page.waitForURL('**/entries/new');

    await page.getByLabel(/title/i).fill('My E2E Test Entry');
    await page
      .locator('textarea, [contenteditable]')
      .first()
      .fill('This is an automated test entry created by Playwright.');

    // Select a mood
    await page.getByTitle('great').click();

    await page.getByRole('button', { name: /save|create/i }).click();

    // Should redirect to entries list or entry detail
    await expect(page.getByText('My E2E Test Entry')).toBeVisible({ timeout: 10_000 });
  });

  test('4. Search for entry', async ({ page }) => {
    await loginUser(page);
    await page.goto('/search');

    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill('E2E Test');
    await searchInput.press('Enter');

    await expect(page.getByText('My E2E Test Entry')).toBeVisible({ timeout: 10_000 });
  });

  test('5. Edit an entry', async ({ page }) => {
    await loginUser(page);

    // Navigate to the entry
    await page.getByText('My E2E Test Entry').click();
    await page.waitForURL(/\/entries\/.+/);

    // Click edit button
    await page.getByRole('button', { name: /edit/i }).click();

    // Update the title
    const titleInput = page.getByLabel(/title/i);
    await titleInput.clear();
    await titleInput.fill('My E2E Test Entry (Edited)');

    await page.getByRole('button', { name: /save|update/i }).click();

    await expect(page.getByText('E2E Test Entry (Edited)')).toBeVisible({ timeout: 10_000 });
  });

  test('6. Delete an entry', async ({ page }) => {
    await loginUser(page);

    // Navigate to the entry
    await page.getByText('E2E Test Entry (Edited)').click();
    await page.waitForURL(/\/entries\/.+/);

    // Click delete
    await page.getByRole('button', { name: /delete/i }).click();

    // Confirm deletion if there's a confirmation dialog
    const confirmButton = page.getByRole('button', { name: /confirm|delete|yes/i });
    if (await confirmButton.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await confirmButton.click();
    }

    // Should redirect to entries list
    await page.waitForURL('**/entries');
    await expect(page.getByText('E2E Test Entry (Edited)')).not.toBeVisible({ timeout: 5_000 });
  });

  test('7. Navigate to settings and verify user info', async ({ page }) => {
    await loginUser(page);
    await page.goto('/settings');

    await expect(page.getByText(TEST_EMAIL)).toBeVisible({ timeout: 5_000 });
  });

  test('8. Logout', async ({ page }) => {
    await loginUser(page);
    await page.goto('/settings');

    await page.getByRole('button', { name: /sign out|logout/i }).click();

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });
});
