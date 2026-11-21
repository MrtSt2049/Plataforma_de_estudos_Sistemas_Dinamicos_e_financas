import { NavLink } from 'react-router-dom'
import { cx } from '@/lib/cx'
import { navigation } from '@/navigation'
import { Brand } from './Brand'

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Principal" className="flex h-full w-60 flex-col gap-5 overflow-y-auto border-r border-line bg-panel px-3 py-4">
      <div className="px-2">
        <Brand />
      </div>
      {navigation.map((group) => (
        <div key={group.label} className="flex flex-col gap-0.5">
          <p className="px-2 pb-1 text-[10.5px] font-semibold uppercase tracking-[0.08em] text-fg-muted">{group.label}</p>
          {group.items.map((item) => {
            const Icon = item.icon
            const content = (
              <>
                <Icon aria-hidden className="size-4 shrink-0" />
                <span className="flex-1 truncate">{item.label}</span>
                {!item.ready && <span className="font-mono text-[10px] uppercase tracking-wider">em breve</span>}
              </>
            )
            if (!item.ready) {
              return (
                <span
                  key={item.to}
                  aria-disabled="true"
                  className="flex h-[30px] items-center gap-2 rounded-md px-2 text-fg-muted/70"
                >
                  {content}
                </span>
              )
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end
                onClick={onNavigate}
                className={({ isActive }) =>
                  cx(
                    'flex h-[30px] items-center gap-2 rounded-md px-2 hover:bg-surface',
                    isActive ? 'bg-surface text-fg' : 'text-fg-muted',
                  )
                }
              >
                {content}
              </NavLink>
            )
          })}
        </div>
      ))}
    </nav>
  )
}
