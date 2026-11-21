import { loadConfig } from './config'
import { getSupabase } from './supabase'

export type ApiErrorCode =
  | 'api_not_configured'
  | 'network'
  | 'unauthorized'
  | 'invalid_response'
  | (string & {})

/** An error from the API, already in a shape the interface can show (RULE 034). */
export class ApiError extends Error {
  readonly status: number
  readonly code: ApiErrorCode

  constructor(message: string, status: number, code: ApiErrorCode) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export interface ApiRequest<T> {
  method?: 'GET' | 'POST' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  /** Validates the JSON body; the types of the API are not trusted blindly. */
  parse: (data: unknown) => T
}

/** What the client needs from the outside; injected so tests need no network. */
export interface ApiDeps {
  baseUrl: string | null
  getAccessToken: () => Promise<string | null>
  refreshAccessToken: () => Promise<string | null>
  onUnauthorized: () => Promise<void>
  fetchFn: typeof fetch
}

export function defaultApiDeps(): ApiDeps {
  const { apiBaseUrl } = loadConfig()
  const auth = getSupabase().auth
  return {
    baseUrl: apiBaseUrl,
    getAccessToken: async () => (await auth.getSession()).data.session?.access_token ?? null,
    refreshAccessToken: async () => (await auth.refreshSession()).data.session?.access_token ?? null,
    onUnauthorized: async () => {
      await auth.signOut()
    },
    fetchFn: (input, init) => fetch(input, init),
  }
}

async function readErrorBody(response: Response): Promise<{ message: string | null; code: string | null }> {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null) {
      const record = body as Record<string, unknown>
      const message = [record.detail, record.message].find((value) => typeof value === 'string')
      const code = typeof record.code === 'string' ? record.code : null
      return { message: typeof message === 'string' ? message : null, code }
    }
  } catch {
    // Not JSON: fall back to the status text.
  }
  return { message: null, code: null }
}

async function send(
  deps: ApiDeps,
  url: string,
  token: string,
  method: string,
  body: unknown,
  signal: AbortSignal | undefined,
): Promise<Response> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    Authorization: `Bearer ${token}`,
  }
  const init: RequestInit = { method, headers }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }
  if (signal) init.signal = signal
  try {
    return await deps.fetchFn(url, init)
  } catch (error) {
    // By name, not instanceof: it also works across realms (jsdom, workers).
    if (typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError') throw error
    throw new ApiError('Não foi possível conectar à API. Verifique a conexão e tente de novo.', 0, 'network')
  }
}

/**
 * Calls the Django API with the user's access token.
 *
 * On a 401 it renews the session once and retries; if that fails the user is signed out.
 * The token is only ever sent to the configured API origin.
 */
export async function apiRequest<T>(
  path: string,
  request: ApiRequest<T>,
  deps: ApiDeps = defaultApiDeps(),
): Promise<T> {
  if (deps.baseUrl === null) {
    throw new ApiError('A API ainda não está configurada (VITE_API_BASE_URL).', 0, 'api_not_configured')
  }
  if (!path.startsWith('/') || path.startsWith('//')) {
    throw new Error(`API paths must start with a single "/": ${path}`)
  }
  const url = `${deps.baseUrl}${path}`
  const method = request.method ?? 'GET'

  let token = await deps.getAccessToken()
  if (token === null) throw new ApiError('Sessão ausente. Entre novamente.', 401, 'unauthorized')

  let response = await send(deps, url, token, method, request.body, request.signal)
  if (response.status === 401) {
    token = await deps.refreshAccessToken()
    if (token !== null) response = await send(deps, url, token, method, request.body, request.signal)
    if (token === null || response.status === 401) {
      await deps.onUnauthorized()
      throw new ApiError('Sua sessão expirou. Entre novamente.', 401, 'unauthorized')
    }
  }

  if (!response.ok) {
    const { message, code } = await readErrorBody(response)
    throw new ApiError(message ?? `A API respondeu com erro ${response.status}.`, response.status, code ?? 'http_error')
  }
  if (response.status === 204) return request.parse(undefined)

  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new ApiError('A API devolveu uma resposta que não é JSON.', response.status, 'invalid_response')
  }
  try {
    return request.parse(data)
  } catch {
    throw new ApiError('A resposta da API não tem o formato esperado.', response.status, 'invalid_response')
  }
}
