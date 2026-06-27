/** Apple Studio — 嘉宾状态指示灯: 精致小点 + 脉冲动画 */
import type { PanelistStatus } from '../../types';

interface StatusIndicatorProps {
  status: PanelistStatus;
  size?: 'sm' | 'md';
}

const LABELS: Record<PanelistStatus, string> = {
  idle: '待发言',
  preparing: '准备中',
  speaking: '发言中',
  silent: '沉默',
};

export default function StatusIndicator({ status, size = 'sm' }: StatusIndicatorProps) {
  const dims = size === 'md' ? 'w-1.5 h-1.5' : 'w-1.5 h-1.5';
  const label = LABELS[status];
  const pulse = status === 'preparing' || status === 'speaking';

  return (
    <span data-testid={`status-${status}`} className="inline-flex items-center gap-1.5" title={label}>
      <span
        className={`inline-block ${dims} rounded-full shrink-0`}
        style={{
          background:
            status === 'idle' ? 'var(--text-muted)' :
            status === 'preparing' ? 'var(--text-secondary)' :
            status === 'speaking' ? 'var(--accent-live)' :
            'rgba(255,255,255,0.08)',
          opacity: status === 'silent' ? 0.4 : 1,
          animation: pulse ? `pulse-live ${status === 'speaking' ? '2s' : '1.5s'} ease-in-out infinite` : 'none',
        }}
      />
      <span
        className="text-[10px] font-medium"
        style={{
          color:
            status === 'idle' ? 'var(--text-muted)' :
            status === 'speaking' ? 'var(--accent-live)' :
            status === 'preparing' ? 'var(--text-secondary)' :
            'var(--text-muted)',
        }}
      >
        {label}
      </span>
    </span>
  );
}
