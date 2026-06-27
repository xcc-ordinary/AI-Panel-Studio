import { useState, type FormEvent } from 'react';
import { ArrowLeft, Sparkles, Users, Mic } from 'lucide-react';
import { createDiscussion, type CreateDiscussionPayload } from '../../services/api';
import type { CreateDiscussionResponse } from '../../types';
import LoadingSkeleton from '../shared/LoadingSkeleton';

interface CreateDiscussionProps {
  onBack: () => void;
  onCreated: (data: CreateDiscussionResponse) => void;
}

const MIN_EXPERTS = 2;
const MAX_EXPERTS = 8;
const DEFAULT_EXPERTS = 4;

export default function CreateDiscussion({ onBack, onCreated }: CreateDiscussionProps) {
  const [topic, setTopic] = useState('');
  const [expertCount, setExpertCount] = useState(DEFAULT_EXPERTS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = topic.trim().length > 0 && !loading;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    try {
      const data = await createDiscussion({ topic: topic.trim(), expert_count: expertCount });
      onCreated(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-[720px] mx-auto px-4 py-10">
      {/* 返回 */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm mb-8 cursor-pointer
                   transition-colors duration-[var(--duration-fast)] hover:opacity-80"
        style={{ color: 'var(--text-secondary)' }}
      >
        <ArrowLeft size={16} strokeWidth={1.5} />
        返回首页
      </button>

      {/* 氛围文案 + 表单卡片 并排 */}
      <div className="grid gap-8 lg:grid-cols-5">
        {/* 左侧氛围文案 — 桌面 2/5 列 */}
        <div className="lg:col-span-2 flex flex-col justify-center">
          <div className="mb-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium"
            style={{ background: 'rgba(56,189,248,0.1)', color: '#38BDF8', width: 'fit-content' }}>
            <Sparkles size={12} />
            演播厅
          </div>
          <h2
            className="text-[28px] font-bold mb-3 leading-tight tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
          >
            发起一场<br />AI 圆桌讨论
          </h2>
          <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-secondary)' }}>
            输入话题，系统将自动生成一位主持人和多位立场各异的 AI 专家。
            他们会在演播厅中展开一场自然的圆桌辩论——你只需观看。
          </p>
          <div className="flex flex-col gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
            <span className="inline-flex items-center gap-1.5">
              <Users size={12} strokeWidth={1.5} />
              2–8 位专家，各持不同立场
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Mic size={12} strokeWidth={1.5} />
              主持人引导讨论，非机械轮流发言
            </span>
          </div>
        </div>

        {/* 右侧表单卡片 — 桌面 3/5 列 */}
        <div className="lg:col-span-3">
          <div
            className="p-6 rounded-[var(--radius-lg)] border"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
          >
            {loading ? (
              <LoadingSkeleton lines={5} withCircle />
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                {/* 话题输入 */}
                <div>
                  <label
                    htmlFor="topic"
                    className="block text-sm font-medium mb-2"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    讨论话题
                  </label>
                  <textarea
                    data-testid="topic-input"
                    id="topic"
                    value={topic}
                    onChange={e => setTopic(e.target.value)}
                    placeholder='输入你感兴趣的话题…例如"AI 是否应该开源？"'
                    maxLength={200}
                    rows={3}
                    autoFocus
                    className="w-full px-4 py-3 rounded-[var(--radius-md)] text-[15px] leading-relaxed resize-none
                               border transition-all duration-[var(--duration-fast)]
                               focus:outline-none focus:ring-2 focus:ring-[#E2E8F0] focus:ring-offset-2 focus:ring-offset-[#020617]"
                    style={{
                      background: 'var(--bg-raised)',
                      borderColor: 'var(--border-accent)',
                      color: 'var(--text-primary)',
                      fontFamily: 'var(--font-body)',
                    }}
                  />
                  <p className="text-xs mt-1.5" style={{ color: 'var(--text-muted)' }}>
                    {topic.length}/200 · 话题将经过内容审核
                  </p>
                </div>

                {/* 专家人数 */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                    专家人数
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      data-testid="expert-count-decrease"
                      type="button"
                      onClick={() => setExpertCount(c => Math.max(MIN_EXPERTS, c - 1))}
                      disabled={expertCount <= MIN_EXPERTS}
                      className="w-10 h-10 rounded-[var(--radius-sm)] text-lg font-medium cursor-pointer
                                 transition-all duration-[var(--duration-fast)] disabled:opacity-30
                                 hover:bg-[var(--border-accent)]"
                      style={{ background: 'var(--bg-raised)', color: 'var(--text-primary)' }}
                    >
                      −
                    </button>
                    <span className="text-xl font-bold min-w-[3ch] text-center"
                      style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
                      {expertCount}
                    </span>
                    <button
                      data-testid="expert-count-increase"
                      type="button"
                      onClick={() => setExpertCount(c => Math.min(MAX_EXPERTS, c + 1))}
                      disabled={expertCount >= MAX_EXPERTS}
                      className="w-10 h-10 rounded-[var(--radius-sm)] text-lg font-medium cursor-pointer
                                 transition-all duration-[var(--duration-fast)] disabled:opacity-30
                                 hover:bg-[var(--border-accent)]"
                      style={{ background: 'var(--bg-raised)', color: 'var(--text-primary)' }}
                    >
                      +
                    </button>
                    <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>
                      {MIN_EXPERTS}–{MAX_EXPERTS} 人，默认 {DEFAULT_EXPERTS}
                    </span>
                  </div>
                  <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                    1 名主持人 + {expertCount} 名专家，各持不同立场
                  </p>
                </div>

                {/* 错误 */}
                {error && (
                  <div data-testid="create-error" className="p-3 rounded-lg text-sm"
                    style={{ background: 'rgba(239,68,68,0.1)', color: '#EF4444' }}>
                    {error}
                  </div>
                )}

                {/* 提交按钮 */}
                <button
                  data-testid="generate-panelists-btn"
                  type="submit"
                  disabled={!canSubmit}
                  className="w-full inline-flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold
                             cursor-pointer transition-all duration-[var(--duration-fast)]
                             disabled:opacity-30 disabled:cursor-not-allowed
                             hover:shadow-[0_0_24px_rgba(226,232,240,0.12)]"
                  style={{
                    background: canSubmit ? 'var(--text-primary)' : 'var(--bg-raised)',
                    color: canSubmit ? 'var(--bg-canvas)' : 'var(--text-muted)',
                  }}
                >
                  <Sparkles size={16} />
                  生成嘉宾阵容
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
