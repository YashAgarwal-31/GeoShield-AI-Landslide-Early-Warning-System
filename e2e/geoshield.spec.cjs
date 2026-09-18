const { test, expect } = require('@playwright/test');

const adminEmail = process.env.E2E_ADMIN_EMAIL || 'e2e-admin@example.invalid';
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'StrongE2EAdminPassword123!';
const citizenEmail = 'browser-citizen@example.invalid';
const citizenPassword = 'BrowserCitizenPass123!';

async function apiLogin(request, email, password) {
  const response = await request.post('/api/auth/login', {
    form: { email, password },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()).token;
}

async function uiLogin(page, email, password) {
  await page.goto('/');
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole('button', { name: 'Sign In to GeoShield' }).click();
  await expect(page.getByText('SYSTEM READY')).toBeVisible();
}

test('citizen report can be submitted in the UI and verified by an admin', async ({ page, request }) => {
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  const adminToken = await apiLogin(request, adminEmail, adminPassword);
  const createCitizen = await request.post('/api/users', {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      email: citizenEmail,
      name: 'Browser Citizen',
      password: citizenPassword,
      role: 'citizen',
    },
  });
  expect([201, 409]).toContain(createCitizen.status());

  const description = `Browser E2E slope crack ${Date.now()}`;

  await uiLogin(page, citizenEmail, citizenPassword);
  await page.getByRole('link', { name: 'Reports' }).click();
  await expect(page.getByRole('heading', { name: 'Reports' })).toBeVisible();

  await page.getByRole('button', { name: 'Submit Report' }).click();
  await page.locator('textarea').fill(description);
  await page.locator('input[placeholder="25.5788"]').fill('25.58');
  await page.locator('input[placeholder="91.8933"]').fill('91.89');
  await page.locator('input[type="file"]').setInputFiles({
    name: 'evidence.png',
    mimeType: 'image/png',
    buffer: Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      Buffer.from('GeoShield browser E2E evidence'),
    ]),
  });
  await page.getByRole('button', { name: 'Submit', exact: true }).click();

  await expect(page.getByText('Report Submitted Successfully!')).toBeVisible();
  await expect(page.getByText(description)).toBeVisible({ timeout: 8_000 });

  await page.getByTitle('Logout').click();
  await expect(page.getByRole('button', { name: 'Sign In to GeoShield' })).toBeVisible();

  await uiLogin(page, adminEmail, adminPassword);
  await page.getByRole('link', { name: 'Administration' }).click();
  await expect(page.getByRole('heading', { name: 'System Administration' })).toBeVisible();
  await expect(page.getByText('Monitoring station inventory')).toBeVisible();

  await page.getByRole('link', { name: 'Reports' }).click();
  const reportCard = page.locator('div.glass').filter({ hasText: description }).first();
  await expect(reportCard).toBeVisible();
  await expect(reportCard.getByRole('button', { name: 'View evidence' })).toBeVisible();

  await reportCard.getByRole('button', { name: 'Verify' }).click();
  await expect(reportCard.getByText('Report verified successfully')).toBeVisible();
  await expect(reportCard.getByText('Verified', { exact: true })).toBeVisible();

  expect(pageErrors).toEqual([]);
});
