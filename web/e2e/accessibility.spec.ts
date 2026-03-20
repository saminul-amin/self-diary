import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Automated WCAG 2.1 AA accessibility scans using axe-core.
 *
 * Prerequisites:
 *   npm install --save-dev @axe-core/playwright
 *   npx playwright install chromium
 *
 * Run:
 *   npx playwright test e2e/accessibility.spec.ts
 */

test.describe('Accessibility — WCAG 2.1 AA', () => {
  test('login page has no critical violations', async ({ page }) => {
    await page.goto('/login');
    await page.waitForSelector('form');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
  });

  test('register page has no critical violations', async ({ page }) => {
    await page.goto('/register');
    await page.waitForSelector('form');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
  });

  test('entries list page has no critical violations', async ({ page }) => {
    // Requires authenticated session — login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'a11y-test@selfdiary.com');
    await page.fill('input[type="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/entries/);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
  });

  test('new entry page has no critical violations', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'a11y-test@selfdiary.com');
    await page.fill('input[type="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/entries/);

    await page.goto('/entries/new');
    await page.waitForSelector('form');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
  });

  test('settings page has no critical violations', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'a11y-test@selfdiary.com');
    await page.fill('input[type="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/entries/);

    await page.goto('/settings');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
  });
});
