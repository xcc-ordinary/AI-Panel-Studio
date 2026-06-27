/** Apple Studio — 单个嘉宾状态小窗: 玻璃卡片 + 色块 + 身份 + 状态 + 关注点 */
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
      data-testid={`panelist-window-${panelist.name}`}
      className="p-4 rounded-[16px] transition-colors duration-[var(--duration-fast)]"
      style={{
        background: isHost ? 'rgba(255,255,255,0.04)' : 'var(--glass-bg)',
        backdropFilter: 'blur(var(--glass-blur))',
        WebkitBackdropFilter: 'blur(var(--glass-blur))',
        border: '0.5px solid var(--glass-border)',
        boxShadow: 'var(--glass-shadow)',
      }}
    >
      {/* Header: badge + name + role */}
      <div className="flex items-center gap-2 mb-2">
        <ColorBadge colorIndex={panelist.colorIndex} size="md" />
        <span
          className="text-sm font-semibold truncate flex-1"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
        >
          {panelist.name}
        </span>
        {isHost && (
          <span
            className="text-[10px] px-1.5 py-px rounded-full font-medium shrink-0"
            style={{ background: 'rgba(10,132,255,0.10)', color: 'var(--accent-brand)' }}
          >
            主持
          </span>
        )}
      </div>

      {/* Title */}
      <p className="text-xs mb-2 px-1" style={{ color: 'var(--text-secondary)' }}>
        {panelist.title}
      </p>

      {/* Status */}
      <div className="mb-2 px-1">
        <StatusIndicator status={panelist.status} />
      </div>

      {/* Public focus */}
      {panelist.publicFocus.length > 0 && (
        <div
          className="rounded-[16px] p-2 text-[11px] leading-relaxed space-y-0.5"
          style={{ background: 'rgba(255,255,255,0.02)' }}
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
