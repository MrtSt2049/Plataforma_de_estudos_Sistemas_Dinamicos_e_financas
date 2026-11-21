import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'

export interface PanelProps {
  title: string
  /** Optional element on the right of the header, usually a Badge. */
  aside?: ReactNode
  className?: string
  children: ReactNode
}

export function Panel({ title, aside, className, children }: PanelProps) {
  return (
    <section className={cx('rounded-lg border border-line bg-panel', className)}>
      <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider">{title}</h2>
        {aside}
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}
