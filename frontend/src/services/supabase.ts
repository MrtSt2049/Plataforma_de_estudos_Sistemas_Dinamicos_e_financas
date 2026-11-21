import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import { loadConfig } from './config'

let client: SupabaseClient | null = null

/**
 * The Supabase client, created on first use so that a bad configuration is reported by
 * the app (see ConfigGate) instead of failing at import time.
 *
 * It is used for authentication only. Business data goes through the Django API
 * (RULE 001), so the browser never writes to the database.
 */
export function getSupabase(): SupabaseClient {
  if (client === null) {
    const config = loadConfig()
    client = createClient(config.supabaseUrl, config.supabasePublishableKey)
  }
  return client
}

/** Test helper: forgets the cached client. */
export function resetSupabaseClient(): void {
  client = null
}
