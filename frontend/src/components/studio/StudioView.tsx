import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
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

// ── 静态假数据 ───────────────────────────────────────────────

interface FakePanelist {
  name: string; title: string; colorIndex: number;
  status: PanelistStatus; isHost: boolean; publicFocus: string[];
}

interface FakeUtterance {
  panelistName: string; panelistTitle: string; colorIndex: number; content: string;
}

interface FakeConsensus { id: string; content: string; isNew?: boolean; involvedNames: string[]; }
interface FakeDivergence { id: string; description: string; camps: { position: string; names: string[] }[]; isNew?: boolean; }

const FAKE_PANELISTS: FakePanelist[] = [
  { name: '张明远', title: '科技媒体主编', colorIndex: 0, status: 'speaking', isHost: true, publicFocus: ['引导讨论节奏', '确保各方观点平衡'] },
  { name: '李开放', title: '开源社区领袖', colorIndex: 1, status: 'idle', isHost: false, publicFocus: ['开源生态的可持续性'] },
  { name: '陈安全', title: '网络安全专家', colorIndex: 2, status: 'preparing', isHost: false, publicFocus: ['开源模型的安全审计机制', '准备回应李开放的生态观点'] },
  { name: '王商业', title: 'AI企业CEO', colorIndex: 3, status: 'silent', isHost: false, publicFocus: [] },
  { name: '赵伦理', title: '科技伦理学者', colorIndex: 4, status: 'idle', isHost: false, publicFocus: ['AI治理的国际协调机制'] },
];

const FAKE_UTTERANCES: FakeUtterance[] = [
  { panelistName: '张明远', panelistTitle: '科技媒体主编', colorIndex: 0, content: '欢迎各位来到今天的圆桌讨论。今天的话题是：AI 是否应该开源？我们有四位来自不同领域的专家。李开放先生，您先来谈谈？' },
  { panelistName: '李开放', panelistTitle: '开源社区领袖', colorIndex: 1, content: '开源是 AI 创新的生命线。如果每家公司都把模型锁在保险柜里，我们永远无法建立一个健康的 AI 生态。' },
  { panelistName: '陈安全', panelistTitle: '网络安全专家', colorIndex: 2, content: '我补充一点：开源确实有助于安全审计。我们最近发现的一个关键漏洞，正是因为模型的代码是公开的，才被及时发现并修复。' },
  { panelistName: '王商业', panelistTitle: 'AI企业CEO', colorIndex: 3, content: '但公司的研发投入需要回报。完全开源意味着任何人都可以复制我们的成果，这会打击企业创新的积极性。' },
  { panelistName: '赵伦理', panelistTitle: '科技伦理学者', colorIndex: 4, content: '我们需要跳出二元思维。问题不是该不该开源，而是如何建立一套全球性的 AI 治理框架，让开源的益处最大化、风险最小化。' },
  { panelistName: '张明远', panelistTitle: '科技媒体主编', colorIndex: 0, content: '赵伦理学者提到了治理框架，这个观点很有意思。李开放，您觉得开源社区能接受某种形式的监管吗？' },
  { panelistName: '李开放', panelistTitle: '开源社区领袖', colorIndex: 1, content: '监管不等于封杀。如果监管框架是由社区共同制定的，我想开源社区是愿意参与的。关键在于透明和参与。' },
  { panelistName: '陈安全', panelistTitle: '网络安全专家', colorIndex: 2, content: '同意。我们可以在开源社区内部先建立安全标准，再向监管机构证明自我规制的可行性。' },
];

const FAKE_CONSENSUS: FakeConsensus[] = [
  { id: 'c1', content: '与会专家一致认为需要建立 AI 开源的安全标准与治理框架', involvedNames: ['李开放', '陈安全', '赵伦理'] },
  { id: 'c2', content: '各方认同开源有助于安全审计，能更快发现和修复关键漏洞', involvedNames: ['李开放', '陈安全'], isNew: true },
];

const FAKE_DIVERGENCES: FakeDivergence[] = [
  {
    id: 'd1', description: '关于开源程度的根本分歧：一方主张完全开源，另一方认为核心模型应保留商业壁垒',
    camps: [
      { position: '完全开源', names: ['李开放'] },
      { position: '有限开源', names: ['王商业'] },
      { position: '有治理的开源', names: ['陈安全', '赵伦理'] },
    ],
  },
];

// ── 组件 ──────────────────────────────────────────────────

export default function StudioView({ topic, onBack }: StudioViewProps) {
  const [mobileTab, setMobileTab] = useState<MobileTab>('transcript');

  const tabDefs: { key: MobileTab; label: string }[] = [
    { key: 'panelists', label: '嘉宾' },
    { key: 'transcript', label: 'Transcript' },
    { key: 'consensus', label: '共识' },
  ];

  const panelProps = { scrollbarWidth: 'thin' as const, scrollbarColor: 'var(--bg-raised) transparent' as const };

  return (
    <div className="flex flex-col h-screen overflow-hidden"
      style={{ background: 'var(--bg-canvas)' }}>

      {/* ── 顶部栏 ──────────────────────────────── */}
      <header
        className="shrink-0 h-14 flex items-center justify-between px-4 border-b"
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      >
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onBack}
            className="shrink-0 cursor-pointer transition-opacity duration-[var(--duration-fast)] hover:opacity-80"
            style={{ color: 'var(--text-secondary)' }}
            aria-label="返回首页"
          >
            <ArrowLeft size={18} strokeWidth={1.5} />
          </button>
          <h1
            className="text-base font-semibold truncate"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}
          >
            {topic || 'AI 圆桌讨论'}
          </h1>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
            style={{ background: 'rgba(239,68,68,0.12)', color: 'var(--accent-live)' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-live)] animate-pulse" />
            直播中
          </span>
          <button
            className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium cursor-pointer
                       transition-colors duration-[var(--duration-fast)] border hover:bg-[var(--bg-elevated)]"
            style={{ background: 'transparent', borderColor: 'var(--border-accent)', color: 'var(--text-secondary)' }}>
            结束讨论
          </button>
        </div>
      </header>

      {/* ── 桌面三列 ─────────────────────────────── */}
      <div className="hidden md:flex flex-1 min-h-0">
        <aside className="flex-1 min-w-0 min-h-0 overflow-y-auto p-4 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <PanelistGrid panelists={FAKE_PANELISTS} />
        </aside>
        <main className="flex-[1.2] min-w-0 min-h-0 overflow-y-auto p-4 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <h2 className="text-sm font-semibold mb-3 px-1" style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-secondary)' }}>现场 Transcript</h2>
          <TranscriptPanel utterances={FAKE_UTTERANCES} />
        </main>
        <aside className="flex-1 min-w-0 min-h-0 overflow-y-auto p-4" style={panelProps}>
          <ConsensusPanel consensus={FAKE_CONSENSUS} divergences={FAKE_DIVERGENCES} />
        </aside>
      </div>

      {/* ── 平板双列 ─────────────────────────────── */}
      <div className="hidden sm:flex md:hidden flex-1 min-h-0">
        <aside className="w-[200px] shrink-0 min-h-0 overflow-y-auto p-3 border-r" style={{ borderColor: 'var(--border-default)', ...panelProps }}>
          <PanelistGrid panelists={FAKE_PANELISTS} />
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
              ? <TranscriptPanel utterances={FAKE_UTTERANCES} />
              : <ConsensusPanel consensus={FAKE_CONSENSUS} divergences={FAKE_DIVERGENCES} />
            }
          </div>
        </div>
      </div>

      {/* ── 窄屏单列 + 底部 tab ──────────────────── */}
      <div className="flex sm:hidden flex-1 min-h-0 flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto p-3" style={panelProps}>
          {mobileTab === 'panelists' && <PanelistGrid panelists={FAKE_PANELISTS} />}
          {mobileTab === 'transcript' && <TranscriptPanel utterances={FAKE_UTTERANCES} />}
          {mobileTab === 'consensus' && <ConsensusPanel consensus={FAKE_CONSENSUS} divergences={FAKE_DIVERGENCES} />}
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
