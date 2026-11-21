import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'

type Variant = 'primary' | 'secondary' | 'ghost'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  /** Shows a spinner and blocks clicks while an operation runs. */
  loading?: boolean
}

const base =
  'inline-flex h-8 items-center justify-center gap-2 rounded-md px-3 text-[13px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50'

const variants: Record<Variant, string> = {
  primary: 'bg-action text-white hover:bg-action/85',
  secondary: 'border border-line bg-surface text-fg hover:border-fg-muted',
  ghost: 'text-fg-muted hover:bg-surface hover:text-fg',
}

export function Button({
  variant = 'primary',
  loading = false,
  disabled,
  className,
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cx(base, variants[variant], className)}
      {...rest}
    >
      {loading && <Loader2 aria-hidden className="size-4 animate-spin" />}
      {children}
    </button>
  )
}
