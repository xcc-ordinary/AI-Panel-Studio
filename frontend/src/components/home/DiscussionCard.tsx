import { Users, MessageSquare, Clock } from 'lucide-react';
import type { Discussion } from '../../types';
import { getColor } from '../../utils/colors';

interface DiscussionCardProps {
  discussion: Discussion;
  onClick: (id: string, topic: string) => void;
}

/** 按 expert_count 渲染 N 位专家 + 1 位主持人的示意色点。 */
function ColorDots({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-1" aria-hidden="true">
      {Array.from({ length: count + 1 }).map((_, i) => {
        const { hex, soft } = getColor(i);
        return (
          <span
            key={i}
            className="inline-block w-2 h-2 rounded-full shrink-0"
            style={{ background: hex, boxShadow: `0 0 5px ${soft}` }}
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
      className="group p-5 rounded-[var(--radius-lg)] border cursor-pointer
                 transition-all duration-[var(--duration-fast)]
                 focus-visible:ring-2 focus-visible:ring-[#E2E8F0] focus-visible:ring-offset-2 focus-visible:ring-offset-[#020617]"
      style={{
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
        transform: 'translateY(0)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.background = 'var(--bg-elevated)';
        e.currentTarget.style.borderColor = 'var(--border-accent)';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.3)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'var(--bg-surface)';
        e.currentTarget.style.borderColor = 'var(--border-default)';
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
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
        <span
          data-testid="discussion-status-badge"
          className={`shrink-0 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium
            ${isLive ? 'bg-red-500/10 text-red-400' : 'bg-slate-700/40 text-slate-400'}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-red-500 animate-pulse' : 'bg-slate-500'}`} />
          {isLive ? '进行中' : isEnded ? '已结束' : '待生成'}
        </span>
      </div>

      {/* 中部: 元信息 + 图标 */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mb-4 text-[13px]"
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

      {/* 底部: 嘉宾色点 — 九色盘在首页可见 */}
      <div className="flex items-center justify-between pt-3 border-t"
        style={{ borderColor: 'var(--border-default)' }}>
        <ColorDots count={discussion.expert_count} />
        <span className="text-[11px] font-medium" style={{ color: 'var(--text-muted)' }}>
          加入观察 →
        </span>
      </div>
    </article>
  );
}
