/**
 * Scenario 2: 投递活性
 *
 * 进入 in_progress 讨论后，断言前端在 N 秒内收到的 utterance 数量 > 初始 snapshot 数。
 * 锁死"后端在产、前端收得到"，防投递断链复发。
 *
 * Uses seed-001-ai-open-source (8 pre-existing utterances).
 * On SSE connect, the orchestrator auto-spawns and continues from round 8.
 */
import { test, expect } from '@playwright/test';
import { goHome, joinDiscussion, waitForUtterances, utteranceCount } from './helpers';

test.describe('Delivery Liveness', () => {
  test('utterances grow beyond initial snapshot within time limit', async ({ page }) => {
    test.setTimeout(90_000);

    // ── Navigate & join seed-001 ────────────────────────
    await goHome(page);
    await joinDiscussion(page, 'seed-001-ai-open-source');

    // ── Wait for initial snapshot to load ────────────────
    // seed-001 has 8 utterances pre-loaded. The initial REST GET /transcript
    // returns them; then SSE incremental adds new ones.
    // Wait for initial rendering
    await page.waitForTimeout(2_000);

    const initialCount = await utteranceCount(page);
    expect(initialCount).toBeGreaterThanOrEqual(1);
    console.log(`[liveness] Initial utterance count: ${initialCount}`);

    // ── Wait N seconds, then check growth ────────────────
    // Orchestrator spawns on SSE connect, continues from round 8.
    // New utterances should appear within 30 seconds.
    await waitForUtterances(page, initialCount + 2, 35_000);

    const finalCount = await utteranceCount(page);
    console.log(`[liveness] Final utterance count: ${finalCount}`);

    // ── Critical assertion: growth happened ──────────────
    expect(finalCount).toBeGreaterThan(initialCount);
    // At least 2 new utterances received
    expect(finalCount - initialCount).toBeGreaterThanOrEqual(2);
  });
});
