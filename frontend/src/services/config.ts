/**
 * Runtime configuration, read from the VITE_* variables of the root `.env`.
 *
 * Everything here ends up in the browser bundle, so only public values are accepted:
 * a secret key or a `service_role` token is refused outright (RULE 028).
 */

export interface AppConfig {
  /** Project base URL, for example `https://<ref>.supabase.co` (no path). */
  supabaseUrl: string
  /** Publishable key (or the legacy `anon` key). Public by design. */
  supabasePublishableKey: string
  /** Django API base URL, or null while the backend is not configured. */
  apiBaseUrl: string | null
}

export class ConfigError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ConfigError'
  }
}

type Env = Readonly<Record<string, string | undefined>>

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1'])

function readJwtRole(token: string): string | null {
  const [, payload] = token.split('.')
  if (payload === undefined) return null
  try {
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const claims: unknown = JSON.parse(json)
    if (typeof claims === 'object' && claims !== null && 'role' in claims) {
      const role = (claims as { role: unknown }).role
      return typeof role === 'string' ? role : null
    }
  } catch {
    return null
  }
  return null
}

function parseHttpUrl(name: string, value: string): URL {
  let url: URL
  try {
    url = new URL(value)
  } catch {
    throw new ConfigError(`${name} is not a valid URL.`)
  }
  const secure = url.protocol === 'https:'
  const localHttp = url.protocol === 'http:' && LOCAL_HOSTS.has(url.hostname)
  if (!secure && !localHttp) {
    throw new ConfigError(`${name} must use https (http is allowed only for localhost).`)
  }
  return url
}

function requireVariable(env: Env, name: string): string {
  const value = env[name]?.trim()
  if (!value) {
    throw new ConfigError(`${name} is not set. Fill it in the .env at the repository root.`)
  }
  return value
}

export function loadConfig(env: Env = import.meta.env): AppConfig {
  const supabaseUrl = parseHttpUrl('VITE_SUPABASE_URL', requireVariable(env, 'VITE_SUPABASE_URL'))
  if (supabaseUrl.pathname !== '/' || supabaseUrl.search !== '') {
    throw new ConfigError(
      'VITE_SUPABASE_URL must be the project base URL, without a path (remove suffixes such as /rest/v1).',
    )
  }

  const key = requireVariable(env, 'VITE_SUPABASE_PUBLISHABLE_KEY')
  if (key.startsWith('sb_secret_')) {
    throw new ConfigError('VITE_SUPABASE_PUBLISHABLE_KEY holds a SECRET key. Use the publishable key.')
  }
  const isPublishable = key.startsWith('sb_publishable_')
  if (!isPublishable) {
    const role = readJwtRole(key)
    if (role === 'service_role') {
      throw new ConfigError('VITE_SUPABASE_PUBLISHABLE_KEY holds a service_role key. Use the publishable key.')
    }
    if (role !== 'anon') {
      throw new ConfigError('VITE_SUPABASE_PUBLISHABLE_KEY is not a publishable (or anon) key.')
    }
  }

  const rawApi = env.VITE_API_BASE_URL?.trim()
  const apiBaseUrl = rawApi ? parseHttpUrl('VITE_API_BASE_URL', rawApi).toString().replace(/\/+$/, '') : null

  return {
    supabaseUrl: supabaseUrl.origin,
    supabasePublishableKey: key,
    apiBaseUrl,
  }
}

export type ConfigResult = { ok: true; config: AppConfig } | { ok: false; error: ConfigError }

export function tryLoadConfig(env: Env = import.meta.env): ConfigResult {
  try {
    return { ok: true, config: loadConfig(env) }
  } catch (error) {
    if (error instanceof ConfigError) return { ok: false, error }
    throw error
  }
}
