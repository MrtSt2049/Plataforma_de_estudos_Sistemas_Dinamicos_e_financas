import type { ReactNode } from 'react'
import { ApiError } from '@/services/apiClient'
import { ErrorState } from './ui/ErrorState'
import { Skeleton } from './ui/Skeleton'

/** The part of a TanStack Query result the boundary needs. */
export interface AsyncQuery<T> {
  status: 'pending' | 'error' | 'success'
  data: T | undefined
  error: unknown
  refetch: () => unknown
}

export interface AsyncBoundaryProps<T> {
  query: AsyncQuery<T>
  /** What to show when the request worked but there is nothing to display. */
  empty: ReactNode
  isEmpty?: (data: T) => boolean
  /** Shown instead of the generic error for errors it recognises (for example "API not configured"). */
  errorOverride?: (error: unknown) => ReactNode | null
  children: (data: T) => ReactNode
}

function messageOf(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Não foi possível carregar os dados.'
}

/**
 * Every asynchronous screen has four states (RULE 034): loading, error, empty and success.
 * This component makes it impossible to forget one of them.
 */
export function AsyncBoundary<T>({ query, empty, isEmpty, errorOverride, children }: AsyncBoundaryProps<T>) {
  if (query.status === 'pending') return <Skeleton />
  if (query.status === 'error') {
    const override = errorOverride?.(query.error)
    if (override) return <>{override}</>
    return <ErrorState message={messageOf(query.error)} onRetry={() => void query.refetch()} />
  }
  const data = query.data as T
  if (isEmpty?.(data)) return <>{empty}</>
  return <>{children(data)}</>
}
