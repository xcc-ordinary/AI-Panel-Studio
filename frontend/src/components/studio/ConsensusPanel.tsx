/** MASTER.md §5.4 — 共识与分歧面板: 共识绿描边 + 分歧琥珀描边 + 阵营展示 */
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
    <div className="space-y-5 px-1">
      {/* 已形成共识 */}
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
              key={c.id}
              className="p-3 rounded-[var(--radius-md)] border transition-all duration-[var(--duration-normal)]"
              style={{
                background: 'var(--bg-surface)',
                borderColor: c.isNew ? 'var(--accent-positive)' : 'var(--border-default)',
                boxShadow: c.isNew ? '0 0 0 1px var(--accent-positive)' : 'none',
                animation: c.isNew ? 'glow-brief 250ms ease-out' : 'none',
              }}
            >
              <p className="text-[14px] leading-relaxed mb-2" style={{ color: 'var(--text-primary)' }}>
                {c.content}
              </p>
              <div className="flex flex-wrap gap-1">
                {c.involvedNames.map(n => (
                  <span key={n} className="text-[10px] px-1.5 py-px rounded-full"
                    style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--accent-positive)' }}>
                    {n}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 存在分歧 */}
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
              key={d.id}
              className="p-3 rounded-[var(--radius-md)] border transition-all duration-[var(--duration-normal)]"
              style={{
                background: 'var(--bg-surface)',
                borderColor: d.isNew ? 'var(--accent-divergence)' : 'var(--border-default)',
                boxShadow: d.isNew ? '0 0 0 1px var(--accent-divergence)' : 'none',
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
                        style={{ background: 'rgba(245,158,11,0.1)', color: 'var(--accent-divergence)' }}>
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
