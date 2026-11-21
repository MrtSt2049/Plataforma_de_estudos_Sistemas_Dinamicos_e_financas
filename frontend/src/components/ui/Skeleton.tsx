import { cx } from '@/lib/cx'

/** Placeholder shown while data loads. It announces itself as busy. */
export function Skeleton({ label = 'Carregando', lines = 3, className }: { label?: string; lines?: number; className?: string }) {
  return (
    <div role="status" aria-busy="true" aria-label={label} className={cx('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={index}
          className="h-3 animate-pulse rounded-sm bg-surface"
          style={{ width: `${index === lines - 1 ? 55 : 100}%` }}
        />
      ))}
    </div>
  )
}
