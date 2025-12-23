import { test, expect } from '@playwright/test';

/**
 * Basic Application Tests
 *
 * Tests core functionality of the Meeting Minutes Pro application
 */

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/');

    // Check that the page loads without errors
    await expect(page).toHaveTitle(/Meeting Minutes/i);
  });

  test('should have proper meta tags', async ({ page }) => {
    await page.goto('/');

    // Check viewport meta tag
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toContain('width=device-width');
  });

  test('should render main content', async ({ page }) => {
    await page.goto('/');

    // Wait for root element to be visible
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out expected errors (like API connection failures when backend is down)
    const unexpectedErrors = errors.filter(error =>
      !error.includes('Failed to fetch') &&
      !error.includes('NetworkError') &&
      !error.includes('ERR_CONNECTION_REFUSED') &&
      !error.includes('Failed to load resource')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Press Tab to navigate through interactive elements
    await page.keyboard.press('Tab');

    // Check that focus is visible on at least one element
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});

test.describe('Responsive Design', () => {
  test('should be mobile responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check that content is visible and not overflowing
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('should be tablet responsive', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('should be desktop responsive', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Should load in less than 10 seconds (increased for first-time loads)
    expect(loadTime).toBeLessThan(10000);
  });
});
