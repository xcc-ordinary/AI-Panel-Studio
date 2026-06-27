# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: sse-reconnection.spec.ts >> SSE Reconnection >> reconnect via snapshot + replay preserves all utterances without dupes
- Location: tests\e2e\sse-reconnection.spec.ts:20:3

# Error details

```
TimeoutError: page.waitForFunction: Timeout 40000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - button "首页" [ref=e5] [cursor=pointer]
    - button "发起讨论" [ref=e6] [cursor=pointer]
    - button "SSE 调试" [ref=e7] [cursor=pointer]
  - generic [ref=e8]:
    - banner [ref=e9]:
      - generic [ref=e10]:
        - button "返回首页" [ref=e11] [cursor=pointer]:
          - img [ref=e12]
        - heading "预制菜该不该进校园？" [level=1] [ref=e14]
      - generic [ref=e15]:
        - generic [ref=e16]: 直播中
        - button "结束讨论" [ref=e18] [cursor=pointer]
    - generic [ref=e19]:
      - complementary [ref=e20]:
        - generic [ref=e21]:
          - generic [ref=e22]:
            - paragraph [ref=e23]:
              - img [ref=e24]
              - text: 主持人
            - generic [ref=e26]:
              - generic [ref=e27]:
                - generic [ref=e29]: 陈主持
                - generic [ref=e30]: 主持
              - paragraph [ref=e31]: 教育话题主持人
              - generic "待发言" [ref=e33]:
                - generic [ref=e35]: 待发言
              - generic [ref=e37]: · 厘清预制菜的定义和标准
          - generic [ref=e38]:
            - paragraph [ref=e39]: 专家 · 3 人
            - generic [ref=e40]:
              - generic [ref=e41]:
                - generic [ref=e44]: 何食品
                - paragraph [ref=e45]: 食品安全专家
                - generic "待发言" [ref=e47]:
                  - generic [ref=e49]: 待发言
                - generic [ref=e51]: · 预制菜国标的落实情况
              - generic [ref=e52]:
                - generic [ref=e55]: 吕家长
                - paragraph [ref=e56]: 家长代表、营养学博士
                - generic "待发言" [ref=e58]:
                  - generic [ref=e60]: 待发言
                - generic [ref=e62]: · 预制菜的维生素流失数据
              - generic [ref=e63]:
                - generic [ref=e66]: 钱供应
                - paragraph [ref=e67]: 团餐供应链管理者
                - generic "沉默" [ref=e69]:
                  - generic [ref=e71]: 沉默
      - main [ref=e72]:
        - heading "现场 Transcript" [level=2] [ref=e73]
        - generic [ref=e74]:
          - generic [ref=e75]:
            - generic [ref=e76]:
              - generic [ref=e77]: 陈主持
              - generic [ref=e78]: 教育话题主持人
            - paragraph [ref=e79]: 预制菜进校园引发了广泛争议。家长们担心营养和安全，学校面临成本压力。何食品专家，从食品安全的角度看，预制菜到底安不安全？
          - generic [ref=e80]:
            - generic [ref=e81]:
              - generic [ref=e82]: 何食品
              - generic [ref=e83]: 食品安全专家
            - paragraph [ref=e84]: 这是一个误区。规范生产的预制菜在微生物指标上往往优于现场制作，因为工业化的冷链和灭菌流程更加可控。问题出在监管执行，不是产品本身。
          - generic [ref=e85]:
            - generic [ref=e86]:
              - generic [ref=e87]: 吕家长
              - generic [ref=e88]: 家长代表、营养学博士
            - paragraph [ref=e89]: 安全不等于营养。我们的检测数据显示，预制菜经过高温灭菌后，维生素C损失高达60%。对于正在发育的孩子，这不是小问题。
      - complementary [ref=e90]:
        - generic [ref=e91]:
          - generic [ref=e92]:
            - heading "已形成共识" [level=3] [ref=e93]:
              - img [ref=e94]
              - text: 已形成共识
            - generic [ref=e98]:
              - paragraph [ref=e99]: 与会专家一致认为预制菜进校园的前提是建立严格的营养与安全标准体系
              - generic [ref=e100]:
                - generic [ref=e101]: 何食品
                - generic [ref=e102]: 吕家长
                - generic [ref=e103]: 钱供应
          - generic [ref=e104]:
            - heading "存在分歧" [level=3] [ref=e105]:
              - img [ref=e106]
              - text: 存在分歧
            - generic [ref=e109]:
              - paragraph [ref=e110]: 在「校园是否应该完全禁止预制菜」上产生根本分歧：食品安全专家认为应看标准，家长代表认为应全面使用新鲜食材
              - generic [ref=e111]:
                - paragraph [ref=e112]: 建立标准后准入
                - generic [ref=e113]:
                  - generic [ref=e114]: 何食品
                  - generic [ref=e115]: 钱供应
              - generic [ref=e116]:
                - paragraph [ref=e117]: 校园应全面使用新鲜食材
                - generic [ref=e119]: 吕家长
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
  29  |       await page.click('[data-testid="expert-count-decrease"]');
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
> 50  |   await page.waitForFunction(
      |              ^ TimeoutError: page.waitForFunction: Timeout 40000ms exceeded.
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