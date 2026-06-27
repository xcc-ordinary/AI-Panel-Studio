# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: full-live-cycle.spec.ts >> Full Live Cycle >> create → roster → confirm → studio → transcript grows → discussion_end
- Location: tests\e2e\full-live-cycle.spec.ts:18:3

# Error details

```
Test timeout of 180000ms exceeded.
```

```
Error: page.click: Test timeout of 180000ms exceeded.
Call log:
  - waiting for locator('[data-testid="expert-count-decrease"]')
    - locator resolved to <button disabled type="button" data-testid="expert-count-decrease" class="w-10 h-10 rounded-[var(--radius-sm)] text-lg font-medium cursor-pointer↵                                 transition-all duration-[var(--duration-fast)] disabled:opacity-30↵                                 hover:bg-[var(--border-accent)]">−</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not enabled
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not enabled
    - retrying click action
      - waiting 100ms
    341 × waiting for element to be visible, enabled and stable
        - element is not enabled
      - retrying click action
        - waiting 500ms

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - button "首页" [ref=e5] [cursor=pointer]
    - button "发起讨论" [ref=e6] [cursor=pointer]
    - button "SSE 调试" [ref=e7] [cursor=pointer]
  - generic [ref=e8]:
    - button "返回首页" [ref=e9] [cursor=pointer]:
      - img [ref=e10]
      - text: 返回首页
    - generic [ref=e12]:
      - generic [ref=e13]:
        - generic [ref=e14]:
          - img [ref=e15]
          - text: 演播厅
        - heading "发起一场 AI 圆桌讨论" [level=2] [ref=e18]:
          - text: 发起一场
          - text: AI 圆桌讨论
        - paragraph [ref=e19]: 输入话题，系统将自动生成一位主持人和多位立场各异的 AI 专家。 他们会在演播厅中展开一场自然的圆桌辩论——你只需观看。
        - generic [ref=e20]:
          - generic [ref=e21]:
            - img [ref=e22]
            - text: 2–8 位专家，各持不同立场
          - generic [ref=e27]:
            - img [ref=e28]
            - text: 主持人引导讨论，非机械轮流发言
      - generic [ref=e33]:
        - generic [ref=e34]:
          - generic [ref=e35]: 讨论话题
          - textbox "讨论话题" [ref=e36]:
            - /placeholder: 输入你感兴趣的话题…例如"AI 是否应该开源？"
            - text: E2E测试：AI是否会改变教育的未来？
          - paragraph [ref=e37]: 19/200 · 话题将经过内容审核
        - generic [ref=e38]:
          - generic [ref=e39]: 专家人数
          - generic [ref=e40]:
            - button "−" [disabled] [ref=e41] [cursor=pointer]
            - generic [ref=e42]: "2"
            - button "+" [ref=e43] [cursor=pointer]
            - generic [ref=e44]: 2–8 人，默认 4
          - paragraph [ref=e45]: 1 名主持人 + 2 名专家，各持不同立场
        - button "生成嘉宾阵容" [ref=e46] [cursor=pointer]:
          - img [ref=e47]
          - text: 生成嘉宾阵容
```

# Test source

```ts
  1   | /**
  2   |  * E2E test helpers: shared page actions and assertions.
  3   |  */
  4   | import type { Page } from '@playwright/test';
  5   | 
  6   | // ── Navigation ──────────────────────────────────────────────────
  7   | 
  8   | export async function goHome(page: Page) {
  9   |   await page.goto('/');
  10  |   await page.waitForSelector('[data-testid="create-discussion-btn"]', { timeout: 10_000 });
  11  |   // Wait for at least one discussion card to load (REST API)
  12  |   await page.waitForSelector('[data-testid="discussion-card"]', { timeout: 15_000 }).catch(() => {
  13  |     console.log('[helpers] No discussion cards found — page may be empty or still loading');
  14  |   });
  15  | }
  16  | 
  17  | export async function clickCreateDiscussion(page: Page) {
  18  |   await page.click('[data-testid="create-discussion-btn"]');
  19  |   await page.waitForSelector('[data-testid="topic-input"]', { timeout: 5_000 });
  20  | }
  21  | 
  22  | export async function fillAndGenerate(page: Page, topic: string, expertCount = 2) {
  23  |   await page.fill('[data-testid="topic-input"]', topic);
  24  |   // Adjust expert count if needed
  25  |   const currentCount = await page.textContent('span.text-xl.font-bold');
  26  |   if (currentCount) {
  27  |     const cur = parseInt(currentCount, 10);
  28  |     while (cur > expertCount) {
> 29  |       await page.click('[data-testid="expert-count-decrease"]');
      |                  ^ Error: page.click: Test timeout of 180000ms exceeded.
  30  |     }
  31  |     while (cur < expertCount) {
  32  |       await page.click('[data-testid="expert-count-increase"]');
  33  |     }
  34  |   }
  35  |   await page.click('[data-testid="generate-panelists-btn"]');
  36  |   // Wait for roster page
  37  |   await page.waitForSelector('[data-testid="confirm-roster-btn"]', { timeout: 30_000 });
  38  | }
  39  | 
  40  | export async function confirmRoster(page: Page) {
  41  |   await page.click('[data-testid="confirm-roster-btn"]');
  42  |   // Wait for studio view
  43  |   await page.waitForSelector('[data-testid="connection-status"]', { timeout: 10_000 });
  44  | }
  45  | 
  46  | // ── Studio assertions ───────────────────────────────────────────
  47  | 
  48  | /** Wait for at least N utterances to appear in the transcript panel. */
  49  | export async function waitForUtterances(page: Page, minCount: number, timeoutMs = 30_000) {
  50  |   await page.waitForFunction(
  51  |     (n) => document.querySelectorAll('[data-testid="utterance-entry"]').length >= n,
  52  |     minCount,
  53  |     { timeout: timeoutMs },
  54  |   );
  55  | }
  56  | 
  57  | /** Count current utterance entries visible on the page. */
  58  | export async function utteranceCount(page: Page): Promise<number> {
  59  |   return page.locator('[data-testid="utterance-entry"]').count();
  60  | }
  61  | 
  62  | /** Assert connection status shows "直播中" (live). */
  63  | export async function assertLiveStatus(page: Page) {
  64  |   await page.waitForSelector('[data-testid="connection-status"]', { timeout: 10_000 });
  65  |   const text = await page.textContent('[data-testid="connection-status"]');
  66  |   if (!text?.includes('直播中')) {
  67  |     throw new Error(`Expected "直播中", got "${text}"`);
  68  |   }
  69  | }
  70  | 
  71  | /** Wait for discussion end banner. */
  72  | export async function waitForDiscussionEnd(page: Page, timeoutMs = 120_000) {
  73  |   await page.waitForSelector('[data-testid="discussion-end-banner"]', { timeout: timeoutMs });
  74  | }
  75  | 
  76  | /** Assert consensus cards are visible. */
  77  | export async function assertConsensusVisible(page: Page) {
  78  |   const count = await page.locator('[data-testid="consensus-card"]').count();
  79  |   if (count === 0) {
  80  |     // May not exist yet — just check no crash
  81  |     const consensusText = await page.textContent('section:has(h3)');
  82  |     if (consensusText?.includes('暂无共识')) {
  83  |       return; // Empty state is OK
  84  |     }
  85  |   }
  86  | }
  87  | 
  88  | /** Assert divergence cards are visible with camps rendered. */
  89  | export async function assertDivergenceWithCamps(page: Page) {
  90  |   const count = await page.locator('[data-testid="divergence-card"]').count();
  91  |   if (count > 0) {
  92  |     // Assert camps text is rendered (not white screen from (d.camps||[]).map crash)
  93  |     const card = page.locator('[data-testid="divergence-card"]').first();
  94  |     const text = await card.textContent();
  95  |     if (!text || text.length < 10) {
  96  |       throw new Error('Divergence card has no text content — possible crash');
  97  |     }
  98  |   }
  99  | }
  100 | 
  101 | // ── Multi-discussion helpers ────────────────────────────────────
  102 | 
  103 | /** Join an existing discussion by its seed ID (navigating from home page by clicking its card). */
  104 | export async function joinDiscussion(page: Page, discussionId: string) {
  105 |   const card = page.locator(`[data-discussion-id="${discussionId}"]`);
  106 |   await card.waitFor({ state: 'visible', timeout: 10_000 });
  107 |   await card.click();
  108 |   // Wait for studio view to render (connection-status appears after loading)
  109 |   await page.waitForSelector('[data-testid="connection-status"]', { timeout: 15_000 });
  110 | }
  111 | 
  112 | /** Get all speaker names from utterance entries on the page. */
  113 | export async function getUtteranceSpeakers(page: Page): Promise<string[]> {
  114 |   const names = await page.locator('[data-testid="utterance-entry"] span.font-semibold').allTextContents();
  115 |   return names;
  116 | }
  117 | 
```