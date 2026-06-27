import { useState, useMemo } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useDiscussion } from '../../hooks/useDiscussion';
import PanelistGrid from './PanelistGrid';
import TranscriptPanel from './TranscriptPanel';
import ConsensusPanel from './ConsensusPanel';
import type { PanelistStatus } from '../../types';

interface StudioViewProps {
  discussionId: string;
  topic?: string;
  onBack: () => void;
}

type MobileTab = 'panelists' | 'transcript' | 'consensus';

export default function StudioView({ discussionId, topic, onBack }: StudioViewProps) {
  const [mobileTab, setMobileTab] = useState<MobileTab>('transcript');
  const { panelists, utterances, consensus, divergences, loading, error, isConnected, discussionEnded, hostSummary } =
    useDiscussion(discussionId);

  // ── 转换为子组件所需格式 ──────────────────────
  const gridPanelists = useMemo(() => panelists.map(p => ({
    name: p.name,
    title: p.title,
    colorIndex: p.sort_order,
    status: p.status as PanelistStatus,
    isHost: p.role === 'host',
    publicFocus: (() => {
      try { return JSON.parse(p.public_focus || '[]'); } catch { return []; }
    })(),
  })), [panelists]);

  const uttEntries = useMemo(() => utterances.map(u => ({
    panelistName: u.panelist_name,
    panelistTitle: u.panelist_title,
    colorIndex: panelists.find(p => p.id === u.panelist_id)?.sort_order ?? 0,
    content: u.content,
  })), [utterances, panelists]);

  const consensusCards = useMemo(() => consensus.map(c => ({
    id: c.id,
    content: c.content,
    involvedNames: (c.involved_panelist_ids || []).map(
      (pid: string) => panelists.find(p => p.id === pid)?.name || pid
    ),
  })), [consensus, panelists]);

  const divergenceCards = useMemo(() => divergences.map(d => ({
    id: d.id,
    description: d.description,
    camps: (d.camps || []).map((camp: { position: string; panelist_ids: string[] }) => ({
      position: camp.position,
      names: (camp.panelist_ids || []).map(
        (pid: string) => panelists.find(p => p.id === pid)?.name || pid
      ),
    })),
  })), [divergences, panelists]);

  const tabDefs: { key: MobileTab; label: string }[] = [
    { key: 'panelists', label: '嘉宾' },
    { key: 'transcript', label: 'Transcript' },
    { key: 'consensus', label: '共识' },
  ];

  const panelProps = { scrollbarWidth: 'thin' as const, scrollbarColor: 'var(--bg-raised) transparent' as const };

  // ── 加载态 / 错误态 ────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: 'var(--bg-canvas)' }}>
        <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>加载中…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4" style={{ background: 'var(--bg-canvas)' }}>
        <p style={{ color: 'var(--accent-live)' }}>{error}</p>
        <button onClick={onBack} className="px-4 py-2 rounded-lg text-sm cursor-pointer"
          style={{ background: 'var(--bg-raised)', color: 'var(--text-primary)' }}>返回首页</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: 'var(--bg-canvas)' }}>

      {/* ── 顶部栏 ──────────────────────────────── */}
      <header className="shrink-0 h-14 flex items-center justify-between px-4 border-b"
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
        <div className="flex items-center gap-3 min-w-0">
          <button onClick={onBack} className="shrink-0 cursor-pointer transition-opacity duration-[var(--duration-fast)] hover:opacity-80"
            style={{ color: 'var(--text-secondary)' }} aria-label="返回首页">
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <h1 className="text-base font-semibold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
            {topic || 'AI 圆桌讨论'}
          </h1>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span data-testid="connection-status"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
            style={{
              background: isConnected ? 'rgba(239,68,68,0.12)' : 'rgba(148,163,184,0.1)',
              color: isConnected ? 'var(--accent-live)' : 'var(--text-muted)',
            }}>
            <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-[var(--accent-live)] animate-pulse' : 'bg-[var(--text-muted)]'}`} />
            {isConnected ? '直播中' : '已断开'}
          </span>
          <button className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium cursor-pointer
            transition-colors duration-[var(--duration-fast)] border hover:bg-[var(--bg-elevated)]"
            style={{ background: 'transparent', borderColor: 'var(--border-accent)', color: 'var(--text-secondary)' }}>
            结束讨论
          </button>
        </div>
      </header>

      {/* ── discussion_end 浮层 ──────────────────── */}
      {discussionEnded && hostSummary && (
        <div data-testid="discussion-end-banner" className="shrink-0 p-4 border-b" style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border-accent)' }}>
          <p className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>讨论结束 — 主持人总结</p>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{hostSummary}</p>
        </div>
      )}

      {/* ── 桌面三列 ─────────────────────────────── */}
      <div className="hidden md:flex flex-1 min-h-0">
        <aside className="flex-1 min-w-0 min-h-0 overflow-y-auto p-4 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <PanelistGrid panelists={gridPanelists} />
        </aside>
        <main className="flex-[1.2] min-w-0 min-h-0 overflow-y-auto p-4 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <h2 className="text-sm font-semibold mb-3 px-1" style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-secondary)' }}>现场 Transcript</h2>
          <TranscriptPanel utterances={uttEntries} />
        </main>
        <aside className="flex-1 min-w-0 min-h-0 overflow-y-auto p-4" style={panelProps}>
          <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />
        </aside>
      </div>

      {/* ── 平板双列 ─────────────────────────────── */}
      <div className="hidden sm:flex md:hidden flex-1 min-h-0">
        <aside className="w-[200px] shrink-0 min-h-0 overflow-y-auto p-3 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <PanelistGrid panelists={gridPanelists} />
        </aside>
        <div className="flex-1 min-w-0 min-h-0 flex flex-col">
          <div className="shrink-0 flex border-b" style={{ borderColor: 'var(--border-default)' }}>
            {(['transcript','consensus'] as const).map(t => (
              <button key={t} onClick={() => setMobileTab(t as 'transcript'|'consensus')}
                className="flex-1 py-2 text-xs font-medium cursor-pointer"
                style={{
                  color: mobileTab === t ? 'var(--text-primary)' : 'var(--text-muted)',
                  borderBottom: mobileTab === t ? '2px solid #E2E8F0' : '2px solid transparent',
                }}>
                {t === 'transcript' ? 'Transcript' : '共识与分歧'}
              </button>
            ))}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto p-3" style={panelProps}>
            {mobileTab === 'transcript'
              ? <TranscriptPanel utterances={uttEntries} />
              : <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />
            }
          </div>
        </div>
      </div>

      {/* ── 窄屏单列 + 底部 tab ──────────────────── */}
      <div className="flex sm:hidden flex-1 min-h-0 flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto p-3" style={panelProps}>
          {mobileTab === 'panelists' && <PanelistGrid panelists={gridPanelists} />}
          {mobileTab === 'transcript' && <TranscriptPanel utterances={uttEntries} />}
          {mobileTab === 'consensus' && <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />}
        </div>
        <nav className="shrink-0 h-12 flex border-t" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
          {tabDefs.map(t => (
            <button key={t.key} onClick={() => setMobileTab(t.key)}
              className="flex-1 text-[11px] font-medium cursor-pointer"
              style={{
                color: mobileTab === t.key ? 'var(--text-primary)' : 'var(--text-muted)',
                borderTop: mobileTab === t.key ? '2px solid #E2E8F0' : '2px solid transparent',
              }}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
