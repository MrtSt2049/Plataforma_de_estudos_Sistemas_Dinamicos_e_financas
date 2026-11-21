# QuantLab — frontend

React + TypeScript (Vite). Primeira fundação do [plano de implantação](../docs/plano-de-implantacao.md): fases F0 a F4 (projeto, tokens do design, componentes, autenticação, camada de API, estrutura e rotas).

## Como rodar

```bash
cd frontend
npm ci            # instala as versões exatas do package-lock.json
npm run dev       # http://localhost:5173
npm test          # testes (Vitest)
npm run lint      # ESLint
npm run typecheck # TypeScript estrito
npm run build     # build de produção em dist/
```

A configuração vem do **único `.env` na raiz do repositório**. Só variáveis `VITE_*` chegam ao navegador:

| Variável | Para quê |
|---|---|
| `VITE_SUPABASE_URL` | URL base do projeto (`https://<ref>.supabase.co`, **sem caminho**) |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Chave publishable (pública). Chave secreta ou `service_role` é recusada |
| `VITE_API_BASE_URL` | API Django. Opcional enquanto o backend não existe |

Se o `.env` estiver errado, a tela mostra o motivo em vez de ficar em branco.

## Estrutura

```
src/
├── components/   ui/ (botão, campo, selo, painel, estados), layout/, AsyncBoundary, guardas de rota
├── contexts/     autenticação (Supabase)
├── hooks/        useAuth, useHealth
├── lib/          utilidades puras
├── pages/        telas (carregadas sob demanda)
├── services/     config, cliente do Supabase, cliente da API
├── theme/        tokens.ts (fonte dos valores visuais)
└── test/         preparação dos testes
```

## Regras que o código aplica

- **TypeScript estrito**, sem `any` (RULE 031), versões exatas e `package-lock.json` versionado.
- **Quatro estados** em toda tela assíncrona: carregando, erro, vazio e sucesso (`AsyncBoundary`, RULE 034).
- **O navegador não grava no banco.** O Supabase serve só para autenticação; os dados passam pela API Django (RULE 001). O token só é enviado à origem da API configurada.
- **Cor nunca sozinha** e dado sintético leva selo `DEMO` (princípios do design). Os tokens são validados contra o tema de gráficos do motor e contra o contraste mínimo de 4,5:1 para texto.
- **Só aparece o que o motor 0.1 entrega.** O resto do menu fica como "em breve".

## O que ainda não existe

Gráficos (F5) e as telas de mercado, sistemas dinâmicos e laboratório (F6) dependem das rotas do backend. O ADR 0009 e a migração do banco estão em `../supabase/` e ainda não foram aplicados.
