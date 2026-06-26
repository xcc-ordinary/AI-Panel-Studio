/** MASTER.md §5.2 — 嘉宾状态指示灯 */
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
  const dims = size === 'md' ? 'w-2.5 h-2.5' : 'w-2 h-2';
  const label = LABELS[status];
  const pulse = status === 'preparing' || status === 'speaking';

  return (
    <span className="inline-flex items-center gap-1.5" title={label}>
      <span
        className={`inline-block ${dims} rounded-full shrink-0`}
        style={{
          background:
            status === 'idle' ? 'var(--text-muted)' :
            status === 'preparing' ? 'var(--text-primary)' :
            status === 'speaking' ? 'var(--accent-live)' :
            'var(--bg-raised)',
          opacity: status === 'silent' ? 0.5 : 1,
          animation: pulse ? `pulse-live ${status === 'speaking' ? '2s' : '1.5s'} ease-in-out infinite` : 'none',
        }}
      />
      <span
        className="text-[11px] font-medium"
        style={{
          color:
            status === 'idle' ? 'var(--text-muted)' :
            status === 'speaking' ? 'var(--accent-live)' :
            status === 'preparing' ? 'var(--text-primary)' :
            'var(--text-muted)',
        }}
      >
        {label}
      </span>
    </span>
  );
}
