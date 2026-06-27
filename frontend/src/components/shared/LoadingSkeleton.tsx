interface LoadingSkeletonProps {
  /** 骨架条数 */
  lines?: number;
  /** 是否显示圆形（模拟头像/色块） */
  withCircle?: boolean;
}

const SKELETON_BG = 'rgba(255, 255, 255, 0.06)';

export default function LoadingSkeleton({ lines = 3, withCircle = false }: LoadingSkeletonProps) {
  return (
    <div className="animate-pulse p-4 space-y-3" role="status" aria-label="加载中">
      {withCircle && (
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full" style={{ background: SKELETON_BG }} />
          <div className="flex-1 space-y-2">
            <div className="h-3 rounded-[16px]" style={{ background: SKELETON_BG, width: '40%' }} />
            <div className="h-2.5 rounded-[16px]" style={{ background: SKELETON_BG, width: '25%' }} />
          </div>
        </div>
      )}
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 rounded-[16px]"
          style={{
            background: SKELETON_BG,
            width: i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  );
}
