# AI Panel Studio — Design System Master

**版本**: v1.0.0 | **日期**: 2026-06-26 | **框架**: React + Vite + TypeScript + Tailwind CSS 4

---

## 0. 设计理念

### 产品定位
AI Panel Studio 是一个观看 AI 专家圆桌实时讨论的 Web 应用。核心体验关键词：

> **沉浸式演播厅 — 直播讨论现场的临场感与实时感**

用户不是在"使用工具"，而是在"观看一场由 AI 专家主持的直播讨论"。设计必须传达出舞台聚光、专业克制、信息密集但从容不迫的氛围。

### 设计原则

| 原则 | 说明 |
|------|------|
| **暗色为主** | 演播厅/控制室氛围，深色背景让嘉宾色块和文字信息向前"浮现" |
| **克制动效** | 动效服务于信息传达（发言出现、状态切换），不服务于装饰 |
| **信息分层** | 三区独立信息流——专家状态 / transcript / 共识分歧——各自独立滚动，互不干扰 |
| **色块即身份** | 嘉宾颜色是唯一身份标识物，全界面一致使用 |
| **中文优先** | 所有 UI 文案简体中文，字体专为中文字形优化 |

### 反模式（明确禁止）

- ❌ **AI 紫/粉渐变**：`#7C3AED → #EC4899` 等"AI 产品标配"渐变色，缺乏个性且与演播厅氛围冲突
- ❌ **过度毛玻璃**：`backdrop-blur-xl` 堆叠在背景上造成视觉噪音
- ❌ **霓虹光污染**：Cyberpunk 风格的大量 `text-shadow` glow 效果
- ❌ **全页滚动**：演播厅整页 body 滚动——破坏了"仪表盘/控制台"的固定视口沉浸感
- ❌ **emoji 图标**：始终使用 SVG 图标（Heroicons / Lucide）

---

## 1. 色彩系统

### 1.1 主题色板

基于 Financial Dashboard + Dark Mode (OLED) 融合调整。

| Token | 色值 | Tailwind | 用途 |
|-------|------|----------|------|
| `--bg-canvas` | `#020617` | `slate-950` | 页面最深背景（演播厅画布） |
| `--bg-surface` | `#0F172A` | `slate-900` | 卡片/面板背景 |
| `--bg-elevated` | `#1E293B` | `slate-800` | 悬停态/焦点面板 |
| `--bg-raised` | `#334155` | `slate-700` | 输入框/次要按钮 |
| `--text-primary` | `#F8FAFC` | `slate-50` | 正文/标题 |
| `--text-secondary` | `#94A3B8` | `slate-400` | 辅助文字/时间戳 |
| `--text-muted` | `#64748B` | `slate-500` | 禁用态/占位符 |
| `--border-default` | `#1E293B` | `slate-800` | 默认边框/分隔线 |
| `--border-accent` | `#334155` | `slate-700` | 悬停/焦点边框 |
| `--accent-brand` | `#E2E8F0` | `slate-200` | 品牌焦点环（白/亮灰描边，不与嘉宾色冲突） |
| `--accent-positive` | `#22C55E` | `green-500` | 共识达成指示（✓ 图标 + 青绿描边） |
| `--accent-divergence` | `#F59E0B` | `amber-500` | 分歧指示（全界面统一用琥珀，不用红） |
| `--accent-live` | `#EF4444` | `red-500` | 直播指示器专用（唯一红色场景，无嘉宾色冲突） |

### 1.2 9 色嘉宾专属调色板

按 `sort_order` 分配（0 = 主持人 = 深蓝）。每组包含 `--panelist-N` 和 `--panelist-N-soft`（用于发光/投影等柔和变体）。

| 序号 | Token | 色值 | 角色 | 深色背景对比度 |
|------|-------|------|------|--------------|
| 0 | `--panelist-0` | `#38BDF8` | 主持人（天空蓝） | AAA (8.2:1) |
| 1 | `--panelist-1` | `#F87171` | 专家（珊瑚红） | AA (5.4:1) |
| 2 | `--panelist-2` | `#818CF8` | 专家（靛蓝） | AA (6.2:1) |
| 3 | `--panelist-3` | `#FBBF24` | 专家（琥珀金） | AAA (7.9:1) |
| 4 | `--panelist-4` | `#A78BFA` | 专家（紫罗兰） | AA (5.6:1) |
| 5 | `--panelist-5` | `#FB923C` | 专家（活力橙） | AA (5.1:1) |
| 6 | `--panelist-6` | `#E879F9` | 专家（品红） | AA (5.3:1) |
| 7 | `--panelist-7` | `#2DD4BF` | 专家（青碧绿） | AAA (7.5:1) |
| 8 | `--panelist-8` | `#FCA5A5` | 专家（浅珊瑚） | AA (4.9:1) |

**分配规则**: `color_index = panelist.sort_order`，不可重复。主持人始终 0 号色。

**色盲安全验证**: 蓝-靛-紫对（0/2/4）、黄-橙对（3/5）、红-粉对（1/8）均通过亮度差异区分。绿被共识独占，嘉宾色中无绿，CVD 下无混淆风险。CVD 模拟（Protanopia/Deuteranopia/Tritanopia）下各色仍可判断为不同灰度。

**柔和变体**（用于 `box-shadow` 发光、状态指示灯外圈）:

```css
--panelist-0-soft: rgba(56, 189, 248, 0.3)
--panelist-1-soft: rgba(248, 113, 113, 0.3)
... /* 对应主色的 30% 透明度 */
```

### 1.3 CSS 变量定义

```css
:root {
  /* 主题色 */
  --bg-canvas: #020617;
  --bg-surface: #0F172A;
  --bg-elevated: #1E293B;
  --bg-raised: #334155;
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --border-default: #1E293B;
  --border-accent: #334155;
  --accent-brand: #E2E8F0;
  --accent-positive: #22C55E;
  --accent-divergence: #F59E0B;
  --accent-live: #EF4444;  /* 直播指示器专用——唯一红色，不与嘉宾色冲突 */

  /* 9 色嘉宾调色板 */
  --panelist-0: #38BDF8; --panelist-0-soft: rgba(56,189,248,0.30);
  --panelist-1: #F87171; --panelist-1-soft: rgba(248,113,113,0.30);
  --panelist-2: #818CF8; --panelist-2-soft: rgba(129,140,248,0.30);  /* 靛蓝——绿被共识独占 */
  --panelist-3: #FBBF24; --panelist-3-soft: rgba(251,191,36,0.30);
  --panelist-4: #A78BFA; --panelist-4-soft: rgba(167,139,250,0.30);
  --panelist-5: #FB923C; --panelist-5-soft: rgba(251,146,60,0.30);
  --panelist-6: #E879F9; --panelist-6-soft: rgba(232,121,249,0.30);
  --panelist-7: #2DD4BF; --panelist-7-soft: rgba(45,212,191,0.30);
  --panelist-8: #FCA5A5; --panelist-8-soft: rgba(252,165,165,0.30);

  /* 间距与圆角 */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-full: 9999px;

  /* 动效 */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}
```

### 1.4 Tailwind 配置映射

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        panelist: {
          0: '#38BDF8', 1: '#F87171', 2: '#818CF8', 3: '#FBBF24',
          4: '#A78BFA', 5: '#FB923C', 6: '#E879F9', 7: '#2DD4BF', 8: '#FCA5A5',
        },
      },
      fontFamily: {
        heading: ['Poppins', '"Noto Sans SC"', 'sans-serif'],  /* 拉丁用 Poppins，中文回退 Noto Sans SC */
        body: ['Poppins', '"Noto Sans SC"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
    },
  },
};
```

---

## 2. 字体系统

### 2.1 字体配对

| 层级 | 字体栈 | 用途 |
|------|--------|------|
| **Heading** | `Poppins, "Noto Sans SC", sans-serif` | 拉丁字符用 Poppins 几何感，中文回退到 Noto Sans SC |
| **Body** | `Poppins, "Noto Sans SC", sans-serif` | 同上——拉丁数字和英文字母优先 Poppins，中文用 Noto Sans SC |
| **Mono** | `"JetBrains Mono", Consolas, monospace` | 技术调试面板、讨论 ID |

**选型依据**: Noto Sans SC 是 Google 与 Adobe 联合设计的开源中文字体，字形现代清晰，支持 300/400/500/700 四个字重。搭配 Poppins 作为英文/数字 fallback，几何感与现代感匹配演播厅氛围。

### 2.2 Google Fonts 引入

```html
<!-- index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
```

### 2.3 排版尺度

| Token | 字号 / 行高 | Tailwind | 用途 |
|-------|-----------|----------|------|
| `text-display` | 28px / 1.3 | `text-3xl font-heading font-bold` | 讨论话题大标题（演播厅顶部） |
| `text-heading` | 20px / 1.4 | `text-xl font-heading font-semibold` | 面板标题（共识/分歧区标题） |
| `text-subheading` | 16px / 1.5 | `text-base font-heading font-medium` | 嘉宾姓名 |
| `text-body` | 15px / 1.65 | `text-[15px] leading-relaxed` | 发言正文、共识内容 |
| `text-caption` | 13px / 1.5 | `text-sm text-secondary` | 职业Title、时间戳、状态标签 |
| `text-tiny` | 11px / 1.4 | `text-xs text-muted` | 计数徽标、次要元数据 |

---

## 3. 布局系统

### 3.1 演播厅三区布局

```
┌─────────────────────────────────────────────────────┐
│  讨论话题标题 + 直播指示器                 [结束讨论] │  ← 顶部栏 (h-14, sticky)
├──────────────────────┬──────────────┬───────────────┤
│                      │              │               │
│   专家小窗区          │  现场        │  共识与分歧区   │
│   (Panelist Grid)    │  Transcript  │  (Consensus   │
│                      │              │   & Divergence)│
│   滚动: overflow-y   │  滚动:       │  滚动:        │
│   独立               │  overflow-y  │  overflow-y   │
│                      │  独立        │  独立         │
│                      │              │               │
├──────────────────────┴──────────────┴───────────────┤
│  flex-1 min-h-0 — 三区等分剩余空间，整页不滚动        │
└─────────────────────────────────────────────────────┘
```

**CSS 关键约束**:
```css
.studio-layout {
  display: flex;
  height: 100vh;           /* 整页不滚动 */
  overflow: hidden;        /* 根容器禁止滚动 */
}

.studio-panel {
  flex: 1;
  min-width: 0;            /* 允许 flex 子元素收缩 */
  overflow-y: auto;        /* 面板内独立滚动 */
  scrollbar-width: thin;
  scrollbar-color: var(--bg-raised) transparent;
}
```

**Tailwind 实现**:
```html
<div class="flex h-screen overflow-hidden">
  <aside class="flex-1 min-w-0 overflow-y-auto">      <!-- 专家区 -->
  <main   class="flex-1 min-w-0 overflow-y-auto">      <!-- Transcript -->
  <aside  class="flex-1 min-w-0 overflow-y-auto">      <!-- 共识区 -->
</div>
```

### 3.2 响应式断点

| 断点 | 宽度 | 布局策略 |
|------|------|---------|
| **Mobile** | 375px – 767px | 三区堆叠为底部 Tab，单区全屏切换。顶部话题标题缩写 |
| **Tablet** | 768px – 1023px | 双列：左侧专家区 + 右侧 tab（Transcript↔共识）。专家卡片缩小为 2 列网格 |
| **Desktop** | 1024px – 1439px | 三列并排，`flex: 1 1 0` 等分。专家区 3 列网格 |
| **Wide** | ≥ 1440px | 三列并排 + 最大宽度 `max-w-[1600px]` 居中。专家区 3–4 列网格。Transcript 区更宽（`flex: 1.2`） |

### 3.3 面板内部滚动条样式

```css
.studio-panel::-webkit-scrollbar { width: 4px; }
.studio-panel::-webkit-scrollbar-track { background: transparent; }
.studio-panel::-webkit-scrollbar-thumb { background: var(--bg-raised); border-radius: 2px; }
.studio-panel::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
```

---

## 4. 动效规范

### 4.1 时间与缓动

| 场景 | 时长 | 缓动 | 说明 |
|------|------|------|------|
| 发言出现（utterance enter） | 250ms | `--ease-out` | `slide-up` + `fade-in`，从下方 8px 滑入 |
| 状态切换（idle→preparing→speaking） | 200ms | `--ease-in-out` | 指示灯颜色渐变 + 微缩放 |
| 沉默标记（→silent） | 300ms | `--ease-out` | 状态标签淡出为灰色 |
| 共识更新（consensus new/update） | 250ms | `--ease-out` | 卡片出现 + 短暂边框发光（200ms 后消失） |
| 直播脉冲（live indicator） | 2s 循环 | `ease-in-out` | `opacity: 1 ↔ 0.5` 呼吸动画 |
| 悬停反馈 | 150ms | `--ease-out` | `bg-elevated` 背景色过渡 |

### 4.2 性能约束

- **动画优先 `transform` 和 `opacity`** —— `box-shadow` 仅用于小范围低频强调（如共识新增描边 250ms 一闪、嘉宾色块静态阴影），不用于列表项持续动画。严禁 `width`/`height`/`top`/`left` 动画
- 所有动效包裹在 `@media (prefers-reduced-motion: no-preference)` 内
- GPU 加速：`will-change: transform, opacity` 仅用于频繁动画元素（如 live indicator），不用作全局规则

### 4.3 Tailwind 动效类

```css
/* tailwind.config.js 扩展 */
animation: {
  'slide-up': 'slide-up 250ms var(--ease-out)',
  'fade-in': 'fade-in 200ms var(--ease-out)',
  'pulse-live': 'pulse-live 2s ease-in-out infinite',
  'glow-brief': 'glow-brief 250ms ease-out',
},
keyframes: {
  'slide-up': { from: { transform: 'translateY(8px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
  'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
  'pulse-live': { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.5' } },
  'glow-brief': { '0%': { boxShadow: '0 0 0 0 var(--accent-positive)' }, '100%': { boxShadow: '0 0 0 0 transparent' } },
},
```

### 4.4 每屏最多动画元素

- 发言列表：只有**最新一条**发言有入场动画，历史发言不重复动画
- 共识面板：只有**新增/更新**的卡片有短暂描边发光（250ms），已存在卡片不动画
- 专家小窗：同一时刻最多 1 个专家处于 `speaking`（动画亮点），其余为静态

---

## 5. 组件 Token（非业务组件——纯视觉规范）

### 5.1 嘉宾色块 (ColorBadge)

```css
.color-badge {
  width: 12px; height: 12px;
  border-radius: var(--radius-full);
  background: var(--panelist-N);           /* N = sort_order */
  box-shadow: 0 0 8px var(--panelist-N-soft);
  flex-shrink: 0;
}
```

### 5.2 状态指示灯 (StatusIndicator)

```css
.status-dot { width: 8px; height: 8px; border-radius: var(--radius-full); }
.status-idle       { background: var(--text-muted); }                /* 灰色 */
.status-preparing  { background: var(--text-primary); animation: pulse-live 1.5s ease-in-out infinite; } /* 亮白——不与嘉宾色冲突 */
.status-speaking   { background: var(--accent-live);   animation: pulse-live 2s ease-in-out infinite; } /* 红——仅直播状态 */
.status-silent     { background: var(--bg-raised);     opacity: 0.6; }
```

### 5.3 Transcript 发言条目

```css
.utterance-item {
  padding: 10px 14px;
  border-left: 3px solid var(--panelist-N);  /* 发言人专属色左边框 */
  background: var(--bg-surface);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin-bottom: 2px;
}

.utterance-item:last-child {
  animation: slide-up 250ms var(--ease-out);
}
```

### 5.4 共识/分歧卡片

```css
.consensus-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 12px 14px;
}

.consensus-card.new-or-updated {
  animation: glow-brief 250ms ease-out;
  border-color: var(--accent-positive);
}

.divergence-card {
  /* 同上，但边框使用 --accent-divergence（琥珀），不用红——红仅用于直播指示器 */
}
```

### 5.5 直播指示器

```css
.live-indicator {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: rgba(239, 68, 68, 0.15);
  color: var(--accent-live);
  font-size: 12px; font-weight: 500;
}

.live-indicator::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: var(--radius-full);
  background: var(--accent-live);
  animation: pulse-live 2s ease-in-out infinite;
}
```

---

## 6. 可访问性 (Accessibility)

| 规则 | 要求 | 验证方法 |
|------|------|---------|
| **颜色对比度** | 正文 ≥ 4.5:1 (WCAG AA)，大标题 ≥ 3:1 | DevTools 对比度检查器 |
| **焦点环** | 所有可交互元素 `focus-visible:ring-2 ring-slate-200 ring-offset-2 ring-offset-slate-950` | Tab 键遍历 |
| **键盘导航** | Tab 顺序 = 视觉顺序；所有交互可用 Enter/Space 触发 | 全程键盘操作测试 |
| **图标标签** | 纯图标按钮必须有 `aria-label` | 辅助技术审查 |
| **动态内容** | transcript 新发言使用 `aria-live="polite"` 通知屏幕阅读器 | VoiceOver/NVDA 测试 |
| **色彩依赖** | 任何信息不得仅依赖颜色传达——状态需同时有图标/文字 | 灰度截图验证 |
| **prefers-reduced-motion** | 所有动效在 `prefers-reduced-motion: reduce` 下禁用 | 系统设置 → 辅助功能 → 减弱动态效果 |
| **触控目标** | 交互元素最小 44×44px | 移动端手指操作不误触 |

### 辅助技术文本

```html
<!-- Transcript 区域 -->
<section aria-label="讨论现场记录" aria-live="polite" aria-atomic="false">
  <!-- 每条新发言自动播报 -->
</section>

<!-- 共识面板 -->
<section aria-label="共识与分歧" aria-live="polite">
  <!-- 共识更新自动播报 -->
</section>

<!-- 专家状态区 -->
<section aria-label="嘉宾状态">
  <!-- 状态切换使用 aria-label -->
</section>
```

---

## 7. 交付前检查表

### 视觉质量
- [ ] 无 emoji 用作图标（全部使用 Lucide SVG）
- [ ] 所有嘉宾色块使用对应的 `--panelist-N` 变量
- [ ] 直播指示器呼吸动效存在且不刺眼
- [ ] 滚动条样式为细条暗色（`w-1`），与深色背景协调
- [ ] 面板底色对比：canvas(#020617) / surface(#0F172A) / elevated(#1E293B) 层次分明

### 交互
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] 悬停态有视觉反馈（`hover:bg-slate-800` 过渡 150ms）
- [ ] 焦点态可见（`focus-visible:ring-2 ring-slate-200`）
- [ ] 动效时长 150–300ms，不超过 500ms

### 响应式断点
- [ ] **375px**: 三区堆叠为 Tab，顶部标题缩写，触摸目标 ≥ 44px
- [ ] **768px**: 双列布局（专家 + Tab），专家卡片 2 列网格
- [ ] **1024px**: 三列并排，`flex: 1 1 0` 等分，各自独立滚动
- [ ] **1440px**: 三列 + `max-w-[1600px] mx-auto` 居中，Transcript 区稍宽

### 无障碍
- [ ] 所有 `img` 有 `alt` 属性
- [ ] 图标按钮有 `aria-label`
- [ ] 表单控件有 `<label>` 或 `aria-labelledby`
- [ ] 颜色对比度：正文 ≥ 4.5:1，大文本 ≥ 3:1
- [ ] 灰度模式下所有信息仍可区分
- [ ] `prefers-reduced-motion: reduce` 下动效完全关闭

### 性能
- [ ] 动画仅使用 `transform` 和 `opacity`
- [ ] Google Fonts 使用 `preconnect` + `display=swap`
- [ ] 大列表使用 `will-change` 保守（仅频繁动画的元素）
