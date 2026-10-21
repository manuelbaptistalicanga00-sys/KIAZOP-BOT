# BOT OPTIMIZATION — Enterprise reference kit

## Estado e finalidade

**Não é uma aplicação Next.js completa, nem um upgrade instalado em produção.**
É uma base de engenharia para a arquitectura proposta em
`../docs/enterprise/PLANO_PREMIUM.md`. Não altera `bot.py`, a base existente ou o site.
Não executa registo de empresas/números sem um host e credenciais adequados.

## Executar as verificações

Requisitos: Node.js 22+ e npm.

```bash
cd enterprise-kit
npm ci
npm run check
npm test
```

Os testes de providers usam HTTP simulado. O teste RLS executa a migração em
PostgreSQL WASM/PGlite, cria duas empresas, usa uma role sem bypass e testa
leitura/escrita/FK/auditoria. **Não é um teste de integração com Neon/Meta/Evolution.**

## Inventário

| Ficheiro | Implementado | Dependências ainda necessárias |
|---|---|---|
| OnboardingWizard.tsx | Quatro ecrãs, contador, barra, validação, retry, ajuda, estados, modelos | Host React/Next, identidade e endpoints reais |
| embedded-signup.ts | SDK/popup, origens exactas, captura code+assets, cancelamento/timeout | App/config/domínio aprovados; teste de browser real |
| meta.ts | Troca/debug token, verificação de asset, registo standard, subscription, template de teste | App/provider, opt-in e template aprovados; contrato da versão Graph |
| evolution.ts | Criação de instância, QR e connection state | Gateway privado v2 fixado, webhook autenticado, sessões/reconexão |
| onboarding-service.ts | RBAC e orquestração de ligação | Repository transaccional, nonce/claim, cifragem KMS, fluxo verificado por servidor |
| webhook.ts | HMAC, tamanho máximo e ACK após persistência | Routing privado, schemas detalhados de eventos e inbox+outbox atómicos |
| db.ts | Drizzle, pooled URL e contexto tenant local à transacção | Credenciais runtime sem ownership/BYPASSRLS; identity/membership |
| migrate.ts | Migrações transaccionais, lock transaccional e checksums | DIRECT_URL de owner em runner protegido |
| migrations/0001_enterprise.sql | 14 tabelas, RLS/FORCE, FKs compostas, auditoria append-only | Bootstrap de organização e políticas de retenção/operadores |

## Como montar o componente no futuro host

```tsx
// Exemplo de composição, NÃO autenticação implementada neste kit.
<OnboardingWizard
  account={sessaoVerificada ? { email: sessaoVerificada.email } : null}
  renderSignIn={() => <ComponenteDoFornecedorDeIdentidade />}
  meta={{ appId: PUBLIC_APP_ID, configId: PUBLIC_CONFIG_ID, version: PUBLIC_GRAPH_VERSION }}
  supportPhone={NUMERO_REAL_DA_EQUIPA}
/>
```

Configurar Clerk/Auth0/equivalente no host, incluindo Google/email e organizações.
No servidor: validar sessão, mapear membership activa à empresa e criar `Actor`.
Nunca confiar em `account` do React para autorizar uma operação: é apenas UI.
Importar `onboarding.css` no layout global se o framework restringir imports de CSS.
Não depender de `localStorage` para provar identidade, estado de ligação ou entrega.

## Contrato HTTP que o host deve implementar

Todas as rotas autenticadas usam a empresa da sessão, rate limits e no-store.
Mutations com cookies têm verificação de Origin/CSRF adequada ao fornecedor.
Schemas de entrada em `src/contracts.ts`.

- `POST /api/onboarding/meta/start`: owner/admin; criar attempt UUID, nonce aleatório
  >=32 bytes, guardar hash+actor+tenant+TTL (10 min); devolver attemptId e nonce.
- `POST /api/onboarding/meta/finish`: `MetaFinishSchema`; usar `finishMeta`. Claim
  atómico só quando a autorização/modo puder ser verificado; se ainda aguarda
  account_update, devolver pendente sem consumir a tentativa nem perder o código.
  Armazenar códigos transitórios cifrados se precisar de concluir em worker.
  Standard pode exigir registo; Coexistence não. Não aceitar o modo do browser.
- `POST /api/onboarding/qr/start`: `QRStartSchema`; owner/admin; feature flag
  experimental; consentimento auditado, nome `bo-<uuid>` criado pelo servidor;
  mapear instância→tenant. Não aceitar nomes de outras instâncias.
- `GET /api/onboarding/state`: `ConnectionState`; QR com no-store, TTL curto e
  redacção dos logs; `firstAIReplyDelivered` vem de receipt verificado, não do clique.
  `inboundTestUrl` só em wa.me, gerada com número comercial e nonce de teste/TTL.
- `POST /api/onboarding/template`: `TemplateSchema`; gravar draft/aprovação; publicar
  só factos reais confirmados. Rascunhos são exemplos e não autorização para inventar.
- `POST /api/onboarding/test`: `TestSchema`; confirmar que o telefone é diferente
  do comercial, guardar consentimento, exigir janela válida ou template aprovado.
  Enfileirar outbox, devolver 202; retornar wa.me para entrada iniciada pelo cliente
  se não puder enviar proactivamente. Não enviar texto livre fora de janela válida.
- `POST /api/onboarding/complete`: provar ligação + perfil aprovado + primeira
  resposta entregue. Idempotente. O cliente não pode forjar estes três flags.

Erros: 400 validação simples em português; 401 sessão; 403 autorização;
409 precondição/estado; 429 limite; 503 dependência temporária. Não expor
stack traces, respostas cruas de providers, tokens ou URLs com segredos.

## Ingestão e worker

1. Assinatura válida antes de parsing/routing. Validar schema detalhado por versão.
2. Lookup privado de asset autorizado→tenant. Nunca usar tenant do payload como prova.
3. Gravar inbox única por evento e outbox na mesma transacção; ACK após commit.
4. Dispatcher durável, worker idempotente por conversa, budget e regras de canal.
5. Receipt autenticado actualiza o estado; evento de teste com nonce não contamina ROI.
6. Retry transitório com backoff; revogação exige reautorização. DLQ/replay auditados.

O servidor deve impor um limite de request body no reverse proxy antes de alocar
memória. A biblioteca faz uma segunda verificação de 1 MB, que sozinha não é
protecção contra alocação abusiva. Logs devem redigir query strings OAuth.

## Aplicar o schema: apenas nova branch de teste

```bash
# Fornecer DIRECT_URL com secrets do runner. Nunca colar credenciais no chat.
npm run db:migrate
```

Criar uma role de login de runtime pelo processo seguro da Neon, sem ownership,
sem superuser/BYPASSRLS, e conceder `bot_app`. Não conceder privilégios administrativos
nem a role do owner à app. A ligação pooled dessa role fica em DATABASE_URL.
DIRECT_URL fica **apenas** no runner de migrações; `db.ts` não a lê.

Não apontar a migração para converter automaticamente a base legada. Schema
administrativo `bo_meta` é exclusivo do runner; tabelas de cliente ficam em `bo`.
O job de migração usa node-postgres para SQL versionado; as queries runtime usam Drizzle.

Bootstrap e routing são operações de controlo com identidade verificada. Desenvolver
um serviço mínimo separado, em vez de distribuir a credencial do owner entre rotas.
Transacções da aplicação nunca executam SQL sem contexto de empresa. Queries, cache,
retrieval e URLs assinadas precisam de isolamento, não apenas as tabelas.

## Bloqueadores de go-live

- [ ] Identidade, membership, bootstrap e RBAC real testados.
- [ ] Handlers HTTP, CSRF, rate limiting e auditoria com logs expurgados.
- [ ] Cofre/KMS e rotação testados; segredo nunca devolvido ao browser.
- [ ] Repositório atómico para tentativa, conexão, inbox/outbox e receipts.
- [ ] Gateway e Meta testados com números reais autorizados em staging.
- [ ] Coexistence/standard diferenciados por prova no servidor; expiração/revogação.
- [ ] Outbox dispatcher/worker/DLQ, ordenação e reconciliação de envios desconhecidos.
- [ ] RLS testada no Neon com URLs/roles reais, em todos os caminhos de dados.
- [ ] Restore, limites de custo, opt-out e rejeição de acções sensíveis.
- [ ] Contratos/DPA/base legal, fornecedores/países e equipa de suporte.

Sem estes itens não se deve vender o kit como produto de produção certificado.
