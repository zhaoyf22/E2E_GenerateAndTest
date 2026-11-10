import { test, expect, request as playwrightRequest } from '@playwright/test';

/**
 * TestForge Playwright skeleton.
 * - API setup creates data (faster, more stable than UI setup).
 * - Role/label/testid selectors only.
 * - Web-first assertions; no sleep.
 * - Each test owns its data and cleans up.
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const API_URL = process.env.API_URL ?? 'http://localhost:8000';

test.describe('下单与支付', () => {
  let api: Awaited<ReturnType<typeof playwrightRequest.newContext>>;
  const email = `buyer+${Date.now()}@example.com`;

  test.beforeAll(async () => {
    api = await playwrightRequest.newContext({ baseURL: API_URL });
    const response = await api.post('/test/seed', {
      data: { email, sku: 'SKU-001', stock: 10, price: 99.0 },
    });
    expect(response.ok()).toBeTruthy();
  });

  test.afterAll(async () => {
    await api.post('/test/cleanup', { data: { email } });
    await api.dispose();
  });

  test('已登录用户购买单件商品并支付成功', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel('邮箱').fill(email);
    await page.getByLabel('密码').fill('Abc12345');
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.getByRole('link', { name: '商品 SKU-001' }).click();
    await page.getByRole('button', { name: '加入购物车' }).click();
    await page.getByRole('link', { name: '购物车' }).click();
    await page.getByRole('button', { name: '去结算' }).click();

    await page.getByLabel('在线支付').check();
    await page.getByRole('button', { name: '提交订单' }).click();

    await expect(page).toHaveURL(/\/orders\/[^/]+$/);
    await expect(page.getByTestId('order-status')).toHaveText('待支付');

    await page.getByRole('button', { name: '立即支付' }).click();
    await expect(page.getByTestId('order-status')).toHaveText('已支付');

    const stock = await api.get('/products/SKU-001');
    expect(stock.ok()).toBeTruthy();
    expect((await stock.json()).stock).toBe(9);
  });

  test('库存不足时提交订单被拒绝', async ({ page }) => {
    await api.post('/test/set-stock', { data: { sku: 'SKU-001', stock: 1 } });

    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel('邮箱').fill(email);
    await page.getByLabel('密码').fill('Abc12345');
    await page.getByRole('button', { name: '登录' }).click();

    await page.goto(`${BASE_URL}/cart`);
    await page.getByTestId('qty-SKU-001').fill('2');
    await page.getByRole('button', { name: '提交订单' }).click();

    await expect(page.getByRole('alert')).toHaveText('库存不足');
    const stock = await api.get('/products/SKU-001');
    expect((await stock.json()).stock).toBe(1);
    const orders = await api.get(`/orders?email=${encodeURIComponent(email)}`);
    expect((await orders.json()).items).toHaveLength(0);
  });
});
