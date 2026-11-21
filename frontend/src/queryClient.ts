import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/services/apiClient'

const MAX_RETRIES = 2

/** Client errors (4xx) will not fix themselves, so only network and server failures are retried. */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
  if (error instanceof ApiError && error.code === 'api_not_configured') return false
  return failureCount < MAX_RETRIES
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: shouldRetry, staleTime: 30_000, refetchOnWindowFocus: false },
    },
  })
}
