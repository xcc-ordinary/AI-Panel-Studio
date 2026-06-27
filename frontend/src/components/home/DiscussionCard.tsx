import { Users, MessageSquare, Clock } from 'lucide-react';
import type { Discussion } from '../../types';
import { getColor } from '../../utils/colors';

interface DiscussionCardProps {
  discussion: Discussion;
  onClick: (id: string, topic: string) => void;
}

/** 按 expert_count 渲染 N 位专家 + 1 位主持人的精致色点。 */
function ColorDots({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-1" aria-hidden="true">
      {Array.from({ length: count + 1 }).map((_, i) => {
        const { hex, soft } = getColor(i);
        return (
          <span
            key={i}
            className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
            style={{ background: hex, boxShadow: `0 0 4px ${soft}` }}
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
      aria-label={`${discussion.topic}——${discussion.panelist_count || discussion.expert_count + 1}位嘉宾，${isLive ? '进行中' : '已结束'}，第${discussion.current_round}轮`}
      className="group p-6 rounded-[var(--radius-lg)] cursor-pointer
                 transition-all duration-[var(--duration-fast)]
                 focus-visible:ring-2 focus-visible:ring-[var(--accent-brand)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-canvas)]"
      style={{
        background: 'var(--glass-bg)',
        backdropFilter: 'blur(var(--glass-blur))',
        WebkitBackdropFilter: 'blur(var(--glass-blur))',
        border: '0.5px solid var(--glass-border)',
        boxShadow: 'var(--glass-shadow)',
        transform: 'translateY(0)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.background = 'var(--glass-bg-hover)';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'var(--glass-bg)';
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'var(--glass-shadow)';
      }}
    >
      {/* 顶部: 话题 + 状态 */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <h3
          className="text-base font-semibold leading-snug line-clamp-2 flex-1"
          style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
        >
          {discussion.topic}
        </h3>
        {/* Apple 弱化状态标签 */}
        <span
          data-testid="discussion-status-badge"
          className="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
          style={{
            background: isLive ? 'rgba(255,69,58,0.08)' : 'rgba(110,110,115,0.10)',
            color: isLive ? 'var(--accent-live)' : 'var(--text-muted)',
          }}
        >
          <span
            className="w-1 h-1 rounded-full"
            style={{
              background: isLive ? 'var(--accent-live)' : 'var(--text-muted)',
              animation: isLive ? 'pulse-live 2s ease-in-out infinite' : 'none',
            }}
          />
          {isLive ? '进行中' : isEnded ? '已结束' : '待生成'}
        </span>
      </div>

      {/* 中部: 元信息 */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mb-5 text-[13px]"
        style={{ color: 'var(--text-secondary)' }}>
        <span className="inline-flex items-center gap-1.5">
          <Users size={14} strokeWidth={1.5} />
          {discussion.panelist_count || discussion.expert_count + 1} 位嘉宾
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MessageSquare size={14} strokeWidth={1.5} />
          第 {discussion.current_round} 轮
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Clock size={14} strokeWidth={1.5} />
          {timeStr}
        </span>
      </div>

      {/* 底部: 色点 + CTA — 用留白替代分隔线 */}
      <div className="flex items-center justify-between">
        <ColorDots count={discussion.expert_count} />
        <span
          className="text-[11px] font-medium transition-opacity duration-[var(--duration-fast)] opacity-50 group-hover:opacity-100"
          style={{ color: 'var(--text-muted)' }}
        >
          加入观察 →
        </span>
      </div>
    </article>
  );
}
