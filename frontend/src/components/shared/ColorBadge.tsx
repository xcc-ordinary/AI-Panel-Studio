import { getColor } from '../../utils/colors';

interface ColorBadgeProps {
  /** sort_order 索引，0=主持人 */
  colorIndex: number;
  size?: 'sm' | 'md';
}

export default function ColorBadge({ colorIndex, size = 'sm' }: ColorBadgeProps) {
  const { hex, soft } = getColor(colorIndex);
  const dims = size === 'md' ? 'w-3 h-3' : 'w-2.5 h-2.5';

  return (
    <span
      className={`inline-block ${dims} rounded-full shrink-0`}
      style={{
        background: hex,
        boxShadow: `0 0 6px ${soft}`,
      }}
      aria-hidden="true"
    />
  );
}
