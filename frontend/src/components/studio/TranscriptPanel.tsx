/** Apple Studio — 现场 Transcript: 四面圆角玻璃气泡 + 发言人名字保留彩色 */
import { useEffect, useRef } from 'react';
import { getColor } from '../../utils/colors';

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
    <div className="space-y-3 px-1">
      {utterances.map((u, i) => {
        const { hex } = getColor(u.colorIndex);
        const isLatest = i === utterances.length - 1;

        return (
          <div
            data-testid="utterance-entry"
            key={i}
            className="p-3.5 rounded-[var(--radius-sm)] mb-3"
            style={{
              background: 'var(--glass-card-bg)',
              backdropFilter: 'blur(var(--glass-card-blur))',
              WebkitBackdropFilter: 'blur(var(--glass-card-blur))',
              border: '0.5px solid var(--border-default)',
              animation: isLatest ? 'slide-up 250ms var(--ease-apple)' : 'none',
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium"
                style={{ color: hex }}>
                {u.panelistName}
              </span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                {u.panelistTitle}
              </span>
            </div>
            <p className="text-body text-[13px]">
              {u.content}
            </p>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
