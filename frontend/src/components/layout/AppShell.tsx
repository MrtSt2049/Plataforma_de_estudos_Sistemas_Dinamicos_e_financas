import { Menu } from 'lucide-react'
import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '../ui/Button'
import { Sidebar } from './Sidebar'

/** Sidebar, top bar and the page. Below `lg` the sidebar opens over the page (RULE 036). */
export function AppShell() {
  const { user, signOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:block">
        <Sidebar />
      </div>
      {menuOpen && (
        <div className="fixed inset-0 z-20 flex lg:hidden">
          <Sidebar onNavigate={() => setMenuOpen(false)} />
          <button
            type="button"
            aria-label="Fechar menu"
            className="flex-1 bg-canvas/70"
            onClick={() => setMenuOpen(false)}
          />
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 items-center gap-3 border-b border-line px-4">
          <Button
            variant="ghost"
            className="lg:hidden"
            aria-label="Abrir menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(true)}
          >
            <Menu aria-hidden className="size-4" />
          </Button>
          <div className="flex-1" />
          <span className="hidden truncate text-fg-muted sm:inline" title={user?.email ?? ''}>
            {user?.email}
          </span>
          <Button variant="secondary" onClick={() => void signOut()}>
            Sair
          </Button>
        </header>
        <main className="flex-1 px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
