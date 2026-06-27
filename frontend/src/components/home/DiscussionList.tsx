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
    <div className="max-w-[1400px] mx-auto px-6 sm:px-8 py-12">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-10">
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
                     transition-all duration-[var(--duration-fast)]"
          style={{
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(var(--glass-blur))',
            WebkitBackdropFilter: 'blur(var(--glass-blur))',
            border: '0.5px solid var(--glass-border)',
            color: 'var(--accent-brand)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--glass-bg-hover)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'var(--glass-bg)';
          }}
        >
          <Plus size={16} strokeWidth={2} />
          发起新讨论
        </button>
      </div>

      {/* Error */}
      {error && (
        <div
          className="p-4 rounded-[16px] mb-6 text-sm flex items-center justify-between"
          style={{ background: 'rgba(255,69,58,0.08)', color: 'var(--accent-live)' }}
        >
          <span>{error}</span>
          <button onClick={() => window.location.reload()} className="underline cursor-pointer">重试</button>
        </div>
      )}

      {/* Loading */}
      {loading && <LoadingSkeleton lines={4} withCircle />}

      {/* Empty */}
      {!loading && !error && data && data.discussions.length === 0 && (
        <EmptyState
          message="还没有讨论，发起第一场吧"
          actionLabel="发起新讨论"
          onAction={onCreateNew}
        />
      )}

      {/* Card grid */}
      {!loading && data && data.discussions.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {data.discussions.map(d => (
            <DiscussionCard key={d.id} discussion={d} onClick={(id, topic) => onJoin(id, topic)} />
          ))}
        </div>
      )}
    </div>
  );
}
