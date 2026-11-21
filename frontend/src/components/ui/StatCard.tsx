import { TrendingDown, TrendingUp } from 'lucide-react'
import type { ReactNode } from 'react'

export interface StatCardProps {
  label: string
  value: string | number
  change?: {
    value: string | number
    positive: boolean
  }
  unit?: string
  helperText?: string
  badge?: ReactNode
  className?: string
}

/**
 * Metric/KPI card adhering to QuantLab design principles:
 * - Tabular mono font for all numbers (`font-mono tabular-nums`)
 * - Color never appears alone: positive/negative always carries ▲/▼ (+/−)
 * - Dark panel background with subtle hairline border
 */
export function StatCard({
  label,
  value,
  change,
  unit,
  helperText,
  badge,
  className = '',
}: StatCardProps) {
  return (
    <div
      className={`flex flex-col gap-2 rounded-md border border-line bg-panel p-4 transition-colors ${className}`}
    >
      <div className="flex items-center justify-between text-xs text-fg-muted">
        <span>{label}</span>
        {badge}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
          {value}
        </span>
        {unit && <span className="text-xs text-fg-muted font-mono">{unit}</span>}
      </div>

      {(change || helperText) && (
        <div className="flex items-center justify-between text-xs">
          {change && (
            <span
              className={`flex items-center gap-1 font-mono font-medium ${
                change.positive ? 'text-pos' : 'text-neg-text'
              }`}
            >
              {change.positive ? (
                <>
                  <TrendingUp className="h-3 w-3" /> ▲ +{change.value}
                </>
              ) : (
                <>
                  <TrendingDown className="h-3 w-3" /> ▼ {change.value}
                </>
              )}
            </span>
          )}
          {helperText && <span className="text-fg-muted truncate">{helperText}</span>}
        </div>
      )}
    </div>
  )
}
