/**
 * 9 色嘉宾专属调色板 —— 与 design-system/MASTER.md §1.2 完全一致。
 *
 * 分配规则: color_index = panelist.sort_order，不可重复。主持人始终 0 号色。
 * 语义色独占: 绿(#22C55E)=共识, 琥珀(#F59E0B)=分歧, 红(#EF4444)=直播指示器——嘉宾色不占用。
 */

export const PANELIST_COLORS: Record<number, { hex: string; soft: string }> = {
  0: { hex: '#38BDF8', soft: 'rgba(56, 189, 248, 0.30)' },   // 天空蓝 — 主持人
  1: { hex: '#F87171', soft: 'rgba(248, 113, 113, 0.30)' },   // 珊瑚红
  2: { hex: '#818CF8', soft: 'rgba(129, 140, 248, 0.30)' },   // 靛蓝
  3: { hex: '#FBBF24', soft: 'rgba(251, 191, 36, 0.30)' },    // 琥珀金
  4: { hex: '#A78BFA', soft: 'rgba(167, 139, 250, 0.30)' },   // 紫罗兰
  5: { hex: '#FB923C', soft: 'rgba(251, 146, 60, 0.30)' },    // 活力橙
  6: { hex: '#E879F9', soft: 'rgba(232, 121, 249, 0.30)' },   // 品红
  7: { hex: '#2DD4BF', soft: 'rgba(45, 212, 191, 0.30)' },    // 青碧绿
  8: { hex: '#FCA5A5', soft: 'rgba(252, 165, 165, 0.30)' },   // 浅珊瑚
};

const TOTAL = Object.keys(PANELIST_COLORS).length;

/**
 * 按 sort_order 索引获取嘉宾颜色。索引越界时回环取模（理论上不超 9 人）。
 */
export function getColor(index: number): { hex: string; soft: string } {
  return PANELIST_COLORS[index % TOTAL];
}

/**
 * 语义色 —— 不与嘉宾调色板重叠。
 * 颜色选取见 design-system/MASTER.md §1.1。
 */
export const SEMANTIC_COLORS = {
  /** 共识达成 (#22C55E) —— 嘉宾色中无绿，被共识独占 */
  consensus: '#22C55E',
  /** 分歧 (#F59E0B) —— 琥珀，全界面统一使用 */
  divergence: '#F59E0B',
  /** 直播指示器 (#EF4444) —— 唯一红色场景 */
  live: '#EF4444',
  /** 品牌焦点环 (#E2E8F0) —— 亮灰中性，不与嘉宾色冲突 */
  brand: '#E2E8F0',
} as const;
