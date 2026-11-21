import { describe, expect, it } from 'vitest'
import { ConfigError, loadConfig, tryLoadConfig } from './config'

const base = {
  VITE_SUPABASE_URL: 'https://abc.supabase.co',
  VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_abc123',
} as const

function jwt(claims: object): string {
  const encode = (value: object) => btoa(JSON.stringify(value)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
  return `${encode({ alg: 'HS256' })}.${encode(claims)}.signature`
}

describe('loadConfig', () => {
  it('accepts the project URL and a publishable key', () => {
    expect(loadConfig(base)).toEqual({
      supabaseUrl: 'https://abc.supabase.co',
      supabasePublishableKey: 'sb_publishable_abc123',
      apiBaseUrl: null,
    })
  })

  it('accepts the legacy anon JWT', () => {
    const key = jwt({ role: 'anon' })
    expect(loadConfig({ ...base, VITE_SUPABASE_PUBLISHABLE_KEY: key }).supabasePublishableKey).toBe(key)
  })

  it('normalizes the project URL and the API URL', () => {
    const config = loadConfig({ ...base, VITE_SUPABASE_URL: 'https://abc.supabase.co/', VITE_API_BASE_URL: 'http://localhost:8000/api/' })
    expect(config.supabaseUrl).toBe('https://abc.supabase.co')
    expect(config.apiBaseUrl).toBe('http://localhost:8000/api')
  })

  it('treats a blank API URL as not configured', () => {
    expect(loadConfig({ ...base, VITE_API_BASE_URL: '  ' }).apiBaseUrl).toBeNull()
  })

  it('allows http only for localhost', () => {
    expect(loadConfig({ ...base, VITE_SUPABASE_URL: 'http://127.0.0.1:54321' }).supabaseUrl).toBe('http://127.0.0.1:54321')
    expect(() => loadConfig({ ...base, VITE_SUPABASE_URL: 'http://abc.supabase.co' })).toThrow(/https/)
    expect(() => loadConfig({ ...base, VITE_API_BASE_URL: 'http://api.example.com' })).toThrow(/https/)
  })

  it.each(['VITE_SUPABASE_URL', 'VITE_SUPABASE_PUBLISHABLE_KEY'] as const)('requires %s', (name) => {
    expect(() => loadConfig({ ...base, [name]: undefined })).toThrow(new RegExp(name))
    expect(() => loadConfig({ ...base, [name]: '   ' })).toThrow(ConfigError)
  })

  it.each(['https://abc.supabase.co/rest/v1/', 'https://abc.supabase.co/auth/v1', 'https://abc.supabase.co/?x=1'])(
    'rejects a project URL with a path or query: %s',
    (url) => {
      expect(() => loadConfig({ ...base, VITE_SUPABASE_URL: url })).toThrow(/base URL/)
    },
  )

  it('rejects text that is not a URL', () => {
    expect(() => loadConfig({ ...base, VITE_SUPABASE_URL: 'not a url' })).toThrow(/valid URL/)
  })

  it('refuses a secret key: it would ship to every visitor', () => {
    expect(() => loadConfig({ ...base, VITE_SUPABASE_PUBLISHABLE_KEY: 'sb_secret_abc123' })).toThrow(/SECRET/)
  })

  it('refuses a service_role JWT', () => {
    expect(() => loadConfig({ ...base, VITE_SUPABASE_PUBLISHABLE_KEY: jwt({ role: 'service_role' }) })).toThrow(/service_role/)
  })

  it.each(['plain-text', 'a.b.c', jwt({ role: 'authenticated' }), jwt({ no: 'role' })])('refuses an unrecognised key: %s', (key) => {
    expect(() => loadConfig({ ...base, VITE_SUPABASE_PUBLISHABLE_KEY: key })).toThrow(/not a publishable/)
  })
})

describe('tryLoadConfig', () => {
  it('returns the error instead of throwing', () => {
    const result = tryLoadConfig({})
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error).toBeInstanceOf(ConfigError)
  })

  it('returns the configuration when it is valid', () => {
    const result = tryLoadConfig(base)
    expect(result.ok).toBe(true)
  })
})
