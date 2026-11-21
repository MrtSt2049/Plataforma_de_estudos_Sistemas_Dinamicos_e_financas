import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { PublicOnly, RequireAuth } from '@/components/RouteGuards'
import { Skeleton } from '@/components/ui/Skeleton'

// One chunk per screen, so the heavy ones are not part of the first load.
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const SignupPage = lazy(() => import('@/pages/SignupPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'))
const UpdatePasswordPage = lazy(() => import('@/pages/UpdatePasswordPage'))
const OverviewPage = lazy(() => import('@/pages/OverviewPage'))
const MarketAnalysisPage = lazy(() => import('@/pages/MarketAnalysisPage'))
const DynamicalSystemsPage = lazy(() => import('@/pages/DynamicalSystemsPage'))
const ResearchLabPage = lazy(() => import('@/pages/ResearchLabPage'))
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
            <Route path="/mercados" element={<MarketAnalysisPage />} />
            <Route path="/retornos" element={<MarketAnalysisPage />} />
            <Route path="/risco" element={<MarketAnalysisPage />} />
            <Route path="/dinamica/logistico" element={<DynamicalSystemsPage />} />
            <Route path="/dinamica/lorenz" element={<DynamicalSystemsPage />} />
            <Route path="/projetos" element={<ResearchLabPage />} />
            <Route path="/experimentos" element={<ResearchLabPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
