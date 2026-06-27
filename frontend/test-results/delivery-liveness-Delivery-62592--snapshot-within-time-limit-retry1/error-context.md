# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: delivery-liveness.spec.ts >> Delivery Liveness >> utterances grow beyond initial snapshot within time limit
- Location: tests\e2e\delivery-liveness.spec.ts:14:3

# Error details

```
TimeoutError: page.waitForFunction: Timeout 35000ms exceeded.
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
        - heading "AI是否应该开源？" [level=1] [ref=e14]
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
                - generic [ref=e29]: 张明远
                - generic [ref=e30]: 主持
              - paragraph [ref=e31]: 科技媒体主编
              - generic "发言中" [ref=e33]:
                - generic [ref=e35]: 发言中
              - generic [ref=e36]:
                - generic [ref=e37]: · 引导讨论节奏
                - generic [ref=e38]: · 确保各方观点得到表达
          - generic [ref=e39]:
            - paragraph [ref=e40]: 专家 · 4 人
            - generic [ref=e41]:
              - generic [ref=e42]:
                - generic [ref=e45]: 李开放
                - paragraph [ref=e46]: 开源社区领袖
                - generic "待发言" [ref=e48]:
                  - generic [ref=e50]: 待发言
                - generic [ref=e52]: · 关注开源生态的可持续性
              - generic [ref=e53]:
                - generic [ref=e56]: 陈安全
                - paragraph [ref=e57]: 网络安全专家
                - generic "待发言" [ref=e59]:
                  - generic [ref=e61]: 待发言
                - generic [ref=e63]: · 开源模型的安全审计机制
              - generic [ref=e64]:
                - generic [ref=e67]: 王商业
                - paragraph [ref=e68]: AI企业CEO
                - generic "沉默" [ref=e70]:
                  - generic [ref=e72]: 沉默
              - generic [ref=e73]:
                - generic [ref=e76]: 赵伦理
                - paragraph [ref=e77]: 科技伦理学者
                - generic "待发言" [ref=e79]:
                  - generic [ref=e81]: 待发言
                - generic [ref=e83]: · AI治理的国际协调机制
      - main [ref=e84]:
        - heading "现场 Transcript" [level=2] [ref=e85]
        - generic [ref=e86]:
          - generic [ref=e87]:
            - generic [ref=e88]:
              - generic [ref=e89]: 张明远
              - generic [ref=e90]: 科技媒体主编
            - paragraph [ref=e91]: 欢迎各位来到今天的圆桌讨论。今天的话题是：AI是否应该开源？我们有四位来自不同领域的专家。李开放先生，您先来谈谈？
          - generic [ref=e92]:
            - generic [ref=e93]:
              - generic [ref=e94]: 李开放
              - generic [ref=e95]: 开源社区领袖
            - paragraph [ref=e96]: 开源是AI创新的生命线。如果每家公司都把模型锁在保险柜里，我们永远无法建立一个健康的AI生态。
          - generic [ref=e97]:
            - generic [ref=e98]:
              - generic [ref=e99]: 陈安全
              - generic [ref=e100]: 网络安全专家
            - paragraph [ref=e101]: 我补充一点：开源确实有助于安全审计。我们最近发现的一个关键漏洞，正是因为模型的代码是公开的，才被及时发现并修复。
          - generic [ref=e102]:
            - generic [ref=e103]:
              - generic [ref=e104]: 王商业
              - generic [ref=e105]: AI企业CEO
            - paragraph [ref=e106]: 但公司的研发投入需要回报。完全开源意味着任何人都可以复制我们的成果，这会打击企业创新的积极性。
          - generic [ref=e107]:
            - generic [ref=e108]:
              - generic [ref=e109]: 赵伦理
              - generic [ref=e110]: 科技伦理学者
            - paragraph [ref=e111]: 我们需要跳出二元思维。问题不是该不该开源，而是如何建立一套全球性的AI治理框架，让开源的益处最大化、风险最小化。
          - generic [ref=e112]:
            - generic [ref=e113]:
              - generic [ref=e114]: 张明远
              - generic [ref=e115]: 科技媒体主编
            - paragraph [ref=e116]: 赵伦理学者提到了治理框架，这个观点很有意思。李开放，您觉得开源社区能接受某种形式的监管吗？
          - generic [ref=e117]:
            - generic [ref=e118]:
              - generic [ref=e119]: 李开放
              - generic [ref=e120]: 开源社区领袖
            - paragraph [ref=e121]: 监管不等于封杀。如果监管框架是由社区共同制定的，我想开源社区是愿意参与的。关键在于透明和参与。
          - generic [ref=e122]:
            - generic [ref=e123]:
              - generic [ref=e124]: 陈安全
              - generic [ref=e125]: 网络安全专家
            - paragraph [ref=e126]: 同意。我们可以在开源社区内部先建立安全标准，再向监管机构证明自我规制的可行性，而不是等外部强加规则。
          - generic [ref=e127]:
            - generic [ref=e128]:
              - generic [ref=e129]: 王商业
              - generic [ref=e130]: AI企业CEO
            - paragraph [ref=e131]: 自我规制听起来不错，但历史证明，缺乏强制力的自愿标准往往形同虚设。企业投入巨资研发，凭什么要相信竞争者的善意？
          - generic [ref=e132]:
            - generic [ref=e133]:
              - generic [ref=e134]: 赵伦理
              - generic [ref=e135]: 科技伦理学者
            - paragraph [ref=e136]: 王务实先生的观点其实触及了信任问题。我们能否设计一种机制，让企业既能保护核心资产，又能参与开源社区？
          - generic [ref=e137]:
            - generic [ref=e138]:
              - generic [ref=e139]: 赵伦理
              - generic [ref=e140]: 科技伦理学者
            - paragraph [ref=e141]: 王务实先生，您提到信任问题。那么您认为什么样的机制能让企业愿意共享核心资产？
          - generic [ref=e142]:
            - generic [ref=e143]:
              - generic [ref=e144]: 王商业
              - generic [ref=e145]: AI企业CEO
            - paragraph [ref=e146]: 共享核心资产？除非有法律保障和补偿机制，否则企业不可能冒这个风险。
          - generic [ref=e147]:
            - generic [ref=e148]:
              - generic [ref=e149]: 李开放
              - generic [ref=e150]: 开源社区领袖
            - paragraph [ref=e151]: 我同意需要法律保障，但我们可以从部分开源开始，比如公开训练方法和评估数据，这样既能促进研究，又能保护核心资产。
          - generic [ref=e152]:
            - generic [ref=e153]:
              - generic [ref=e154]: 张明远
              - generic [ref=e155]: 科技媒体主编
            - paragraph [ref=e156]: 各位专家，我们讨论了开源与监管的平衡，但似乎还缺少对全球治理框架具体设计的探讨。赵伦理学者，您能进一步阐述您设想的治理框架吗？
          - generic [ref=e157]:
            - generic [ref=e158]:
              - generic [ref=e159]: 陈安全
              - generic [ref=e160]: 网络安全专家
            - paragraph [ref=e161]: 我同意需要法律保障，但我们可以从部分开源开始，比如公开训练方法和评估数据，这样既能促进研究，又能保护核心资产。
          - generic [ref=e162]:
            - generic [ref=e163]:
              - generic [ref=e164]: 陈安全
              - generic [ref=e165]: 网络安全专家
            - paragraph [ref=e166]: 赵伦理学者，您刚才被主持人点名，但未回应。能否具体谈谈您设想的全球治理框架？
          - generic [ref=e167]:
            - generic [ref=e168]:
              - generic [ref=e169]: 赵伦理
              - generic [ref=e170]: 科技伦理学者
            - paragraph [ref=e171]: 感谢点名。我设想的全球治理框架包括一个多方利益相关者委员会，负责制定开源AI的安全标准，并建立争议仲裁机制。
          - generic [ref=e172]:
            - generic [ref=e173]:
              - generic [ref=e174]: 王商业
              - generic [ref=e175]: AI企业CEO
            - paragraph [ref=e176]: 王务实先生，您对赵伦理学者提出的多方利益相关者委员会有何看法？您认为这样的机制能解决您担心的信任问题吗？
          - generic [ref=e177]:
            - generic [ref=e178]:
              - generic [ref=e179]: 李开放
              - generic [ref=e180]: 开源社区领袖
            - paragraph [ref=e181]: 我完全同意赵学者的观点，但我想补充一点：委员会应包含开源社区代表，以确保标准不会扼杀创新。
          - generic [ref=e182]:
            - generic [ref=e183]:
              - generic [ref=e184]: 张明远
              - generic [ref=e185]: 科技媒体主编
            - paragraph [ref=e186]: 感谢各位的精彩讨论。我们听到了关于委员会构成的建议，那么如何确保这个委员会在全球范围内具有执行力和公信力呢？
          - generic [ref=e187]:
            - generic [ref=e188]:
              - generic [ref=e189]: 陈安全
              - generic [ref=e190]: 网络安全专家
            - paragraph [ref=e191]: 我同意需要法律保障，但我们可以从部分开源开始，比如公开训练方法和评估数据，这样既能促进研究，又能保护核心资产。
          - generic [ref=e192]:
            - generic [ref=e193]:
              - generic [ref=e194]: 陈安全
              - generic [ref=e195]: 网络安全专家
            - paragraph [ref=e196]: 我不同意完全由委员会制定标准，开源社区的自发标准往往更灵活有效。
          - generic [ref=e197]:
            - generic [ref=e198]:
              - generic [ref=e199]: 赵伦理
              - generic [ref=e200]: 科技伦理学者
            - paragraph [ref=e201]: 您提出的委员会如何确保全球范围内的执行力和公信力？是否需要联合国或类似机构的背书？
          - generic [ref=e202]:
            - generic [ref=e203]:
              - generic [ref=e204]: 王商业
              - generic [ref=e205]: AI企业CEO
            - paragraph [ref=e206]: 我注意到大家讨论了很多委员会和标准，但我想回到务实角度：如果核心模型不开源，工具链开源能否同样实现安全审计？
          - generic [ref=e207]:
            - generic [ref=e208]:
              - generic [ref=e209]: 李开放
              - generic [ref=e210]: 开源社区领袖
            - paragraph [ref=e211]: 我注意到工具链开源的提议很有价值，但我想强调，如果核心模型完全闭源，安全审计可能流于表面。
          - generic [ref=e212]:
            - generic [ref=e213]:
              - generic [ref=e214]: 张明远
              - generic [ref=e215]: 科技媒体主编
            - paragraph [ref=e216]: 感谢各位的深入讨论。我们听到了关于委员会构成、法律保障和工具链开源的多种观点，那么这些方案如何在实际中平衡创新与安全？
          - generic [ref=e217]:
            - generic [ref=e218]:
              - generic [ref=e219]: 陈安全
              - generic [ref=e220]: 网络安全专家
            - paragraph [ref=e221]: 我不同意完全由委员会制定标准，开源社区的自发标准往往更灵活有效。
          - generic [ref=e222]:
            - generic [ref=e223]:
              - generic [ref=e224]: 赵伦理
              - generic [ref=e225]: 科技伦理学者
            - paragraph [ref=e226]: 您提到开源社区的自发标准更灵活，但如何保证这些标准在全球范围内被采纳并具备公信力？
          - generic [ref=e227]:
            - generic [ref=e228]:
              - generic [ref=e229]: 王商业
              - generic [ref=e230]: AI企业CEO
            - paragraph [ref=e231]: 我理解对标准公信力的担忧，但我们可以先推动工具链开源，积累实际经验后再逐步扩展。
      - complementary [ref=e232]:
        - generic [ref=e233]:
          - generic [ref=e234]:
            - heading "已形成共识" [level=3] [ref=e235]:
              - img [ref=e236]
              - text: 已形成共识
            - generic [ref=e240]:
              - paragraph [ref=e241]: 与会专家一致认为需要建立AI开源的安全标准与治理框架
              - generic [ref=e242]:
                - generic [ref=e243]: 李开放
                - generic [ref=e244]: 陈安全
                - generic [ref=e245]: 赵伦理
          - generic [ref=e246]:
            - heading "存在分歧" [level=3] [ref=e247]:
              - img [ref=e248]
              - text: 存在分歧
            - generic [ref=e251]:
              - paragraph [ref=e252]: 关于开源程度的根本分歧：一方主张完全开源，另一方认为核心模型应保留商业壁垒
              - generic [ref=e253]:
                - paragraph [ref=e254]: 完全开源
                - generic [ref=e256]: 李开放
              - generic [ref=e257]:
                - paragraph [ref=e258]: 有限开源
                - generic [ref=e260]: 王商业
              - generic [ref=e261]:
                - paragraph [ref=e262]: 有治理的开源
                - generic [ref=e263]:
                  - generic [ref=e264]: 陈安全
                  - generic [ref=e265]: 赵伦理
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
      |              ^ TimeoutError: page.waitForFunction: Timeout 35000ms exceeded.
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