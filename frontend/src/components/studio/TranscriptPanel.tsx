/** MASTER.md §5.3 — 现场 Transcript: 嘉宾色左边框 + 姓名/Title/内容 + 最新条 slide-up */
import { useEffect, useRef } from 'react';

interface FakeUtterance {
  panelistName: string;
  panelistTitle: string;
  colorIndex: number;
  content: string;
}

interface TranscriptPanelProps {
  utterances: FakeUtterance[];
}

export default function TranscriptPanel({ utterances }: TranscriptPanelProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [utterances]);

  return (
    <div className="space-y-1 px-1">
      {utterances.map((u, i) => {
        const colorHex = [
          '#38BDF8','#F87171','#818CF8','#FBBF24','#A78BFA',
          '#FB923C','#E879F9','#2DD4BF','#FCA5A5',
        ][u.colorIndex % 9];
        const isLatest = i === utterances.length - 1;

        return (
          <div
            data-testid="utterance-entry"
            key={i}
            className="p-2.5 rounded-r-[var(--radius-sm)] mb-1"
            style={{
              background: 'var(--bg-surface)',
              borderLeft: `3px solid ${colorHex}`,
              animation: isLatest ? 'slide-up 250ms var(--ease-out)' : 'none',
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold"
                style={{ fontFamily: 'var(--font-heading)', color: colorHex }}>
                {u.panelistName}
              </span>
              <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                {u.panelistTitle}
              </span>
            </div>
            <p className="text-[14px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
              {u.content}
            </p>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
