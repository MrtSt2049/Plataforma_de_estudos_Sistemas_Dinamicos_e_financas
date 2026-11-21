import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { safeDestination } from '@/lib/safeDestination'
import { Skeleton } from './ui/Skeleton'

function FullScreenLoading() {
  return (
    <div className="grid min-h-screen place-items-center">
      <Skeleton label="Verificando sessão" lines={2} className="w-64" />
    </div>
  )
}

/** Sends visitors without a session to the login page, remembering where they were going. */
export function RequireAuth() {
  const { ready, session } = useAuth()
  const location = useLocation()
  if (!ready) return <FullScreenLoading />
  if (session === null) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

/** Login, sign-up and recovery pages: people who are already in go to the app. */
export function PublicOnly() {
  const { ready, session, recovering } = useAuth()
  const location = useLocation()
  if (!ready) return <FullScreenLoading />
  if (session !== null) {
    const from = (location.state as { from?: unknown } | null)?.from
    return <Navigate to={recovering ? '/update-password' : safeDestination(from)} replace />
  }
  return <Outlet />
}
