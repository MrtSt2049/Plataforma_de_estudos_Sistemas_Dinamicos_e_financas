import type { ConfigError } from '@/services/config'

/** Shown instead of the app when the .env is wrong, so the cause is not a blank screen. */
export default function ConfigErrorPage({ error }: { error: ConfigError }) {
  return (
    <main className="grid min-h-screen place-items-center px-4">
      <div role="alert" className="w-full max-w-lg rounded-lg border border-neg/40 bg-panel p-6">
        <h1 className="mb-2 text-base font-semibold text-neg-text">Configuração inválida</h1>
        <p className="mb-3 text-fg">{error.message}</p>
        <p className="text-fg-muted">
          Corrija o <span className="font-code">.env</span> na raiz do repositório e reinicie o servidor de
          desenvolvimento.
        </p>
      </div>
    </main>
  )
}
