import type { Session, User } from '@supabase/supabase-js'
import { createContext } from 'react'

export type AuthResult = { ok: true } | { ok: false; message: string }
export type SignUpResult = { ok: true; needsConfirmation: boolean } | { ok: false; message: string }

export interface AuthContextValue {
  /** False until Supabase reports the initial session, so guards do not flash the login page. */
  ready: boolean
  session: Session | null
  user: User | null
  /** True after the user opens a password-recovery link. */
  recovering: boolean
  signIn: (email: string, password: string) => Promise<AuthResult>
  signUp: (email: string, password: string) => Promise<SignUpResult>
  signOut: () => Promise<void>
  requestPasswordReset: (email: string) => Promise<AuthResult>
  updatePassword: (password: string) => Promise<AuthResult>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
