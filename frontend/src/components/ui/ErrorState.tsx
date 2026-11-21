import { Button } from './Button'

export interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorState({ title = 'Algo deu errado', message, onRetry }: ErrorStateProps) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 rounded-md border border-neg/40 bg-neg/5 px-4 py-3">
      <p className="font-semibold text-neg-text">{title}</p>
      <p className="text-fg">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Tentar de novo
        </Button>
      )}
    </div>
  )
}
