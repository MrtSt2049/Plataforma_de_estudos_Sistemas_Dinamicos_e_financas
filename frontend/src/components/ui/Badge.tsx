import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'

export type BadgeVariant =
  | 'success'
  | 'running'
  | 'failed'
  | 'queued'
  | 'demo'
  | 'dynamical'
  | 'active'
  | 'warning'

const variants: Record<BadgeVariant, string> = {
  success: 'border-pos/40 text-pos',
  running: 'border-analytic/50 text-analytic-text',
  failed: 'border-neg/50 text-neg-text',
  queued: 'border-line text-fg-muted',
  demo: 'border-warn/50 text-warn',
  dynamical: 'border-science/50 text-science-text',
  active: 'border-pos/40 text-pos',
  warning: 'border-warn/50 text-warn',
}

export function Badge({ variant, children }: { variant: BadgeVariant; children: ReactNode }) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-sm border px-1.5 py-px font-mono text-[10.5px] font-medium uppercase tracking-wider',
        variants[variant],
      )}
    >
      {children}
    </span>
  )
}
