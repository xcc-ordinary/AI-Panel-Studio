interface EmptyStateProps {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 px-4 text-center"
      role="status"
    >
      <svg
        className="w-16 h-16 mb-4 opacity-20"
        viewBox="0 0 64 64"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <circle cx="32" cy="20" r="8" />
        <ellipse cx="32" cy="48" rx="20" ry="10" />
        <circle cx="24" cy="20" r="2" fill="currentColor" />
        <circle cx="40" cy="20" r="2" fill="currentColor" />
        <path d="M22 28 Q32 34 42 28" strokeLinecap="round" />
      </svg>
      <p className="text-base mb-4" style={{ color: 'var(--text-secondary)' }}>
        {message}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-2.5 rounded-[16px] text-sm font-medium cursor-pointer
                     transition-all duration-[var(--duration-fast)]"
          style={{
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(var(--glass-blur))',
            WebkitBackdropFilter: 'blur(var(--glass-blur))',
            border: '0.5px solid var(--glass-border)',
            color: 'var(--text-primary)',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--glass-bg-hover)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'var(--glass-bg)')}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
