/** 轻量共识合并 hook — 被 useDiscussion 内部覆盖，保留供将来解耦使用。 */
import type { ConsensusPoint, DivergencePoint } from '../types';

export interface ConsensusState {
  consensus: ConsensusPoint[];
  divergences: DivergencePoint[];
}

export function mergeConsensusUpdate(
  prev: ConsensusPoint[],
  incoming: ConsensusPoint,
): ConsensusPoint[] {
  const idx = prev.findIndex(c => c.id === incoming.id);
  if (idx >= 0) return prev.map((c, i) => (i === idx ? incoming : c));
  return [...prev, incoming];
}

export function mergeDivergenceUpdate(
  prev: DivergencePoint[],
  incoming: DivergencePoint,
): DivergencePoint[] {
  const idx = prev.findIndex(d => d.id === incoming.id);
  if (idx >= 0) return prev.map((d, i) => (i === idx ? incoming : d));
  return [...prev, incoming];
}
