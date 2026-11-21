import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { PublicOnly, RequireAuth } from '@/components/RouteGuards'
import { Skeleton } from '@/components/ui/Skeleton'

// One chunk per screen, so the heavy ones (charts, later) are not part of the first load.
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const SignupPage = lazy(() => import('@/pages/SignupPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'))
const UpdatePasswordPage = lazy(() => import('@/pages/UpdatePasswordPage'))
const OverviewPage = lazy(() => import('@/pages/OverviewPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

export function AppRoutes() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center">
          <Skeleton lines={2} className="w-64" />
        </div>
      }
    >
      <Routes>
        <Route element={<PublicOnly />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        </Route>
        <Route element={<RequireAuth />}>
          <Route path="/update-password" element={<UpdatePasswordPage />} />
          <Route element={<AppShell />}>
            <Route index element={<OverviewPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
