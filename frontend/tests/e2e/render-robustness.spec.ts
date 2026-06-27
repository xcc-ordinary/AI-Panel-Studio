/**
 * Scenario 3: 渲染健壮性
 *
 * 加载一个含分歧 camps 的讨论（seed-001：1 consensus + 1 divergence with 3 camps），
 * 断言页面不白屏、camps 区块正常渲染。
 * 锁死 (d.camps||[]).map 崩树回归。
 */
import { test, expect } from '@playwright/test';
import { goHome, joinDiscussion, assertDivergenceWithCamps } from './helpers';

test.describe('Render Robustness', () => {
  test('divergence camps render without white screen', async ({ page }) => {
    test.setTimeout(30_000);

    // ── Navigate & join seed-001 ────────────────────────
    await goHome(page);

    // seed-001 card should be visible on the home page
    const card = page.locator('[data-discussion-id="seed-001-ai-open-source"]');
    await expect(card).toBeVisible({ timeout: 10_000 });
    await card.click();

    // ── Wait for studio view to fully load ────────────────
    // StudioView goes through loading → normal. Wait for the connection status.
    await page.waitForSelector('[data-testid="connection-status"]', { timeout: 10_000 });

    // ── Wait for REST calls to populate the UI ────────────
    // REST GET /transcript + GET /consensus/current for seed-001
    await page.waitForTimeout(2_000);

    // ── Assert page is not white screen ──────────────────
    // If (d.camps||[]).map crashes, the entire StudioView tree dies
    const studioRoot = page.locator('header');
    await expect(studioRoot).toBeVisible();

    // ── Assert transcript rendered ───────────────────────
    const utterances = page.locator('[data-testid="utterance-entry"]');
    const uttCount = await utterances.count();
    expect(uttCount).toBeGreaterThanOrEqual(1);
    console.log(`[robustness] Utterances visible: ${uttCount}`);

    // ── Assert divergence with camps renders ──────────────
    // seed-001 has a divergence point with 3 camps:
    //   - "完全开源" (p1)
    //   - "有限开源" (p3)
    //   - "有治理的开源" (p2, p4)
    await assertDivergenceWithCamps(page);

    const divCard = page.locator('[data-testid="divergence-card"]').first();
    await expect(divCard).toBeVisible({ timeout: 10_000 });

    // Assert camp positions are rendered (not empty/blank)
    const divText = await divCard.textContent();
    expect(divText).toContain('完全开源');
    expect(divText).toContain('有限开源');

    // ── Assert consensus also rendered ────────────────────
    const conCard = page.locator('[data-testid="consensus-card"]').first();
    await expect(conCard).toBeVisible({ timeout: 5_000 });
    const conText = await conCard.textContent();
    // seed-001 consensus: "与会专家一致认为需要建立AI开源的安全标准与治理框架"
    expect(conText).toBeTruthy();
    expect(conText!.length).toBeGreaterThan(20);

    // ── Assert panelist grid rendered ─────────────────────
    // Note: responsive layouts may render multiple host-section elements;
    // use first() to avoid strict mode violation
    const hostSection = page.locator('[data-testid="host-section"]').first();
    await expect(hostSection).toBeVisible();
    const expertSection = page.locator('[data-testid="experts-section"]').first();
    await expect(expertSection).toBeVisible();

    // ── Smoke: no React error boundary visible ─────────────
    // The page should not contain unstyled error text
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toMatch(/is not a function/);
    expect(bodyText).not.toMatch(/cannot read properties/i);
    expect(bodyText).not.toMatch(/Uncaught TypeError/i);
  });
});
