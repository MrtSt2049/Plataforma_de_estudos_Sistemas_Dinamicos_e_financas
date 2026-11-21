import { apiRequest } from './apiClient'

export interface Health {
  status: string
  version: string
}

function parseHealth(data: unknown): Health {
  if (typeof data === 'object' && data !== null) {
    const record = data as Record<string, unknown>
    if (typeof record.status === 'string' && typeof record.version === 'string') {
      return { status: record.status, version: record.version }
    }
  }
  throw new Error('invalid health response')
}

/** `GET /v1/health`, the backend's liveness route (plan B5). */
export function fetchHealth(signal?: AbortSignal): Promise<Health> {
  return apiRequest('/v1/health', signal ? { parse: parseHealth, signal } : { parse: parseHealth })
}
