import type { ReactNode } from 'react'

export interface EmptyStateProps {
  title: string
  description: string
  /** The action that resolves the emptiness, when there is one. */
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-md border border-dashed border-line px-6 py-8 text-center">
      <p className="text-[13px] font-semibold">{title}</p>
      <p className="max-w-md text-fg-muted">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
