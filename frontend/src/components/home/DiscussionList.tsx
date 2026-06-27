import { useEffect, useState } from 'react';
import { Plus, Radio } from 'lucide-react';
import type { DiscussionListResponse } from '../../types';
import { listDiscussions } from '../../services/api';
import DiscussionCard from './DiscussionCard';
import EmptyState from '../shared/EmptyState';
import LoadingSkeleton from '../shared/LoadingSkeleton';

interface DiscussionListProps {
  onCreateNew: () => void;
  onJoin: (id: string, topic: string) => void;
}

export default function DiscussionList({ onCreateNew, onJoin }: DiscussionListProps) {
  const [data, setData] = useState<DiscussionListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const res = await listDiscussions();
        if (!cancelled) { setData(res); setError(null); }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-8">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1
            className="text-[28px] font-bold mb-1 tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
          >
            AI Panel Studio
          </h1>
          <p className="text-sm flex items-center gap-2" style={{ color: 'var(--text-secondary)' }}>
            <Radio size={14} strokeWidth={1.5} style={{ color: 'var(--accent-live)' }} />
            {data && <>{data.active_count}/{data.max_concurrent} 场讨论进行中</>}
            {!data && '加载中…'}
          </p>
        </div>
        <button
          data-testid="create-discussion-btn"
          onClick={onCreateNew}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold cursor-pointer
                     transition-all duration-[var(--duration-fast)]
                     border hover:shadow-[0_0_20px_rgba(226,232,240,0.15)]"
          style={{
            background: 'var(--bg-surface)',
            borderColor: '#E2E8F0',
            color: '#E2E8F0',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--bg-elevated)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'var(--bg-surface)';
          }}
        >
          <Plus size={16} strokeWidth={2} />
          发起新讨论
        </button>
      </div>

      {/* 错误 */}
      {error && (
        <div
          className="p-4 rounded-lg mb-6 text-sm flex items-center justify-between"
          style={{ background: 'rgba(239,68,68,0.1)', color: '#EF4444' }}
        >
          <span>{error}</span>
          <button onClick={() => window.location.reload()} className="underline cursor-pointer">重试</button>
        </div>
      )}

      {/* 加载态 */}
      {loading && <LoadingSkeleton lines={4} withCircle />}

      {/* 空态 */}
      {!loading && !error && data && data.discussions.length === 0 && (
        <EmptyState
          message="还没有讨论，发起第一场吧"
          actionLabel="发起新讨论"
          onAction={onCreateNew}
        />
      )}

      {/* 卡片网格 — 桌面 3 列 / 平板 2 列 / 窄屏 1 列 */}
      {!loading && data && data.discussions.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {data.discussions.map(d => (
            <DiscussionCard key={d.id} discussion={d} onClick={(id, topic) => onJoin(id, topic)} />
          ))}
        </div>
      )}
    </div>
  );
}
