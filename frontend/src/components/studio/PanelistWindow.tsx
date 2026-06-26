/** MASTER.md §5.1–§5.2 — 单个嘉宾状态小窗: 色块 + 身份 + 状态 + 关注点 */
import type { PanelistStatus } from '../../types';
import ColorBadge from '../shared/ColorBadge';
import StatusIndicator from './StatusIndicator';

interface PanelistInfo {
  name: string;
  title: string;
  colorIndex: number;
  status: PanelistStatus;
  publicFocus: string[];
}

interface PanelistWindowProps {
  panelist: PanelistInfo;
  isHost?: boolean;
}

export default function PanelistWindow({ panelist, isHost }: PanelistWindowProps) {
  return (
    <div
      className="p-3 rounded-[var(--radius-md)] transition-colors duration-[var(--duration-fast)]"
      style={{
        background: isHost ? 'var(--bg-elevated)' : 'var(--bg-surface)',
        border: isHost ? '1px solid var(--border-accent)' : '1px solid var(--border-default)',
      }}
    >
      {/* 头部: 色块 + 姓名 + 角色标签 */}
      <div className="flex items-center gap-2 mb-2">
        <ColorBadge colorIndex={panelist.colorIndex} size="md" />
        <span
          className="text-sm font-semibold truncate"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
        >
          {panelist.name}
        </span>
        {isHost && (
          <span
            className="text-[10px] px-1.5 py-px rounded-full font-medium shrink-0 ml-auto"
            style={{ background: 'rgba(56,189,248,0.15)', color: '#38BDF8' }}
          >
            主持
          </span>
        )}
      </div>

      {/* 职业 Title */}
      <p className="text-xs mb-2 px-1" style={{ color: 'var(--text-secondary)' }}>
        {panelist.title}
      </p>

      {/* 状态 */}
      <div className="mb-2 px-1">
        <StatusIndicator status={panelist.status} />
      </div>

      {/* 公开关注点 */}
      {panelist.publicFocus.length > 0 && (
        <div
          className="rounded-[var(--radius-sm)] p-2 text-[11px] leading-relaxed space-y-0.5"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          {panelist.publicFocus.map((f, i) => (
            <div key={i} style={{ color: 'var(--text-muted)' }}>
              · {f}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
