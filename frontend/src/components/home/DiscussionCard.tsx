import { Users, MessageSquare, Clock } from 'lucide-react';
import type { Discussion } from '../../types';
import { getColor } from '../../utils/colors';

interface DiscussionCardProps {
  discussion: Discussion;
  onClick: (id: string, topic: string) => void;
}

function ColorDots({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-1" aria-hidden="true">
      {Array.from({ length: count + 1 }).map((_, i) => {
        const { hex } = getColor(i);
        return (
          <span
            key={i}
            className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
            style={{ background: hex }}
          />
        );
      })}
    </div>
  );
}

export default function DiscussionCard({ discussion, onClick }: DiscussionCardProps) {
  const isLive = discussion.status === 'in_progress';
  const isEnded = discussion.status === 'ended';
  const timeStr = new Date(discussion.created_at).toLocaleDateString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });

  return (
    <article
      data-testid="discussion-card"
      data-discussion-id={discussion.id}
      onClick={() => onClick(discussion.id, discussion.topic)}
      onKeyDown={e => { if (e.key === 'Enter') onClick(discussion.id, discussion.topic); }}
      tabIndex={0}
      role="button"
      className="glass-card group p-6 cursor-pointer
                 focus-visible:ring-2 focus-visible:ring-[var(--accent-brand)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-canvas)]"
      aria-label={`${discussion.topic}——${discussion.panelist_count || discussion.expert_count + 1}位嘉宾`}
    >
      {/* Topic + status */}
      <div className="flex items-start justify-between gap-3 mb-5">
        <h3 className="text-heading text-[15px] leading-snug line-clamp-2 flex-1">
          {discussion.topic}
        </h3>
        <span
          data-testid="discussion-status-badge"
          className="shrink-0 text-[10px] px-2 py-0.5 rounded-full border"
          style={{
            color: isLive ? 'var(--accent-positive)' : 'var(--text-muted)',
            borderColor: isLive ? 'rgba(48,209,88,0.2)' : 'rgba(255,255,255,0.06)',
          }}
        >
          <span
            className="inline-block w-1 h-1 rounded-full mr-1 align-middle"
            style={{
              background: isLive ? 'var(--accent-positive)' : 'var(--text-muted)',
              animation: isLive ? 'pulse-live 2s ease-in-out infinite' : 'none',
            }}
          />
          {isLive ? '进行中' : isEnded ? '已结束' : '待生成'}
        </span>
      </div>

      {/* Meta info */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mb-5 text-caption text-[12px]">
        <span className="inline-flex items-center gap-1.5">
          <Users size={13} strokeWidth={1.5} />
          {discussion.panelist_count || discussion.expert_count + 1} 位嘉宾
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MessageSquare size={13} strokeWidth={1.5} />
          第 {discussion.current_round} 轮
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Clock size={13} strokeWidth={1.5} />
          {timeStr}
        </span>
      </div>

      {/* Color dots + CTA — whitespace, no divider line */}
      <div className="flex items-center justify-between">
        <ColorDots count={discussion.expert_count} />
        <span className="text-[11px] transition-opacity duration-[var(--duration-fast)] opacity-40 group-hover:opacity-70"
          style={{ color: 'var(--text-secondary)' }}>
          加入观察 →
        </span>
      </div>
    </article>
  );
}
