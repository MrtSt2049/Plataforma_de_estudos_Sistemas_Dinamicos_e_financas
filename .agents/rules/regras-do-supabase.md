---
trigger: manual
---

6. REGRAS DO SUPABASE

RULE 024 — Autenticação oficial

Supabase Auth será o único provedor oficial de autenticação.

Não implemente um segundo sistema independente de identidade no Django.

RULE 025 — Validação JWT

O backend deve validar os tokens emitidos pelo Supabase.

Verifique:

Assinatura criptográfica.

Expiração.

Emissor.

Audiência, quando aplicável.

Claims relevantes.

Identificador do usuário.

Utilize a estratégia de validação compatível com a configuração atual do projeto Supabase.

Não confie apenas na decodificação do token.

RULE 026 — Identidade do usuário

Utilize o identificador UUID do usuário Supabase como referência de identidade.

Mantenha associação consistente entre usuários e registros privados.

RULE 027 — Row Level Security

As tabelas com dados privados devem possuir políticas RLS apropriadas.

Considere:

SELECT.

INSERT.

UPDATE.

DELETE.

Verifique propriedade dos registros.

Não considere a interface frontend como mecanismo de segurança.

RULE 028 — Credenciais

Nunca exponha service_role.

Nunca exponha tokens administrativos.

Nunca armazene segredos no Git.

Utilize variáveis de ambiente.

Separe ambientes de desenvolvimento e produção.

Não compartilhe credenciais em logs.

RULE 029 — Banco de dados

Utilize migrações versionadas.

Defina restrições e índices adequados.

Utilize transações quando necessário.

Evite consultas N+1.

Utilize UUID quando apropriado.

Defina relacionamentos explícitos.

Considere integridade referencial.

RULE 030 — Supabase Storage

Arquivos privados devem utilizar políticas de acesso apropriadas.

Não exponha arquivos de pesquisa ou dados privados por URLs públicas sem autorização.