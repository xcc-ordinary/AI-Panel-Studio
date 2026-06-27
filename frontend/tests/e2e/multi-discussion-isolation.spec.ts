/**
 * Scenario 4: 多讨论隔离
 *
 * 并行打开两场种子讨论（seed-002-remote-work + seed-003-cars），
 * 断言各自 transcript 不串台——每个 panelist 只属于一场讨论。
 */
import { test, expect } from '@playwright/test';
import { goHome, joinDiscussion, getUtteranceSpeakers } from './helpers';

test.describe('Multi-Discussion Isolation', () => {
  test('two parallel discussions do not cross-contaminate transcripts', async ({ browser }) => {
    test.setTimeout(90_000);

    // ── Open two isolated contexts ───────────────────────
    const ctx1 = await browser.newContext();
    const ctx2 = await browser.newContext();

    // ── Load both pages in parallel ──────────────────────
    const page1 = await ctx1.newPage();
    const page2 = await ctx2.newPage();

    await Promise.all([
      (async () => {
        await goHome(page1);
        await page1.waitForTimeout(1_000);
        await joinDiscussion(page1, 'seed-002-remote-work');
      })(),
      (async () => {
        await goHome(page2);
        await page2.waitForTimeout(1_000);
        await joinDiscussion(page2, 'seed-003-cars');
      })(),
    ]);

    // Wait for transcript to populate
    await page1.waitForTimeout(3_000);
    await page2.waitForTimeout(3_000);

    // ── Get speakers from each page ──────────────────────
    const speakers1 = await getUtteranceSpeakers(page1);
    const speakers2 = await getUtteranceSpeakers(page2);

    console.log(`[isolation] Discussion 1 speakers: ${speakers1.join(', ')}`);
    console.log(`[isolation] Discussion 2 speakers: ${speakers2.join(', ')}`);

    // ── Identity assertions ──────────────────────────────
    const seed002Names = ['刘思辨', '孙远程', '周管理', '吴效率'];
    const seed003Names = ['林对话', '马交通', '郑自由', '黄绿能'];

    // Every speaker in page 1 must belong to seed-002
    for (const name of speakers1) {
      expect(seed002Names).toContain(name);
    }
    // Every speaker in page 2 must belong to seed-003
    for (const name of speakers2) {
      expect(seed003Names).toContain(name);
    }

    // No cross-contamination
    for (const name of seed003Names) {
      expect(speakers1).not.toContain(name);
    }
    for (const name of seed002Names) {
      expect(speakers2).not.toContain(name);
    }

    await ctx1.close();
    await ctx2.close();
  });
});
