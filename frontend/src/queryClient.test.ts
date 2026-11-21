import { describe, expect, it } from 'vitest'
import { shouldRetry } from './queryClient'
import { ApiError } from './services/apiClient'

describe('shouldRetry', () => {
  it('does not retry client errors, which will not fix themselves', () => {
    expect(shouldRetry(0, new ApiError('x', 404, 'not_found'))).toBe(false)
    expect(shouldRetry(0, new ApiError('x', 401, 'unauthorized'))).toBe(false)
  })

  it('does not retry a missing configuration', () => {
    expect(shouldRetry(0, new ApiError('x', 0, 'api_not_configured'))).toBe(false)
  })

  it('retries network and server failures a limited number of times', () => {
    expect(shouldRetry(0, new ApiError('x', 0, 'network'))).toBe(true)
    expect(shouldRetry(1, new ApiError('x', 503, 'http_error'))).toBe(true)
    expect(shouldRetry(2, new ApiError('x', 503, 'http_error'))).toBe(false)
  })

  it('retries unknown errors too, within the limit', () => {
    expect(shouldRetry(0, new Error('boom'))).toBe(true)
    expect(shouldRetry(5, new Error('boom'))).toBe(false)
  })
})
