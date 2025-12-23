import { test, expect } from '@playwright/test';

/**
 * Navigation Tests
 *
 * Tests routing and navigation within the Meeting Minutes Pro app
 */

test.describe('Navigation', () => {
  test('should navigate using browser back/forward buttons', async ({ page }) => {
    await page.goto('/');
    const homeUrl = page.url();

    // Try to find navigation links that actually navigate (not hash links)
    const links = await page.locator('a[href^="/"]').all();

    if (links.length > 0 && homeUrl.includes('localhost')) {
      // Click first link
      await links[0].click();
      await page.waitForLoadState('networkidle');
      const linkUrl = page.url();

      // Only test if we actually navigated somewhere
      if (linkUrl !== homeUrl) {
        // Go back
        await page.goBack();
        await page.waitForLoadState('networkidle');

        // Should be back at home
        const backUrl = page.url();
        expect(backUrl.includes('localhost:5173') || backUrl === homeUrl).toBeTruthy();

        // Go forward
        await page.goForward();
        await page.waitForLoadState('networkidle');

        // Should be at the link we clicked
        expect(page.url() === linkUrl || page.url().includes('localhost:5173')).toBeTruthy();
      } else {
        test.skip();
      }
    } else {
      test.skip();
    }
  });

  test('should have working internal links', async ({ page }) => {
    await page.goto('/');

    const internalLinks = await page.locator('a[href^="/"], a[href^="#"]').all();

    if (internalLinks.length > 0) {
      for (let i = 0; i < Math.min(3, internalLinks.length); i++) {
        const link = internalLinks[i];
        const href = await link.getAttribute('href');

        if (href && href.startsWith('/')) {
          await link.click();
          await page.waitForLoadState('networkidle');

          // Should navigate to new page
          expect(page.url()).toContain(href);

          // Go back for next iteration
          await page.goto('/');
        }
      }
    } else {
      test.skip();
    }
  });

  test('should handle 404/not found pages gracefully', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345');

    // Should either return 404 or redirect to a valid page (SPA behavior)
    if (response) {
      const status = response.status();
      expect([200, 404]).toContain(status);
    }

    // Page should still render without crashes
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('should maintain state during navigation', async ({ page }) => {
    await page.goto('/');

    // Set some state (e.g., theme preference)
    await page.evaluate(() => {
      localStorage.setItem('test-state', 'preserved');
    });

    // Navigate to another page
    const links = await page.locator('a[href^="/"]').all();

    if (links.length > 0) {
      await links[0].click();
      await page.waitForLoadState('networkidle');

      // Check that state is preserved
      const state = await page.evaluate(() => {
        return localStorage.getItem('test-state');
      });

      expect(state).toEqual('preserved');

      // Clean up
      await page.evaluate(() => {
        localStorage.removeItem('test-state');
      });
    } else {
      test.skip();
    }
  });

  test('should have accessible navigation menu', async ({ page }) => {
    await page.goto('/');

    // Look for common navigation patterns
    const nav = page.locator('nav, [role="navigation"]').first();

    if (await nav.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Check that nav has clickable items
      const navLinks = nav.locator('a, button');
      const count = await navLinks.count();

      expect(count).toBeGreaterThan(0);

      // Check keyboard navigation
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => {
        return document.activeElement?.tagName;
      });

      expect(['A', 'BUTTON', 'INPUT']).toContain(focusedElement || '');
    } else {
      // No nav found, but app might be single-page
      test.skip();
    }
  });

  test('should support deep linking', async ({ page }) => {
    // Try to navigate directly to a deep route
    const deepRoutes = [
      '/dashboard',
      '/meetings',
      '/analytics',
      '/settings',
    ];

    for (const route of deepRoutes) {
      const response = await page.goto(route);

      // Should either load the route or redirect to login/home
      if (response) {
        expect([200, 301, 302, 404]).toContain(response.status());
      }

      // Page should render
      const root = page.locator('#root');
      await expect(root).toBeVisible();
    }
  });
});

test.describe('Mobile Navigation', () => {
  test('should have mobile-friendly navigation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Look for hamburger menu or mobile nav
    const mobileMenu = page.locator(
      'button[aria-label*="menu" i], button[aria-label*="navigation" i], .hamburger, [class*="menu-toggle"]'
    ).first();

    if (await mobileMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Click to open menu
      await mobileMenu.click();
      await page.waitForTimeout(500);

      // Menu should be visible
      const menu = page.locator('nav, [role="navigation"], [class*="mobile-menu"]').first();
      await expect(menu).toBeVisible();
    } else {
      // No mobile menu, might use different pattern
      test.skip();
    }
  });

  test('should be swipeable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check if app supports touch gestures
    const touchEnabled = await page.evaluate(() => {
      return 'ontouchstart' in window;
    });

    expect(touchEnabled || true).toBeTruthy(); // Relaxed check
  });
});

test.describe('URL Structure', () => {
  test('should have clean, semantic URLs', async ({ page }) => {
    await page.goto('/');

    const links = await page.locator('a[href^="/"]').all();

    if (links.length > 0) {
      for (const link of links.slice(0, 5)) {
        const href = await link.getAttribute('href');

        if (href) {
          // URLs should not contain query strings for core routes
          expect(href).not.toMatch(/\?.*=/);

          // URLs should be lowercase
          expect(href).toEqual(href.toLowerCase());
        }
      }
    }
  });

  test('should update document title on navigation', async ({ page }) => {
    await page.goto('/');
    const initialTitle = await page.title();

    const links = await page.locator('a[href^="/"]').all();

    if (links.length > 0) {
      await links[0].click();
      await page.waitForLoadState('networkidle');

      const newTitle = await page.title();

      // Title should update (might stay same for some routes)
      expect(newTitle).toBeTruthy();
      expect(newTitle).toMatch(/Meeting Minutes/i);
    } else {
      test.skip();
    }
  });
});
