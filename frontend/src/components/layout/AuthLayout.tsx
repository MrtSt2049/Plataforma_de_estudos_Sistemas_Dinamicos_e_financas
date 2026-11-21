import type { ReactNode } from 'react'
import { Brand } from './Brand'

/** Centered card shared by the login, sign-up and recovery pages. */
export function AuthLayout({ title, footer, children }: { title: string; footer?: ReactNode; children: ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex justify-center">
          <Brand />
        </div>
        <section className="rounded-lg border border-line bg-panel p-6">
          <h1 className="mb-4 text-base font-semibold">{title}</h1>
          {children}
        </section>
        {footer && <p className="mt-4 text-center text-fg-muted">{footer}</p>}
      </div>
    </main>
  )
}
