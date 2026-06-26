/** 嘉宾网格: 主持人置顶突出，专家网格排列 */
import { Crown } from 'lucide-react';
import PanelistWindow from './PanelistWindow';
import type { PanelistStatus } from '../../types';

interface PanelistInfo {
  name: string;
  title: string;
  colorIndex: number;
  status: PanelistStatus;
  isHost: boolean;
  publicFocus: string[];
}

interface PanelistGridProps {
  panelists: PanelistInfo[];
}

export default function PanelistGrid({ panelists }: PanelistGridProps) {
  const host = panelists.find(p => p.isHost);
  const experts = panelists.filter(p => !p.isHost);

  return (
    <div className="space-y-4">
      {/* 主持人区 */}
      {host && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1 flex items-center gap-1.5"
            style={{ color: 'var(--text-muted)' }}>
            <Crown size={11} /> 主持人
          </p>
          <PanelistWindow panelist={host} isHost />
        </div>
      )}

      {/* 专家区 */}
      {experts.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1"
            style={{ color: 'var(--text-muted)' }}>
            专家 · {experts.length} 人
          </p>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {experts.map(p => (
              <PanelistWindow key={p.name} panelist={p} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
