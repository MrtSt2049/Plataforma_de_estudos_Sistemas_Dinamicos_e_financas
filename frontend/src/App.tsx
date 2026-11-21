import { QueryClientProvider } from '@tanstack/react-query'
import { lazy, useState } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthProvider'
import { createQueryClient } from '@/queryClient'
import { AppRoutes } from '@/routes'
import { tryLoadConfig } from '@/services/config'

const ConfigErrorPage = lazy(() => import('@/pages/ConfigErrorPage'))

export default function App() {
  const [config] = useState(() => tryLoadConfig())
  const [queryClient] = useState(createQueryClient)

  // A wrong .env is reported on screen, with the reason, instead of a blank page.
  if (!config.ok) return <ConfigErrorPage error={config.error} />

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
