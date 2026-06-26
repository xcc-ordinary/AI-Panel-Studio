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
      if (data.discussion_id !== 'mock-d') await confirmPanelists(data.discussion_id);
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
      if (data.discussion_id !== 'mock-d') {
        const res = await regeneratePanelists(data.discussion_id);
        setPanelists(res.panelists);
      } else {
        await new Promise(r => setTimeout(r, 1000));
        onBackToCreate();
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="max-w-[720px] mx-auto px-4 py-10">
      <LoadingSkeleton lines={6} withCircle />
    </div>
  );

  return (
    <div className="max-w-[720px] mx-auto px-4 py-10">
      {/* 返回 */}
      <button
        onClick={onBackToCreate}
        className="inline-flex items-center gap-1.5 text-sm mb-6 cursor-pointer
                   transition-colors duration-[var(--duration-fast)] hover:opacity-80"
        style={{ color: 'var(--text-secondary)' }}
      >
        <ArrowLeft size={16} strokeWidth={1.5} />
        重新设置
      </button>

      <div className="mb-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium"
        style={{ background: 'rgba(56,189,248,0.1)', color: '#38BDF8', width: 'fit-content' }}>
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

      {/* 表单卡片 */}
      <div className="p-6 rounded-[var(--radius-lg)] border mb-8"
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>

        {/* 主持人 */}
        {host && (
          <div className="mb-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5"
              style={{ color: 'var(--text-muted)' }}>
              <Crown size={12} /> 主持人
            </p>
            <div className="flex items-start gap-4 p-4 rounded-[var(--radius-md)]"
              style={{ background: 'var(--bg-elevated)' }}>
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

        {/* 专家列表 */}
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider mb-3"
            style={{ color: 'var(--text-muted)' }}>
            专家 · {experts.length} 人
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {experts.map(p => (
              <div key={p.id}
                className="flex items-start gap-3 p-4 rounded-[var(--radius-md)]
                           transition-colors duration-[var(--duration-fast)]"
                style={{ background: 'var(--bg-elevated)' }}>
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

      {/* 错误 */}
      {error && (
        <div className="p-3 rounded-lg text-sm mb-4"
          style={{ background: 'rgba(239,68,68,0.1)', color: '#EF4444' }}>{error}</div>
      )}

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <button
          onClick={handleRegenerate}
          className="flex-1 inline-flex items-center justify-center gap-2 py-3 rounded-[var(--radius-md)]
                     text-sm font-medium cursor-pointer transition-all duration-[var(--duration-fast)]
                     border hover:bg-[var(--bg-elevated)]"
          style={{
            background: 'var(--bg-surface)',
            borderColor: 'var(--border-accent)',
            color: 'var(--text-primary)',
          }}
        >
          <RefreshCw size={15} strokeWidth={1.5} />
          重新生成
        </button>
        <button
          onClick={handleConfirm}
          className="flex-[2] inline-flex items-center justify-center gap-2 py-3 rounded-[var(--radius-md)]
                     text-sm font-semibold cursor-pointer transition-all duration-[var(--duration-fast)]
                     hover:shadow-[0_0_24px_rgba(226,232,240,0.12)]"
          style={{ background: 'var(--text-primary)', color: 'var(--bg-canvas)' }}
        >
          <CheckCircle size={16} />
          确认阵容，进入演播厅
        </button>
      </div>
    </div>
  );
}
