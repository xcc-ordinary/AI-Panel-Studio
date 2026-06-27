/** Apple Studio — 共识与分歧面板: 玻璃卡片 + 软色底代替彩色边框 */
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface FakeConsensus {
  id: string;
  content: string;
  isNew?: boolean;
  involvedNames: string[];
}

interface FakeDivergence {
  id: string;
  description: string;
  camps: { position: string; names: string[] }[];
  isNew?: boolean;
}

interface ConsensusPanelProps {
  consensus: FakeConsensus[];
  divergences: FakeDivergence[];
}

export default function ConsensusPanel({ consensus, divergences }: ConsensusPanelProps) {
  return (
    <div className="space-y-6 px-1">
      {/* Consensus */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2"
          style={{ color: 'var(--accent-positive)' }}>
          <CheckCircle2 size={14} strokeWidth={1.5} />
          已形成共识
        </h3>
        {consensus.length === 0 && (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>暂无共识形成…</p>
        )}
        <div className="space-y-2">
          {consensus.map(c => (
            <div
              data-testid="consensus-card"
              key={c.id}
              className="p-3 rounded-[16px] border transition-all duration-[var(--duration-normal)]"
              style={{
                background: 'rgba(48,209,88,0.05)',
                borderColor: c.isNew ? 'rgba(48,209,88,0.20)' : 'var(--glass-border)',
                animation: c.isNew ? 'glow-brief 250ms ease-out' : 'none',
              }}
            >
              <p className="text-[14px] leading-relaxed mb-2" style={{ color: 'var(--text-primary)' }}>
                {c.content}
              </p>
              <div className="flex flex-wrap gap-1">
                {c.involvedNames.map(n => (
                  <span key={n} className="text-[10px] px-1.5 py-px rounded-full"
                    style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)' }}>
                    {n}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Divergence */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2"
          style={{ color: 'var(--accent-divergence)' }}>
          <AlertTriangle size={14} strokeWidth={1.5} />
          存在分歧
        </h3>
        {divergences.length === 0 && (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>暂无分歧…</p>
        )}
        <div className="space-y-2">
          {divergences.map(d => (
            <div
              data-testid="divergence-card"
              key={d.id}
              className="p-3 rounded-[16px] border transition-all duration-[var(--duration-normal)]"
              style={{
                background: 'rgba(255,159,10,0.05)',
                borderColor: d.isNew ? 'rgba(255,159,10,0.20)' : 'var(--glass-border)',
                animation: d.isNew ? 'glow-brief 250ms ease-out' : 'none',
              }}
            >
              <p className="text-[14px] leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
                {d.description}
              </p>
              {d.camps.map((camp, ci) => (
                <div key={ci} className="mb-1.5 last:mb-0">
                  <p className="text-[11px] font-medium mb-0.5" style={{ color: 'var(--accent-divergence)' }}>
                    {camp.position}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {camp.names.map(n => (
                      <span key={n} className="text-[10px] px-1.5 py-px rounded-full"
                        style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)' }}>
                        {n}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
