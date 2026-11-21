import { describe, expect, it, vi } from 'vitest'
import { apiRequest, ApiError, type ApiDeps } from './apiClient'

const parse = (data: unknown) => data as { value: number }

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function makeDeps(responses: Array<Response | Error | DOMException>, overrides: Partial<ApiDeps> = {}) {
  const queue = [...responses]
  const fetchFn = vi.fn((): Promise<Response> => {
    const next = queue.shift()
    if (next === undefined) throw new Error('unexpected extra request')
    // Anything that is not a Response is a failure of the request itself.
    return next instanceof Response ? Promise.resolve(next) : Promise.reject(next)
  })
  const deps: ApiDeps = {
    baseUrl: 'http://localhost:8000/api',
    getAccessToken: vi.fn(() => Promise.resolve<string | null>('token-1')),
    refreshAccessToken: vi.fn(() => Promise.resolve<string | null>('token-2')),
    onUnauthorized: vi.fn(() => Promise.resolve()),
    fetchFn: fetchFn as unknown as typeof fetch,
    ...overrides,
  }
  return { deps, fetchFn }
}

async function failure(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    if (error instanceof ApiError) return error
    throw error
  }
  throw new Error('expected the request to fail')
}

describe('apiRequest', () => {
  it('sends the access token and returns the parsed body', async () => {
    const { deps, fetchFn } = makeDeps([json({ value: 7 })])
    await expect(apiRequest('/v1/x', { parse }, deps)).resolves.toEqual({ value: 7 })
    const [url, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8000/api/v1/x')
    expect(init.method).toBe('GET')
    expect(init.headers).toMatchObject({ Authorization: 'Bearer token-1', Accept: 'application/json' })
    expect(init.body).toBeUndefined()
  })

  it('sends a JSON body with its content type', async () => {
    const { deps, fetchFn } = makeDeps([json({ value: 1 }, 201)])
    await apiRequest('/v1/x', { method: 'POST', body: { a: 1 }, parse }, deps)
    const [, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"a":1}')
    expect(init.headers).toMatchObject({ 'Content-Type': 'application/json' })
  })

  it('says so when the API is not configured, without any request', async () => {
    const { deps, fetchFn } = makeDeps([], { baseUrl: null })
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error.code).toBe('api_not_configured')
    expect(fetchFn).not.toHaveBeenCalled()
  })

  it('does not call the API without a session', async () => {
    const { deps, fetchFn } = makeDeps([], { getAccessToken: () => Promise.resolve(null) })
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error.status).toBe(401)
    expect(fetchFn).not.toHaveBeenCalled()
  })

  it.each(['v1/x', '//evil.example/x', 'https://evil.example/x'])(
    'refuses the path %s, so the token cannot be sent to another host',
    async (path) => {
      const { deps, fetchFn } = makeDeps([])
      await expect(apiRequest(path, { parse }, deps)).rejects.toThrow(/single "\/"/)
      expect(fetchFn).not.toHaveBeenCalled()
    },
  )

  it('renews the session once on a 401 and retries with the new token', async () => {
    const { deps, fetchFn } = makeDeps([json({}, 401), json({ value: 2 })])
    await expect(apiRequest('/v1/x', { parse }, deps)).resolves.toEqual({ value: 2 })
    expect(deps.refreshAccessToken).toHaveBeenCalledTimes(1)
    const [, retry] = fetchFn.mock.calls[1] as unknown as [string, RequestInit]
    expect(retry.headers).toMatchObject({ Authorization: 'Bearer token-2' })
    expect(deps.onUnauthorized).not.toHaveBeenCalled()
  })

  it('signs the user out when the session cannot be renewed', async () => {
    const { deps } = makeDeps([json({}, 401)], { refreshAccessToken: () => Promise.resolve(null) })
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error.status).toBe(401)
    expect(deps.onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('signs the user out when the retry is also refused, and does not loop', async () => {
    const { deps, fetchFn } = makeDeps([json({}, 401), json({}, 401)])
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error.code).toBe('unauthorized')
    expect(fetchFn).toHaveBeenCalledTimes(2)
    expect(deps.onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('turns a network failure into a friendly error', async () => {
    const { deps } = makeDeps([new TypeError('Failed to fetch')])
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error).toMatchObject({ status: 0, code: 'network' })
  })

  it('lets an abort pass through unchanged', async () => {
    const { deps } = makeDeps([new DOMException('aborted', 'AbortError')])
    await expect(apiRequest('/v1/x', { parse }, deps)).rejects.toMatchObject({ name: 'AbortError' })
  })

  it('uses the message and code of an error body', async () => {
    const { deps } = makeDeps([json({ detail: 'Símbolo não encontrado.', code: 'symbol_not_found' }, 404)])
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error).toMatchObject({ status: 404, message: 'Símbolo não encontrado.', code: 'symbol_not_found' })
  })

  it('falls back to a generic message when the error body is not JSON', async () => {
    const { deps } = makeDeps([new Response('<html>oops</html>', { status: 502 })])
    const error = await failure(apiRequest('/v1/x', { parse }, deps))
    expect(error).toMatchObject({ status: 502, code: 'http_error' })
    expect(error.message).toContain('502')
  })

  it('rejects a success response that is not JSON', async () => {
    const { deps } = makeDeps([new Response('not json', { status: 200 })])
    expect((await failure(apiRequest('/v1/x', { parse }, deps))).code).toBe('invalid_response')
  })

  it('rejects a body the validator does not accept', async () => {
    const { deps } = makeDeps([json({ unexpected: true })])
    const strict = (data: unknown) => {
      if (typeof data === 'object' && data !== null && 'value' in data) return data
      throw new Error('bad shape')
    }
    expect((await failure(apiRequest('/v1/x', { parse: strict }, deps))).code).toBe('invalid_response')
  })

  it('passes an empty 204 body to the validator', async () => {
    const { deps } = makeDeps([new Response(null, { status: 204 })])
    await expect(apiRequest('/v1/x', { method: 'DELETE', parse: () => 'gone' }, deps)).resolves.toBe('gone')
  })
})
