import { useState } from 'react';
import { ArrowLeft, RefreshCw, CheckCircle, Crown, Sparkles } from 'lucide-react';
import type { CreateDiscussionResponse } from '../../types';
import { confirmPanelists, regeneratePanelists } from '../../services/api';
import ColorBadge from '../shared/ColorBadge';
import LoadingSkeleton from '../shared/LoadingSkeleton';

interface PanelistRosterProps {
  data: CreateDiscussionResponse;
  onBackToCreate: () => void;
  onConfirmed: (discussionId: string, topic: string) => void;
}

export default function PanelistRoster({ data, onBackToCreate, onConfirmed }: PanelistRosterProps) {
  const [panelists, setPanelists] = useState(data.panelists);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const host = panelists.find(p => p.role === 'host');
  const experts = panelists.filter(p => p.role === 'expert');

  async function handleConfirm() {
    setLoading(true);
    setError(null);
    try {
      await confirmPanelists(data.discussion_id);
      onConfirmed(data.discussion_id, data.topic);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await regeneratePanelists(data.discussion_id);
      setPanelists(res.panelists);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="max-w-[720px] mx-auto px-4 py-12">
      <LoadingSkeleton lines={6} withCircle />
    </div>
  );

  return (
    <div className="max-w-[720px] mx-auto px-4 py-12">
      <button
        data-testid="roster-back-btn"
        onClick={onBackToCreate}
        className="inline-flex items-center gap-1.5 text-sm mb-6 cursor-pointer
                   transition-colors duration-[var(--duration-fast)] hover:opacity-80"
        style={{ color: 'var(--text-secondary)' }}
      >
        <ArrowLeft size={16} strokeWidth={1.5} />
        重新设置
      </button>

      <div className="mb-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium"
        style={{ background: 'rgba(10,132,255,0.08)', color: 'var(--accent-brand)', width: 'fit-content' }}>
        <Sparkles size={12} />
        嘉宾阵容
      </div>

      <h2 className="text-[28px] font-bold mb-1 tracking-tight"
        style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
        确认嘉宾阵容
      </h2>
      <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
        话题：{data.topic}
      </p>

      {/* Glass card */}
      <div
        className="p-6 rounded-[var(--radius-lg)] mb-8"
        style={{
          background: 'var(--glass-bg)',
          backdropFilter: 'blur(var(--glass-blur))',
          WebkitBackdropFilter: 'blur(var(--glass-blur))',
          border: '0.5px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow)',
        }}
      >
        {/* Host */}
        {host && (
          <div className="mb-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5"
              style={{ color: 'var(--text-muted)' }}>
              <Crown size={12} /> 主持人
            </p>
            <div className="flex items-start gap-4 p-4 rounded-[16px]"
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              <ColorBadge colorIndex={host.sort_order} size="md" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-base"
                    style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
                    {host.name}
                  </span>
                </div>
                <p className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>{host.title}</p>
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{host.stance}</p>
              </div>
            </div>
          </div>
        )}

        {/* Experts */}
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--text-muted)' }}>
            专家 · {experts.length} 人
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {experts.map(p => (
              <div key={p.id}
                className="flex items-start gap-3 p-4 rounded-[16px] transition-colors duration-[var(--duration-fast)]"
                style={{ background: 'rgba(255,255,255,0.03)' }}>
                <ColorBadge colorIndex={p.sort_order} size="md" />
                <div className="flex-1 min-w-0">
                  <span className="font-semibold text-sm block mb-0.5"
                    style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
                    {p.name}
                  </span>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{p.title}</p>
                  <p className="text-xs leading-relaxed line-clamp-2" style={{ color: 'var(--text-muted)' }}>
                    {p.stance}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 rounded-[16px] text-sm mb-4"
          style={{ background: 'rgba(255,69,58,0.08)', color: 'var(--accent-live)' }}>{error}</div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          data-testid="regenerate-btn"
          onClick={handleRegenerate}
          className="flex-1 inline-flex items-center justify-center gap-2 py-3 rounded-[16px]
                     text-sm font-medium cursor-pointer transition-all duration-[var(--duration-fast)]"
          style={{
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(var(--glass-blur))',
            WebkitBackdropFilter: 'blur(var(--glass-blur))',
            border: '0.5px solid var(--glass-border)',
            color: 'var(--text-primary)',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--glass-bg-hover)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'var(--glass-bg)'; }}
        >
          <RefreshCw size={15} strokeWidth={1.5} />
          重新生成
        </button>
        <button
          data-testid="confirm-roster-btn"
          onClick={handleConfirm}
          className="flex-[2] inline-flex items-center justify-center gap-2 py-3 rounded-[16px]
                     text-sm font-semibold cursor-pointer transition-all duration-[var(--duration-fast)]"
          style={{ background: 'var(--accent-brand)', color: '#FFFFFF' }}
        >
          <CheckCircle size={16} />
          确认阵容，进入演播厅
        </button>
      </div>
    </div>
  );
}
