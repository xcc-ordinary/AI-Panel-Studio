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
        <button onClick={onBack} className="px-4 py-2 rounded-[16px] text-sm cursor-pointer"
          style={{ background: 'var(--glass-bg)', color: 'var(--text-primary)' }}>返回首页</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: 'var(--bg-canvas)' }}>

      {/* ── Apple Studio Header ── */}
      <header className="glass-nav shrink-0 h-13 flex items-center justify-between px-5">
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
              background: isConnected ? 'rgba(255,69,58,0.08)' : 'rgba(110,110,115,0.10)',
              color: isConnected ? 'var(--accent-live)' : 'var(--text-muted)',
            }}>
            <span className="w-1.5 h-1.5 rounded-full"
              style={{
                background: isConnected ? 'var(--accent-live)' : 'var(--text-muted)',
                animation: isConnected ? 'pulse-live 2s ease-in-out infinite' : 'none',
              }} />
            {isConnected ? '直播中' : '已断开'}
          </span>
          <button className="px-3 py-1.5 rounded-[16px] text-xs font-medium cursor-pointer
            transition-colors duration-[var(--duration-fast)]"
            style={{ background: 'transparent', border: '0.5px solid var(--glass-border)', color: 'var(--text-secondary)' }}>
            结束讨论
          </button>
        </div>
      </header>

      {/* ── discussion_end banner ── */}
      {discussionEnded && hostSummary && (
        <div data-testid="discussion-end-banner" className="glass-overlay shrink-0 p-5 mx-5 mt-5 rounded-[var(--radius-lg)]">
          <p className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>讨论结束 — 主持人总结</p>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{hostSummary}</p>
        </div>
      )}

      {/* ── Desktop 3-column: glass card modules, gap spacing ── */}
      <div className="hidden md:flex flex-1 min-h-0 gap-3 p-3">
        <aside className="glass-card flex-1 min-w-0 min-h-0 overflow-y-auto p-5">
          <PanelistGrid panelists={gridPanelists} />
        </aside>
        <main className="glass-card flex-[1.2] min-w-0 min-h-0 overflow-y-auto p-5">
          <h2 className="text-caption text-[11px] font-medium mb-4 px-1 tracking-wider uppercase">
            现场 Transcript
          </h2>
          <TranscriptPanel utterances={uttEntries} />
        </main>
        <aside className="glass-card flex-1 min-w-0 min-h-0 overflow-y-auto p-5">
          <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />
        </aside>
      </div>

      {/* ── Tablet 2-column ── */}
      <div className="hidden sm:flex md:hidden flex-1 min-h-0 gap-3 p-3">
        <aside className="glass-card w-[200px] shrink-0 min-h-0 overflow-y-auto p-4">
          <PanelistGrid panelists={gridPanelists} />
        </aside>
        <div className="glass-card flex-1 min-w-0 min-h-0 flex flex-col">
          <div className="shrink-0 flex" style={{ borderBottom: '0.5px solid var(--glass-border)' }}>
            {(['transcript','consensus'] as const).map(t => (
              <button key={t} onClick={() => setMobileTab(t as 'transcript'|'consensus')}
                className="flex-1 py-2 text-xs font-medium cursor-pointer"
                style={{
                  color: mobileTab === t ? 'var(--accent-brand)' : 'var(--text-muted)',
                  borderBottom: mobileTab === t ? '2px solid var(--accent-brand)' : '2px solid transparent',
                }}>
                {t === 'transcript' ? 'Transcript' : '共识与分歧'}
              </button>
            ))}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto p-3">
            {mobileTab === 'transcript'
              ? <TranscriptPanel utterances={uttEntries} />
              : <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />
            }
          </div>
        </div>
      </div>

      {/* ── Mobile single-column + bottom tabs ── */}
      <div className="flex sm:hidden flex-1 min-h-0 flex-col p-1">
        <div className="glass-card flex-1 min-h-0 overflow-y-auto p-4 m-2">
          {mobileTab === 'panelists' && <PanelistGrid panelists={gridPanelists} />}
          {mobileTab === 'transcript' && <TranscriptPanel utterances={uttEntries} />}
          {mobileTab === 'consensus' && <ConsensusPanel consensus={consensusCards} divergences={divergenceCards} />}
        </div>
        <nav className="glass-nav shrink-0 h-12 flex rounded-[var(--radius-lg)] mx-2 mb-2">
          {tabDefs.map(t => (
            <button key={t.key} onClick={() => setMobileTab(t.key)}
              className="flex-1 text-[11px] font-medium cursor-pointer"
              style={{
                color: mobileTab === t.key ? 'var(--accent-brand)' : 'var(--text-muted)',
              }}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}
