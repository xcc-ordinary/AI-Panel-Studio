/** Apple Studio — 单个嘉宾状态小窗: 玻璃卡片 + 色块 + 身份 + 状态 + 发言跑马灯 */
import type { PanelistStatus } from '../../types';
import { getColor } from '../../utils/colors';
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
  const isSpeaking = panelist.status === 'speaking';
  const { hex, soft } = getColor(panelist.colorIndex);

  return (
    <div
      data-testid={`panelist-window-${panelist.name}`}
      className="p-4 rounded-[16px] transition-all duration-[var(--duration-fast)]"
      style={{
        background: isHost ? 'rgba(255,255,255,0.04)' : 'var(--glass-bg)',
        backdropFilter: 'blur(var(--glass-blur))',
        WebkitBackdropFilter: 'blur(var(--glass-blur))',
        border: isSpeaking
          ? `1px solid ${hex}`
          : '0.5px solid var(--glass-border)',
        boxShadow: isSpeaking
          ? `0 0 16px ${soft}, 0 0 32px ${soft}`
          : 'var(--glass-shadow)',
        animation: isSpeaking
          ? `speaking-marquee 2s var(--ease-apple) infinite`
          : 'none',
        color: isSpeaking ? hex : 'inherit',
        transform: isSpeaking ? 'scale(1.02)' : 'scale(1)',
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
