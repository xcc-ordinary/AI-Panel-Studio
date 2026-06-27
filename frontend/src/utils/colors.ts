/**
 * 9 色嘉宾专属调色板 — Apple Studio 去饱和版。
 *
 * 分配规则: color_index = panelist.sort_order，不可重复。主持人始终 0 号色。
 * 语义色独占: 绿(#30D158)=共识, 橙(#FF9F0A)=分歧, 红(#FF453A)=直播指示器——嘉宾色不占用。
 */

export const PANELIST_COLORS: Record<number, { hex: string; soft: string }> = {
  0: { hex: '#64D2FF', soft: 'rgba(100, 210, 255, 0.25)' },   // 天空蓝 — 主持人
  1: { hex: '#FF6961', soft: 'rgba(255, 105, 97, 0.25)' },     // 珊瑚红
  2: { hex: '#7D8FFF', soft: 'rgba(125, 143, 255, 0.25)' },    // 靛蓝
  3: { hex: '#FFD426', soft: 'rgba(255, 212, 38, 0.25)' },     // 琥珀金
  4: { hex: '#A78BFA', soft: 'rgba(167, 139, 250, 0.25)' },    // 紫罗兰
  5: { hex: '#FF9F4A', soft: 'rgba(255, 159, 74, 0.25)' },     // 活力橙
  6: { hex: '#F58FE6', soft: 'rgba(245, 143, 230, 0.25)' },    // 品红
  7: { hex: '#40D4C4', soft: 'rgba(64, 212, 196, 0.25)' },     // 青碧绿
  8: { hex: '#FFAAA5', soft: 'rgba(255, 170, 165, 0.25)' },    // 浅珊瑚
};

const TOTAL = Object.keys(PANELIST_COLORS).length;

/**
 * 按 sort_order 索引获取嘉宾颜色。索引越界时回环取模（理论上不超 9 人）。
 */
export function getColor(index: number): { hex: string; soft: string } {
  return PANELIST_COLORS[index % TOTAL];
}

/**
 * 语义色 — Apple 系统色，不与嘉宾调色板重叠。
 * 颜色选取见 design-system/MASTER.md §1.1。
 */
export const SEMANTIC_COLORS = {
  /** 共识达成 (#30D158) — Apple 系统绿，嘉宾色中无绿，被共识独占 */
  consensus: '#30D158',
  /** 分歧 (#FF9F0A) — Apple 系统橙，全界面统一使用 */
  divergence: '#FF9F0A',
  /** 直播指示器 (#FF453A) — Apple 系统红，唯一红色场景 */
  live: '#FF453A',
  /** 品牌交互色 (#0A84FF) — Apple 系统蓝 */
  brand: '#0A84FF',
} as const;
