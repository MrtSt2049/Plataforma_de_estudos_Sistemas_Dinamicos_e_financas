import type { ReactNode } from 'react'

export interface TabItem {
  id: string
  label: string
  icon?: ReactNode
  badge?: ReactNode
}

export interface TabsProps {
  tabs: readonly TabItem[]
  activeTab: string
  onChange: (id: string) => void
  className?: string
}

export function Tabs({ tabs, activeTab, onChange, className = '' }: TabsProps) {
  return (
    <div className={`flex border-b border-line gap-1 ${className}`}>
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-medium transition-colors border-b-2 -mb-px ${
              isActive
                ? 'border-analytic text-fg bg-surface/50'
                : 'border-transparent text-fg-muted hover:text-fg hover:border-line'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.badge}
          </button>
        )
      })}
    </div>
  )
}
