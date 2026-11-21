# Roteiro: aplicar o banco no projeto Supabase de desenvolvimento

Aplica a migração `supabase/migrations/20261121120116_create_core_schema.sql` (ADR 0009). Vale para o projeto de **desenvolvimento**. Produção segue a fase S7 do [plano de implantação](plano-de-implantacao.md), com projeto separado.

## O que você precisa ter

| Item | Onde pegar | Onde guardar |
|---|---|---|
| Referência do projeto | Painel, Project Settings. É o trecho antes de `.supabase.co` | Já está na `SUPABASE_URL` |
| **Senha do banco** | Painel, Project Settings, Database. Se não lembrar, "Reset database password" | Variável `SUPABASE_DB_PASSWORD` na sessão do terminal, e na `DATABASE_URL` do `.env` |

Nada disso vai para o Git nem para o chat. O `.env` já é ignorado pelo Git.

## 1. Vincular o projeto

```powershell
cd Plataforma_de_estudos_Sistemas_Dinamicos_e_financas
$env:SUPABASE_DB_PASSWORD = "<a senha do banco>"
npx supabase login          # abre o navegador; ou use um token de acesso com escopo
npx supabase link --project-ref <referencia>
```

Se `supabase link` mostrar alguma versão do Postgres diferente da do `config.toml` (`major_version`), ajuste o `config.toml` para a do projeto.

## 2. Ver o que vai ser aplicado (sem aplicar)

```powershell
npx supabase db push --dry-run
```

Deve listar só `20261121120116_create_core_schema.sql`.

## 3. Aplicar

```powershell
npx supabase db push
npx supabase migration list      # a migração deve aparecer como aplicada, local e remota
```

## 4. Ativar o login do papel do backend

A migração cria o papel `quantlab_backend` **sem login**, para a senha não ficar no Git. No SQL Editor do painel, com uma senha forte e nova (diferente da senha do banco):

```sql
alter role quantlab_backend with login password '<senha forte>';
```

Monte a `DATABASE_URL` do `.env` com a string do botão "Connect" do painel, na opção **Session pooler**. O usuário do pooler tem a forma `quantlab_backend.<referencia>` (confira no painel). Use `sslmode=require`.

## 5. Conferir

- [ ] `npx supabase db advisors` sem alerta de tabela sem RLS (precisa da CLI 2.81.3 ou mais nova).
- [ ] No painel, Table Editor: as 4 tabelas aparecem com o selo de RLS ativa.
- [ ] No painel, Database, Roles: `quantlab_backend` existe.
- [ ] Project Settings, Data API: confira "Automatically expose new tables". A migração revoga e concede de forma explícita, então funciona nos dois casos.
- [ ] Teste de isolamento real, quando existirem dois usuários de teste: cada um vê só as próprias linhas pela API de dados.

## Se algo der errado

A migração não tem "voltar". Num projeto de desenvolvimento vazio, o caminho mais simples é apagar as tabelas e reaplicar, ou corrigir com uma **migração nova**. Nunca edite uma migração já aplicada.

## O que ainda não foi testado

- A migração foi verificada num Postgres embutido (versão 16) com atalhos para as peças do Supabase, não na pilha real.
- O teste `supabase/tests/database/core_schema.test.sql` (pgTAP) está escrito mas **não foi executado**. Para rodar: abrir o Docker Desktop, `npx supabase start` e `npx supabase test db`.
