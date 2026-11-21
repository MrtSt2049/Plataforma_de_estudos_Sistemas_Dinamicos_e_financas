import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// The root .env is never read by the tests: every run starts from fixed, fake values.
beforeEach(() => {
  vi.stubEnv('VITE_SUPABASE_URL', 'https://example.supabase.co')
  vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test_key')
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000/api')
})

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
})
