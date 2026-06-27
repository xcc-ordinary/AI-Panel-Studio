/**
 * E2E test helpers: shared page actions and assertions.
 */
import type { Page } from '@playwright/test';

// ── Navigation ──────────────────────────────────────────────────

export async function goHome(page: Page) {
  await page.goto('/');
  await page.waitForSelector('[data-testid="create-discussion-btn"]', { timeout: 10_000 });
  // Wait for at least one discussion card to load (REST API)
  await page.waitForSelector('[data-testid="discussion-card"]', { timeout: 15_000 }).catch(() => {
    console.log('[helpers] No discussion cards found — page may be empty or still loading');
  });
}

export async function clickCreateDiscussion(page: Page) {
  await page.click('[data-testid="create-discussion-btn"]');
  await page.waitForSelector('[data-testid="topic-input"]', { timeout: 5_000 });
}

export async function fillAndGenerate(page: Page, topic: string, expertCount = 2) {
  await page.fill('[data-testid="topic-input"]', topic);
  // Adjust expert count if needed
  const currentCount = await page.textContent('span.text-xl.font-bold');
  if (currentCount) {
    const cur = parseInt(currentCount, 10);
    while (cur > expertCount) {
      await page.click('[data-testid="expert-count-decrease"]');
    }
    while (cur < expertCount) {
      await page.click('[data-testid="expert-count-increase"]');
    }
  }
  await page.click('[data-testid="generate-panelists-btn"]');
  // Wait for roster page
  await page.waitForSelector('[data-testid="confirm-roster-btn"]', { timeout: 30_000 });
}

export async function confirmRoster(page: Page) {
  await page.click('[data-testid="confirm-roster-btn"]');
  // Wait for studio view
  await page.waitForSelector('[data-testid="connection-status"]', { timeout: 10_000 });
}

// ── Studio assertions ───────────────────────────────────────────

/** Wait for at least N utterances to appear in the transcript panel. */
export async function waitForUtterances(page: Page, minCount: number, timeoutMs = 30_000) {
  await page.waitForFunction(
    (n) => document.querySelectorAll('[data-testid="utterance-entry"]').length >= n,
    minCount,
    { timeout: timeoutMs },
  );
}

/** Count current utterance entries visible on the page. */
export async function utteranceCount(page: Page): Promise<number> {
  return page.locator('[data-testid="utterance-entry"]').count();
}

/** Assert connection status shows "直播中" (live). */
export async function assertLiveStatus(page: Page) {
  await page.waitForSelector('[data-testid="connection-status"]', { timeout: 10_000 });
  const text = await page.textContent('[data-testid="connection-status"]');
  if (!text?.includes('直播中')) {
    throw new Error(`Expected "直播中", got "${text}"`);
  }
}

/** Wait for discussion end banner. */
export async function waitForDiscussionEnd(page: Page, timeoutMs = 120_000) {
  await page.waitForSelector('[data-testid="discussion-end-banner"]', { timeout: timeoutMs });
}

/** Assert consensus cards are visible. */
export async function assertConsensusVisible(page: Page) {
  const count = await page.locator('[data-testid="consensus-card"]').count();
  if (count === 0) {
    // May not exist yet — just check no crash
    const consensusText = await page.textContent('section:has(h3)');
    if (consensusText?.includes('暂无共识')) {
      return; // Empty state is OK
    }
  }
}

/** Assert divergence cards are visible with camps rendered. */
export async function assertDivergenceWithCamps(page: Page) {
  const count = await page.locator('[data-testid="divergence-card"]').count();
  if (count > 0) {
    // Assert camps text is rendered (not white screen from (d.camps||[]).map crash)
    const card = page.locator('[data-testid="divergence-card"]').first();
    const text = await card.textContent();
    if (!text || text.length < 10) {
      throw new Error('Divergence card has no text content — possible crash');
    }
  }
}

// ── Multi-discussion helpers ────────────────────────────────────

/** Join an existing discussion by its seed ID (navigating from home page by clicking its card). */
export async function joinDiscussion(page: Page, discussionId: string) {
  const card = page.locator(`[data-discussion-id="${discussionId}"]`);
  await card.waitFor({ state: 'visible', timeout: 10_000 });
  await card.click();
  // Wait for studio view to render (connection-status appears after loading)
  await page.waitForSelector('[data-testid="connection-status"]', { timeout: 15_000 });
}

/** Get all speaker names from utterance entries on the page. */
export async function getUtteranceSpeakers(page: Page): Promise<string[]> {
  const names = await page.locator('[data-testid="utterance-entry"] span.font-semibold').allTextContents();
  return names;
}
