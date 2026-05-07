// e2e/fixtures/auth.setup.js
// Run once before the entire test suite. Saves auth cookies so subsequent
// tests can skip the login page entirely — dramatically faster execution.
import { test as setup, expect } from '@playwright/test';
import { fileURLToPath } from 'url';
import path from 'path';

// ESM-safe equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

export const ADMIN_FILE = path.join(__dirname, '../.auth/admin.json');

const BACKEND_URL = 'http://localhost:8000';

setup('authenticate as admin', async ({ page, request }) => {
  // ── Step 1: Check if backend is ready ──
  console.log('Checking local backend…');
  for (let i = 0; i < 5; i++) {
    try {
      const res = await request.get(`${BACKEND_URL}/api/health`, { timeout: 5000 });
      if (res.ok()) { console.log('Backend is up ✅'); break; }
    } catch {}
    console.log(`  Attempt ${i + 1}/5 — backend not ready yet, waiting 2s…`);
    await page.waitForTimeout(2000);
  }

  // ── Step 2: Log in and save cookies ─────────────────────────────────────────
  await page.goto('/login');
  await page.fill('input[type="text"]',     'TT0004');
  await page.fill('input[type="password"]', 'admin@123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  // Persist cookie / localStorage so every test file can reuse them
  await page.context().storageState({ path: ADMIN_FILE });
});
