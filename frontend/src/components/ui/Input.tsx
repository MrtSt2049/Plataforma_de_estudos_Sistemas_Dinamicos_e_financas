import { useId, type InputHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  /** Error message; marks the field invalid and is announced to screen readers. */
  error?: string
  hint?: string
}

export function Input({ label, error, hint, id, className, ...rest }: InputProps) {
  const generated = useId()
  const inputId = id ?? generated
  const messageId = `${inputId}-message`
  const message = error ?? hint

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="text-[11px] font-medium uppercase tracking-wider text-fg-muted">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={message ? messageId : undefined}
        className={cx(
          'h-8 rounded-md border bg-surface px-2.5 text-[13px] text-fg placeholder:text-fg-muted/70 disabled:cursor-not-allowed disabled:opacity-50',
          error ? 'border-neg' : 'border-line focus:border-analytic',
          className,
        )}
        {...rest}
      />
      {message && (
        <p id={messageId} role={error ? 'alert' : undefined} className={cx('text-xs', error ? 'text-neg-text' : 'text-fg-muted')}>
          {message}
        </p>
      )}
    </div>
  )
}
