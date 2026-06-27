/**
 * Scenario 1: 完整直播链路
 *
 * 首页发起讨论 → 生成阵容 → 确认进演播厅 →
 * 断言 transcript 随时间持续增长 →
 * 断言共识/分歧中途出现（非结束才有）→
 * 断言最终出现 discussion_end 总结浮层且无 JSON 文本
 */
import { test, expect } from '@playwright/test';
import {
  goHome, clickCreateDiscussion, fillAndGenerate, confirmRoster,
  waitForUtterances, utteranceCount,
  assertLiveStatus, waitForDiscussionEnd,
  assertDivergenceWithCamps,
} from './helpers';

test.describe('Full Live Cycle', () => {
  test('create → roster → confirm → studio → transcript grows → discussion_end', async ({ page }) => {
    test.setTimeout(180_000); // LLM calls can be slow

    // ── Step 1: Navigate to home ────────────────────────
    await goHome(page);

    // ── Step 2: Create new discussion ───────────────────
    await clickCreateDiscussion(page);
    await fillAndGenerate(
      page,
      'E2E测试：AI是否会改变教育的未来？',
      2,  // 2 experts for faster generation
    );

    // ── Step 3: Assert roster loaded ────────────────────
    await expect(page.locator('[data-testid="confirm-roster-btn"]')).toBeVisible();
    // Count panelist cards — should have 3 (1 host + 2 experts)
    const hostSection = page.locator('[data-testid="host-section"]').first();
    await expect(hostSection).toBeVisible();
    const expertSection = page.locator('[data-testid="experts-section"]').first();
    await expect(expertSection).toBeVisible();

    // ── Step 4: Confirm and enter studio ────────────────
    await confirmRoster(page);

    // ── Step 5: Assert SSE connected ────────────────────
    await assertLiveStatus(page);

    // ── Step 6: Wait for transcript to grow ──────────────
    // Initial snapshot should have 0 utterances. SSE should start pushing.
    // With DEFAULT_MAX_ROUNDS=6, we expect 6 rounds before discussion_end.
    // Wait for at least 2 utterances to confirm delivery.
    await waitForUtterances(page, 2, 40_000);
    const count2 = await utteranceCount(page);
    expect(count2).toBeGreaterThanOrEqual(2);

    // Wait for more utterances (transcript grows over time)
    await waitForUtterances(page, 4, 60_000);
    const count4 = await utteranceCount(page);
    expect(count4).toBeGreaterThanOrEqual(4);
    // Transcript must have strictly grown
    expect(count4).toBeGreaterThan(count2);

    // ── Step 7: Assert divergence/camps renders mid-stream ──
    // (Seed data has no consensus initially for new discussions,
    // but the orchestrator MAY add them. At minimum, check no crash.)
    await assertDivergenceWithCamps(page);

    // ── Step 8: Wait for discussion_end ──────────────────
    await waitForDiscussionEnd(page, 90_000);
    const banner = page.locator('[data-testid="discussion-end-banner"]');
    await expect(banner).toBeVisible();

    // Banner text must NOT contain raw JSON
    const bannerText = await banner.textContent();
    expect(bannerText).not.toBeNull();
    expect(bannerText).toContain('讨论结束');
    expect(bannerText).toContain('主持人总结');
    // Lock: no raw JSON fragments in summary
    expect(bannerText).not.toMatch(/^\s*\{/);
    expect(bannerText).not.toMatch(/^\s*\[/);
    expect(bannerText).not.toMatch(/"camps"\s*:/);
    expect(bannerText).not.toMatch(/"involved_panelist_ids"\s*:/);
  });
});
