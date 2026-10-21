# BOT OPTIMIZATION — Plano premium de produto, venda e execução

**21 de Outubro de 2026 · Versão 1.0 · Mercado inicial: Angola; expansão selectiva para Portugal/Brasil.**

## Premissas claras

Não vou atrasar o trabalho com perguntas que o repositório já responde. Avanço com estas premissas:

- **Existe hoje:** FastAPI/Python, Claude, WhatsApp Cloud API, painel HTML/JS, Vercel, PostgreSQL/SQLite, configuração multissetor, conversas, encaminhamento humano e solicitações.
- **Estado actual:** versão 3.1 funcional em demonstração; um negócio activo por instalação. Não há evidência fornecida de clientes pagantes, receita incremental ou SLA medido.
- **Ainda não existe:** importação de todo o histórico antigo, aprendizagem supervisionada, multitenancy, RBAC, autenticação por empresa, Embedded Signup, gateway QR, facturação, fila distribuída e atribuição de receita.
- **Preço actual e concorrentes:** não informados; não serão inventados. Os preços e resultados abaixo são propostas e cenários, não factos de mercado ou casos reais.
- **Comprador inicial:** empresa com 5–30 comerciais/atendentes, 1.500–5.000 contactos de entrada por mês e margem suficiente para justificar o investimento. Vertical de entrada: serviços técnicos/comércio de valor elevado; produto horizontal, venda inicialmente focada.
- **Capacidade de execução:** fundador com IA e revisão profissional pontual. Comprar identidade e conectividade oficial em vez de reinventá-las.
- **Fronteira desta entrega:** o kit `enterprise-kit/` contém componentes, adapters, migração e testes de referência. Não é um SaaS enterprise completo, não foi integrado no site publicado e não alterou a base de produção. Os repositórios, handlers HTTP, identidade e workers descritos continuam a exigir implementação.

**Decisão central:** vender uma operação de recuperação e acompanhamento de oportunidades comerciais, com medição e responsáveis — não um “chatbot expert em tudo”.

---

# 1. Diagnóstico brutal

## O que faz parecer barato

1. **“Sabe tudo” não é auditável.** Um comprador sério quer conhecer processos, taxas de erro e responsabilidade por decisões.
2. **Contar mensagens não demonstra dinheiro.** Conversas são actividade; vendas confirmadas e margem são resultado.
3. **Uma chave partilhada não gere uma equipa.** Não identifica quem exportou dados ou alterou preços.
4. **Mudar o perfil do negócio não é multitenancy.** Os históricos actuais não estão separados por empresa. Não revender a mesma instalação a várias empresas sem isolamento.
5. **As solicitações não são confirmações.** Não há integração de stock, calendários ou pagamentos que permita prometer reservas ou vendas concluídas.
6. **A activação continua técnica.** Não há criação de conta self-service, permissões de equipa ou ligação oficial por popup.
7. **A memória actual não importa o WhatsApp antigo.** Guarda mensagens recebidas pelo sistema; não significa aprendizagem automática do passado.
8. **O simulador usa regras locais.** Não o apresentar como prova da qualidade da IA em produção.
9. **Falta uma operação comercial:** responsável por oportunidade, prazo, próxima acção, escalamento e revisão do resultado.
10. **Marca inconsistente:** BOT OPTIMIZATION na venda, KIAZOP no produto. Proponho “BOT OPTIMIZATION — Sales Operations”, com KIAZOP como nome interno do motor durante a transição.

## O que falta para uma empresa grande confiar

**Antes de dados reais:** isolamento por cliente, contas individuais, MFA para administradores, gestão segura de tokens, DPA e mapa de fornecedores, backup restaurado em teste, eventos duráveis, deduplicação, limites de custo e handoff humano com dono.

**Antes de contrato enterprise:** SSO quando exigido, auditoria resistente a alterações, exportação/eliminação, gestão de incidentes, revisão de segurança independente, fornecedor legalmente identificado, suporte com suplente e SLA compatível com evidência operacional.

**Já pode vender honestamente:** implementação dedicada de um processo delimitado, conhecimento aprovado, atendimento/qualificação supervisionados e medição. Não precisa de fingir que todas as funcionalidades futuras estão concluídas.

## Os cinco maiores riscos de não renovação

| Risco | Sinal precoce | Correcção |
|---|---|---|
| ROI invisível | Director pergunta por vendas e recebe apenas volume de mensagens | CRM + confirmação financeira + relatório com atribuição; sponsor comercial como dono |
| Respostas erradas | Mais de 2 erros factuais numa amostra de 100 conversas | Fontes versionadas, revisão diária, bloqueio de acções sensíveis e rollback |
| Equipa não adopta | Menos de 60% dos agentes activos semanalmente; leads sem dono | Inbox única, atribuição e formação; gestor responsável |
| Falhas/custos inesperados | Fila atrasada, número restrito, consumo acima de 80% antes do dia 20 | API oficial, alertas, budget caps e limites autorizados |
| Trabalho manual sem valor | Catálogo sempre desactualizado, fundador a corrigir tudo | Integração com fonte oficial, dono dos dados e escopo contratual limitado |

**Critério de renovação:** margem incremental confirmada + capacidade realmente reaproveitada − custo total. Se não for positivo após o período de avaliação, corrigir ou encerrar o escopo.

---

# 2. Proposta de valor em dinheiro

## ROI: exemplo hipotético, não case study

Empresa de serviços técnicos com 3.000 oportunidades únicas/mês:

| Variável | Baseline | Hipótese de trabalho |
|---|---:|---:|
| Conversão em venda confirmada | 10% | 12% |
| Vendas/mês | 300 | 360 |
| Vendas adicionais | — | 60 |
| Margem de contribuição por venda | US$180 | US$180 |
| Margem incremental | — | **US$10.800** |
| Trabalho repetitivo evitado | — | 180 h |
| Custo/hora carregado | — | US$6 |
| Parcela efectivamente reaproveitada | — | 50% |
| Valor da capacidade libertada | — | **US$540** |

**Benefício económico:** 60 × 180 + 180 × 6 × 50% = **US$11.340/mês**.

Horas libertadas não são automaticamente dinheiro em caixa. Só contar quando reduzirem horas extra/contratação adicional ou permitirem trabalho útil medido. Não contar novamente as mesmas vendas como ganho das horas e ganho de conversão.

**Custo económico mensal:** mensalidade US$1.500 + consumo externo hipotético US$250 + tempo interno US$100 + setup US$3.000 amortizado em seis meses, US$500 = **US$2.350**.

**Líquido:** US$8.990. **ROI:** 8.990 / 2.350 = **382,6%**; benefício/custo **4,83×**. Não é uma previsão garantida.

**Break-even:** (2.350 − 540) / 180 = 10,06 → **11 vendas adicionais**; sem atribuir valor às horas, **14 vendas**. Onze vendas em 3.000 oportunidades equivalem a aproximadamente **0,37 ponto percentual** de conversão incremental.

**Sensibilidade:**
- Ganho de apenas 0,5 ponto percentual: 15 vendas × 180 + 540 = US$3.240; líquido US$890; ROI 37,9%.
- Sem melhoria em vendas: benefício US$540; líquido **−US$1.810**. Não esconder um resultado negativo.
- Primeiro mês de caixa: setup 3.000 + mensalidade 1.500 + consumo 250 + trabalho interno 100 = **US$4.850**, diferente do custo amortizado.

## Como medir sem inventar causalidade

1. Baseline de 14–30 dias: contactos únicos, origem, primeira resposta útil, qualificação, propostas, vendas recebidas e margem.
2. Lead qualificado definido com o cliente; deduplicar contacto/oportunidade.
3. Comparação de cohort ou holdout de 20% quando volume e risco permitirem; controlar mix de tráfego e política comercial. Amostra pequena = tendência, não prova causal.
4. Janela de atribuição inicial de 30 dias; receita confirmada no CRM e financeiramente. Proposta não é receita.
5. Separar **confirmado / estimado / não atribuível**; excluir importações e testes do funil de novos leads.

## Reformulação como resultado

**Oferta:** “Implementamos e acompanhamos um processo para responder, qualificar e fazer follow-up às oportunidades que hoje ficam sem dono — e demonstramos o resultado com dados do seu negócio.”

**Metas negociáveis de piloto:** p90 de primeira resposta útil inferior a 2 minutos em horário operacional; ≥95% dos leads qualificados com responsável; ≥90% dos follow-ups elegíveis executados no prazo. São hipóteses a acordar após baseline, não resultados já alcançados.

### Três posicionamentos de uma linha

1. **Executivo:** “BOT OPTIMIZATION transforma conversas sem seguimento em oportunidades acompanhadas, com receita confirmada e responsabilidade por cada etapa.”
2. **Comercial:** “A sua equipa vende; o BOT OPTIMIZATION organiza resposta, qualificação e acompanhamento para os contactos elegíveis não ficarem esquecidos.”
3. **Operações:** “Uma operação comercial no WhatsApp com IA supervisionada, integração ao CRM e controlo por empresa.”

---

# 3. Funcionalidades premium

P0 = piloto seguro/receita; P1 = escalar o processo comprovado; P2 = expansão. Esforço é relativo, não compromisso de entrega.

| Funcionalidade | O que é / porque paga | Esforço | Prioridade |
|---|---|---|---|
| Inbox e follow-ups | Dono, estágio e prazo por oportunidade; reduz contactos esquecidos | Médio | P0 |
| Painel executivo quase em tempo real | Leads únicos, qualificação, propostas, conversão, receita confirmada, margem estimada, p50/p90 e backlog; freshness-alvo ≤60 s | Médio | P0 |
| IA orientada ao resultado | Qualificação e próxima acção verificável; humano aprova descontos, compromissos e transacções | Médio | P0 |
| Conhecimento aprovado | Catálogo/FAQ com versão, autor, validade e revisão; reduz erros de marca | Médio | P0 |
| Multitenancy, RBAC e auditoria | Owner/admin/manager/agent/analyst; segregação e histórico de acesso/exportação/configuração | Alto | P0 antes de base partilhada |
| WhatsApp oficial + um CRM | Upsert idempotente de lead, owner, estágio e retorno de venda ganha; elimina duplicação manual | Médio | P0, um conector |
| Relatório PDF executivo | Resumo semanal/mensal, custos, resultado e próximos passos; administração recebe evidência | Baixo/médio | P0 assistido |
| Onboarding e modelos por sector | Canal, perfil confirmado e primeira mensagem; baixa tempo até valor | Médio/alto | P0 assistido; self-service P1 |
| API e webhooks | Credenciais/scopes por tenant, HMAC, retries, idempotência e versionamento | Médio | P1 |
| E-mail e Google Calendar | Seguimento e agenda com disponibilidade real; não promessas inferidas pela IA | Médio | P1 |
| Pagamentos e ERP | Link de checkout alojado; recibo via webhook; ERP como fonte de stock/preço | Alto | P1, escopo por integração |
| Automação de decisões | Regras versionadas para atribuir lead, tarefa e slot; reversível e limitada | Médio | P1 |
| Previsão | Cenários/intervalos calibrados com dados suficientes; não um score fictício inicial | Alto | P2 |
| White-label | Domínio/logo/email por tenant, sem mistura de dados; monetiza parceiros | Médio | P2, add-on |
| MFA/SSO | MFA obrigatório para admins; SAML/OIDC comprado quando contratado | Médio | MFA P0; SSO P1 |

**Não construir agora:** CRM/ERP completos, pagamentos próprios, modelo de IA treinado de raiz, app móvel, dezenas de conectores e previsões sem dados. Segurança básica nunca deve ser uma penalização do plano barato.

---

# 4. Confiança enterprise

## Segurança e evidência

| Área | Controlo proposto | Evidência |
|---|---|---|
| Cifragem | HTTPS/TLS; armazenamento cifrado; tokens e conteúdo sensível com envelope encryption/KMS | Diagrama e teste de rotação |
| Isolamento | tenant_id + FORCE RLS; app sem ownership/BYPASSRLS; contexto local à transacção | Testes negativos A→B em leitura, escrita, exportação e ficheiros |
| Identidade | Contas individuais, MFA, revogação, SSO comprado | Teste de remoção de utilizador e matriz de permissões |
| Segredos | Vault/KMS, sem token no browser/logs/analytics | Inventário, permissões e secret scanning |
| Backups | PITR conforme plano + exportação cifrada independente | Restore ensaiado com RPO/RTO medidos |
| Auditoria | Append-only para agentes, request_id e metadados saneados | Exemplo de rastreabilidade e alerta de exportação |
| Contenção | Rate limits, orçamento por tenant, circuit breaker e kill switch | Teste de flood/custo/falha |
| IA | Fontes aprovadas, allowlist, validação de acções e revisão humana | Avaliações de alucinação/prompt injection |
| Deploy | Staging, lockfiles, CI, review e rollback | Histórico e resultados de testes |

**Retenção proposta para negociar:** mensagens 90 dias; auditoria 12 meses; exportações temporárias 24 h; segredos enquanto a ligação está activa; eliminação operacional até 30 dias após termo, com backups a expirar na janela contratada. Definir excepções legais e retenção financeira com advogado. Não prometer apagar backups imutáveis instantaneamente.

**Aprendizagem segura:** histórico autorizado → minimização/redacção → rascunhos de FAQ → aprovação do dono → versão publicada. Não treinar pesos nem reutilizar dados entre empresas por defeito.

## Conformidade

- **Angola:** a APD identifica a Lei n.º 22/11, de 17 de Junho, como quadro de protecção de dados. Transferências internacionais têm requisitos específicos; validar procedimentos, bases e legislação vigente com assessoria/APD. Existem propostas de revisão: não as confundir com lei já em vigor. [2](https://apd.ao/ao/artigos/) [7](https://www.dlapiperafrica.com/en/angola/insights/2021/personal-data-in-angola.html)
- **Portugal/UE:** avaliar âmbito territorial, base legal, direitos, segurança e transferências. RGPD: art. 28, contrato com subcontratante; art. 32, segurança; art. 33, violações. [1](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679)
- **Brasil:** avaliar LGPD, controlador/operador, direitos, bases e transferências usando texto compilado vigente e assessoria local. [2](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm)

**Pacote mínimo:** termos B2B, privacidade, DPA, subprocessadores/países/finalidades, confidencialidade, retenção/direitos, anexo técnico de segurança e SLA quando aplicável. O cliente normalmente decide finalidades das conversas; fornecedor processa sob instruções. Facturação/segurança das contas próprias podem exigir papel autónomo separado.

Não anunciar “100% conforme”, SOC 2, ISO 27001, “parceiro oficial Meta” ou residência exclusiva em Angola sem prova. Região do banco não equivale à localização de todos os subprocessadores.

## Fiabilidade e suporte

**Piloto:** SLO interno de 99,5% para app/inbox, sem SLA indemnizatório até haver operação medida e equipa. **Enterprise futuro:** SLA proposto de 99,9% após ensaios e evidência; em 30 dias equivale a 43 min e 12 s de indisponibilidade. Medir separadamente app, ingestão durável e entrega dependente de terceiros.

| Severidade | Exemplo | Primeira resposta proposta |
|---|---|---|
| P1 | Ingestão parada/incidente de dados | Até 1 h no horário contratado; 24/7 só com escala real |
| P2 | Integração parcial/fila atrasada | 4 h úteis |
| P3 | Dúvida/configuração | 1 dia útil |

Créditos Enterprise indicativos: 5% da mensalidade entre 99 e 99,9%; 10% entre 98 e 99%; 20% abaixo de 98%; cap 25%. Definir medição, reclamação, manutenção e exclusões proporcionais. Não excluir todo o serviço se uma integração essencial falhar; reportar impacto end-to-end.

**RPO ≤15 min/RTO ≤4 h:** objectivos a contratar apenas depois de testar recuperação no plano escolhido, não capacidades já provadas.

## Prova social

Case autorizado = cliente/sector + baseline + datas + amostra + intervenção + comparação + vendas confirmadas + limitações. Testemunho e logo com autorização escrita. Até lá: demo sintética identificada, testes e dossier técnico. Trust centre com documentos, status e contactos; nenhum selo inventado.

---

# 5. Experiência e design

## Sistema de design

Direcção: **centro operacional, não robô mágico**. Premium significa clareza, consistência e prevenção de erros.

- Inter/system-ui; corpo 14/22 px, tabelas 13/20 px, títulos 28–32 px, labels 12–13 px; números tabulares.
- Fundo `#F7F9FC`, superfície `#FFFFFF`, texto `#18282C`, secundário `#556779`, borda `#E3E8ED`, acção `#2563EB`; sucesso `#15803D`, atenção `#B45309`, erro `#B91C1C`.
- Escala 4 px: 8/12/16/24/32/48; cards 24 px; raios 8–12 px; sombras discretas.
- Componentes: sidebar, filtros guardados, tabelas, drawer, skeleton, vazio com próxima acção, toast com pedido ID, confirmação para destrutivas, data de última sincronização.
- Acessibilidade: teclado, foco, labels/erros associados, contraste AA a testar, alvos táctil ≥44 px, timezone explícito. Nunca depender apenas de cor.
- Navegação-alvo: **Executivo · Oportunidades · Inbox · Follow-ups · Conhecimento · Integrações · Relatórios · Equipa · Facturação**.
- Antes de dados suficientes: “Ainda sem dados suficientes”, nunca uma previsão fabricada.

## Onboarding até ao aha moment

| Tempo-alvo | Acção / resultado |
|---|---|
| 0:00–0:30 | Google/email → workspace |
| 0:30–2:30 | Canal elegível → ligação confirmada |
| 2:30–3:30 | Modelo + dados reais → conhecimento aprovado |
| 3:30–5:00 | Teste → primeira resposta entregue e lead de teste identificado |
| 5:00–7:00 | Atribuir dono e tarefa → processo completo |
| 7:00–9:00 | Resumo executivo → sabe como medir o resultado |

Se uma aprovação externa bloquear, oferecer sandbox identificada e activação assistida. Não fingir que a conta está ligada.

**Landing:** promessa específica → perda → processo → demonstração → ROI com premissas → segurança evidenciada → planos → diagnóstico. Textos completos na secção 10. Publicar apenas capacidades disponíveis ou identificadas como em implementação.

---

# 5B. Onboarding WhatsApp em 2 minutos

## Compromisso e pré-requisitos

**Meta de experiência:** ligação em ≤2 minutos para contas elegíveis e primeira resposta em ≤5 minutos. Não é garantia de aprovação da Meta; medir p50/p90 e motivos de abandono.

A documentação actual orienta para Embedded Signup **v4** e informa a descontinuação de v2/v3 em 15 de Outubro de 2026. Evitar snippets antigos. [5](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/implementation/)

**Do lado do operador:**
1. Entidade e app Meta Business, verificação/revisão e permissões requeridas no programa adoptado. O onboarding de Tech Provider documenta verificação empresarial; Tech Provider e Solution Partner não são sinónimos. [6](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/get-started-for-tech-providers)
2. Facebook Login for Business com config ID, domínio HTTPS e redirects exactos; app secret só no servidor; webhook global e subscriptions. [5](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/implementation/)
3. Capturar código e assets, trocar/verificar no servidor, registar número quando o fluxo padrão o exige e subscrever a conta. Coexistence tem passos diferentes; não repetir o registo padrão. [2](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview/)
4. Rotação/expiração/revogação de credenciais; não assumir token permanente.
5. Template de teste aprovado e opt-in, ou mensagem iniciada pelo cliente. Se o cliente ainda não abriu uma janela válida, não enviar texto livre como atalho.
6. Alternativa rápida para a primeira venda: contratar um BSP/Tech Provider já habilitado, em vez de depender de aprovação própria dentro de 30 dias.

**Histórico antigo:** Coexistence documenta partilha autorizada e sincronização para contas elegíveis; não dá acesso universal a backups pessoais. Validar elegibilidade, limites e prazos antes de prometer importação. [1](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users/)

Fluxo de conhecimento proposto: autorização → importação idempotente → redacção → rascunhos de FAQs → aprovação → publicação. Histórico não dispara follow-ups nem conta como lead novo.

## Quatro ecrãs, um por passo

| Passo | Ecrã/CTA | Validação e erro |
|---|---|---|
| 1. Conta | “Comece pela sua conta.” Google/email, sem formulário longo | Sessão e membership verificadas; “A sessão expirou. Entre novamente.” |
| 2. Canal | Oficial em destaque; QR experimental com aviso | Tentativa/nonce/TTL vinculados ao actor; token e assets verificados; “Ligação cancelada. Pode tentar novamente.” |
| 3. Sector | Clínica, salão, imobiliária, restaurante, loja, outro; rascunho de respostas/horários/serviços | Campos editáveis, confirmação de factos reais; não publicar exemplos silenciosamente |
| 4. Teste | Número diferente do comercial + consentimento; “Enviar teste”; “Está a funcionar” | ID do envio e receipt de resposta da IA; sem template, wa.me para iniciar; pendente não vira sucesso por clique |

Sempre: barra 1/4–4/4, cronómetro decorrido, voltar, retry, ajuda pelo WhatsApp do suporte e estado recuperável no servidor.

### Caminho A: oficial

O cliente clica “Ligar WhatsApp”, autoriza no popup da Meta e escolhe os assets. O servidor trata código, credencial, verificação e subscriptions. O callback global é configurado pelo operador uma vez; a conta de cada cliente é subscrita automaticamente. O cliente não vê tokens nem URLs de webhook.

### Caminho B: QR experimental

Instância isolada Evolution/Baileys, fora da Vercel, somente testes/demo. Mostrar: **“Ligação experimental. Pode infringir os termos do WhatsApp e causar bloqueio do número. Não use o número principal nem dados de clientes.”** Guardar aceitação com utilizador, data e versão do aviso. QR num fluxo oficial Meta não é o mesmo que sessão não oficial Baileys.

Gateway preserva sessão cifrada e tenta reconexão com backoff. Logout/revogação exigem nova autorização/QR: reconexão automática não contorna consentimento.

## Eventos

```text
account.created → tenant.created → membership.verified
→ onboarding.attempt.created → whatsapp.authorization.started
  Meta: code + assets → grant.verified → register (standard apenas)
        → subscription → connection.connected
  QR: risk.accepted → instance.created → qr.generated → connected/reconnect_required
→ knowledge.draft → knowledge.approved
→ test.requested → outbox.persisted → message.accepted
→ inbound.test.received → ai.reply.created → outbound.delivered
→ onboarding.completed
```

Envelope: event_id, tenant_id, actor_id, occurred_at, correlation_id, origem e versão. Sem tokens/QR/corpo de conversa em analytics. Estado: disconnected/connecting/qr_pending/connected/reconnect_required/failed. Receipt repetido é idempotente; primeira resposta exige prova do fornecedor.

## Endpoints necessários

| Endpoint | Regra |
|---|---|
| Auth/callback do fornecedor | Sessão assinada e membership; nunca “login” só em localStorage |
| POST `/api/onboarding/meta/start` | Owner/admin; nonce hash, TTL 10 min, origem/CSRF e limite |
| POST `/api/onboarding/meta/finish` | Claim atómico, verificação código/asset, cofre e subscription; nunca devolver token |
| POST `/api/onboarding/qr/start` | Owner/admin, flag de demo, aceitação; instância gerada pelo servidor |
| GET `/api/onboarding/state` | Tenant da sessão; dados saneados, no-store; polling 2 s com backoff |
| POST `/api/onboarding/template` | Validar factos e guardar revisão aprovada |
| POST `/api/onboarding/test` | Consentimento, telefone, canal, janela/template, budget; outbox e 202 |
| POST `/api/onboarding/complete` | Exige canal + conhecimento + primeira resposta entregue |
| GET/POST `/webhooks/meta` | Verificação inicial/HMAC raw body; persistir antes do ACK |
| POST `/webhooks/qr` | Autenticação de gateway, anti-replay, instância→tenant no servidor |
| POST `/api/connections/:id/reconnect` | Owner/admin, cooldown, nova autorização quando necessária |

**Segurança:** tenant vem da identidade verificada; asset→tenant fica num registo privado. IDs do popup não são prova de acesso. Nunca aceitar tenant_id ou nome de instância escolhidos pelo browser como autorização.

## Código entregue

`enterprise-kit/src/`: `OnboardingWizard.tsx`/CSS, `embedded-signup.ts`, `meta.ts`, `evolution.ts`, `onboarding-service.ts`, `webhook.ts`, `contracts.ts`, `db.ts`, `migrate.ts`.

Inclui quatro passos, progresso/tempo, templates, validações, polling, retry, captura SDK, adapters reais quando configurados pelo host, schemas, RBAC, validação de assinatura e contrato de persistência durável.

**Não incluído como implementação concluída:** host Next.js/identidade, handlers HTTP, repositórios/attempt claims, cofre/KMS, dispatcher, workers, reconexão, anti-CSRF/rate limits e processamento de receipts. Estão explicitados como contratos, não fingidos com sucesso automático. Não há conta real ligada nem aprovação Meta obtida por este kit.

Testar antes de produção: tentativas expiradas/repetidas, origem maliciosa, token de outra app, asset errado, QR expirado, concorrência entre tenants, falha da DB, callback duplicado, revogação, template rejeitado, opt-out e limites de custo.

---
# 6. Pricing e pacotes

Preços propostos em USD antes de impostos, sujeitos a validação comercial. Em Angola, definir facturação/câmbio legalmente aplicáveis com contabilista. A proposta assinada separa “disponível / marco de implementação / fora do escopo”.

| | Essencial | **Profissional — recomendado** | Enterprise |
|---|---:|---:|---:|
| Mensalidade | US$750 | **US$1.500** | Desde US$3.500 |
| Setup | US$1.500 | **US$3.000** | Desde US$7.500 |
| Negócios | 1 | 1 | Grupo/entidades conforme contrato |
| Números | 1 | 2 | 5 |
| Utilizadores | 3 | 10 | 30 |
| Respostas IA/mês | 1.500 | 5.000 | 20.000 |
| Integrações standard | 1 | 2 | 4 |
| Valor principal | Inbox, qualificação, conhecimento e resumo semanal | Funil/ROI, follow-up, relatório executivo e revisão mensal de 45 min | SSO, segurança e retenção/serviço negociados, CSM |
| Primeira resposta de suporte | 1 dia útil | P1 até 4 h úteis | P1 até 1 h no horário contratado |

**Isto é oferta-alvo, não afirmação de que tudo já está implementado.** MFA/isolamento e outros controlos básicos não são retirados do Essencial. SSO/SLA/white-label só são vendidos com entrega e capacidade reais.

## Unidade de consumo e custos

Uma resposta de IA = turno do assistente entregue ao contacto; não fragmento de streaming. Retry técnico não duplica franquia. Definir limites de contexto/tokens para evitar “ilimitado” economicamente inviável. Meta/BSP e consumos de terceiros discriminados ou pagos directamente pelo cliente; nunca escondidos na expressão “tudo incluído”.

Alertas a 70/90/100%; excedentes apenas autorizados. Ao limite, encaminhar para humano em vez de interromper silenciosamente atendimento.

**Setup Profissional:** discovery, baseline, um processo, até 30 FAQs aprovadas, canais e integrações standard contratados, formação 90 min, critérios de aceite e go-live assistido. ERP à medida, campanhas e migrações massivas são extra.

**Add-ons propostos:** número adicional US$100/mês + consumo; cinco utilizadores US$150/mês; mil respostas US$150 mediante aprovação; conector standard extra US$250/mês + setup US$500; ERP à medida desde US$2.000 após diagnóstico; white-label US$500/mês + setup US$1.500 quando implementado; histórico autorizado/revisão desde US$750 por lote delimitado; 24/7 desde US$1.000/mês apenas com escala operacional real.

## Ancoragem e margem

Apresentar Enterprise para enquadrar requisitos; Profissional é o percurso completo de processo + medição + revisão, e deve ser visualmente recomendado. Essencial é útil, mas não promete a mesma cadência de gestão.

Hipótese de custo Profissional: IA US$150 + infra US$80 + suporte US$120 + operação/segurança alocada US$100 = US$450; margem bruta 70% antes de CAC/impostos/despesas gerais. Medir por tenant, rever acima de US$600 durante dois meses. Meta/BSP separado neste exemplo. Não assumir que o preço de tokens actual permanecerá igual.

Desconto anual opcional de 10%, só após piloto. Não oferecer setup ilimitado gratuito para fechar.

## Garantia e teste

Diagnóstico gratuito de 30 min sem dados pessoais. **Piloto de 14 dias por US$1.500**: um número, um processo, dois utilizadores, 500 respostas e uma integração standard disponível. Consumos externos separados. Valor creditado no setup Profissional se avançar em até 30 dias.

**Garantia de entrega:** se não entregarmos a conversa de teste e fluxo acordados até ao fim, por falha nossa e com pré-requisitos do cliente cumpridos, devolvemos a taxa em dez dias úteis. Aprovação externa em atraso permite remarcar ou cancelar trabalho não executado nas condições contratuais. Não garantir facturação nem conversão independentemente de procura, preços e equipa.

---

# 7. Máquina de vendas

## ICP e decisores

**Prioritário:** serviços técnicos/equipamentos/comércio B2B de valor elevado; 10–100 colaboradores, 5–30 comerciais/atendentes, ≥1.500 contactos/mês, margem de contribuição ≥US$150 por venda, processo mínimo de CRM e sponsor acessível. Boa referência de capacidade: receita >US$100 mil/mês ou pipeline que suporte o custo.

**Dor:** propostas sem follow-up, vários números, resposta variável, director sem visibilidade de conversão. **Desqualificar:** pouco volume/margem, spam, recusa do canal oficial, sem dono dos dados, stock/produto inexistentes ou exigência de “bloqueio zero por QR”.

**Três cargos a contactar:** CEO/director-geral (orçamento); director comercial/head de vendas (conversão); COO/gestor de atendimento (processo). TI, jurídico e segurança validam riscos.

Score 0–10: volume, margem, perda verificável, acesso ao decisor e prontidão de dados/canal, cada um 0–2. Proposta só a partir de 7, com perda plausível superior ao custo.

## Três versões de abordagem

**WhatsApp — só contacto autorizado/apresentação:**
> Olá, [Nome]. Sou [Seu nome], do BOT OPTIMIZATION. Ajudamos equipas comerciais a acompanhar os contactos que chegam pelo WhatsApp e ficam sem seguimento. Antes de falar de automação, medimos pedidos, propostas e vendas. Faz sentido uma conversa de 15 minutos para perceber se existe dinheiro a perder neste processo? Se não quiser receber mensagens, diga-me e não volto a contactar.

**LinkedIn — convite:**
> Olá, [Nome]. Trabalho na ligação entre atendimento por WhatsApp e gestão comercial. Estou a conversar com responsáveis de [sector] sobre propostas sem follow-up. Gostava de trocar duas perguntas sobre como medem isso na [Empresa]. Podemos ligar-nos?

**LinkedIn — após aceitação:**
> Obrigado, [Nome]. Hoje conseguem identificar quais os contactos que receberam proposta mas ficaram sem próxima acção? Estamos a implementar qualificação e acompanhamento integrados ao CRM. Se o volume justificar, mostro em 15 minutos como avaliamos o retorno antes de propor mensalidade.

**E-mail:**
> Assunto: Propostas sem seguimento na [Empresa]
>
> Olá, [Nome],
> Quando vários comerciais respondem pelo WhatsApp, a questão não é só responder: é saber quem acompanha cada oportunidade até à decisão.
> O BOT OPTIMIZATION combina qualificação assistida por IA, responsáveis, follow-ups elegíveis e medição no CRM. Não prometemos vendas automáticas; propomos medir primeiro onde existe perda.
> Se recebem pelo menos 1.500 contactos/mês, podemos avaliar quantas vendas adicionais pagariam o programa usando a vossa margem real.
> Tem 15 minutos na terça às 10h ou quarta às 15h, hora de Luanda?
> [Nome, entidade, contacto profissional]. Para não receber novo contacto, responda “retirar”.

Não fazer scraping/campanha massiva sem avaliar lei, base de contacto e políticas do canal. Não alegar acesso às mensagens privadas do prospect.

## Cadência

Meta de esforço: 60 contas investigadas → 30 contactos qualificados → 15 reuniões curtas → cinco demos → três propostas → uma venda. São objectivos, não taxas históricas. Dia 0 abordagem, dia 3 observação útil, dia 7 último convite; depois parar sem interesse e respeitar opt-out.

Discovery: volume? proposta→venda? margem? dono do follow-up? CRM? quem aprova? acesso legal aos dados? Quanto valeria recuperar dez oportunidades? Não dar preço antes de conhecer a hipótese económica.

## Demo de 20 minutos

- **0–3:** confirmar uma dor e métrica do comprador.
- **3–6:** contacto de teste → qualificação → dono → tarefa; identificar ambiente sintético.
- **6–10:** cenário do sector e pergunta desconhecida → humano; não só happy path.
- **10–13:** registo CRM e prova de conversão; estimativa separada de receita.
- **13–16:** resumo executivo/PDF e break-even com margem do cliente.
- **16–18:** permissões/revogação/auditoria reais; se ainda não existem, apresentar como requisito de implementação, sem encenar.
- **18–20:** piloto, escopo, pré-requisitos, data, aceite e pagamento.

Fecho: “Se entregarmos este processo e a medição combinada, existe algum impedimento para iniciar o piloto de US$1.500 em [data]?”

## Estrutura completa do PDF

Capa/validade → diagnóstico/baseline → resultado e break-even → escopo/exclusões → integrações/responsabilidades → cronograma/aceite → dados/segurança/suporte → investimento/consumos → garantia/saída → aprovação com entidades, NIF, cargo, assinatura. Modelo completo na secção 10 e no PDF entregue.

## Dez objecções

| Objecção | Resposta e próximo passo |
|---|---|
| É caro | “Se não recuperar margem, concordo. Com US$180 por venda, cerca de 14 vendas adicionais cobrem US$2.350 sem contar horas. Vamos usar a sua margem real; se não for plausível, não recomendo.” |
| Já uso outra coisa | “Óptimo. Onde registam responsável, próxima acção e venda paga? Avaliamos só a lacuna; não precisa de trocar o que funciona.” |
| Preciso falar com o sócio | “Leve uma página com baseline, custo e critério de parar. Podemos marcar 20 minutos com ambos?” |
| A IA inventa | “É risco real. Só fontes aprovadas, acções limitadas e auditoria. Vamos testar perguntas fora do catálogo antes do go-live.” |
| Vão bloquear o número | “Produção é API oficial e políticas cumpridas. QR experimental não é o caminho do contrato. Ninguém pode garantir imunidade a restrições.” |
| Não quero perder histórico | “Validamos elegibilidade e autorização. Não prometemos importação universal nem apagamos a origem para migrar à força.” |
| Equipa não vai usar | “O piloto exige owner e formação. Sem adopção e responsáveis, não chamamos sucesso à IA.” |
| Quero garantia de vendas | “Garantimos entregáveis/testes, não procura ou decisão do comprador. A continuidade depende da medição acordada.” |
| Tenho receio dos dados | “Mapeamos fornecedores, países, retenção e DPA. Uma exigência não cumprida é bloqueador antes de receber dados.” |
| Talvez no próximo trimestre | “O que tem de mudar? Podemos medir propostas sem próxima acção durante duas semanas. Sem perda suficiente, paramos.” |

---

# 8. Arquitectura técnica com Neon

## Stack e razões

| Componente | Escolha / justificação |
|---|---|
| Web/BFF | Next.js + TypeScript/React na Vercel: UI, sessão e APIs curtas; não sockets Baileys/jobs longos |
| Identidade | Clerk/Auth0 ou equivalente contratado: Google/email, organizações, MFA e SSO; validar custo/região |
| Banco | Neon PostgreSQL: SQL, RLS, branches e compute elástico; plano/configuração condicionam fiabilidade |
| ORM | Drizzle, transacções e SQL parametrizado; migrações SQL versionadas com checksum |
| Worker | Python existente refactorado, execução durável fora da função Vercel |
| Fila | Outbox transaccional + transporte durável como SQS; retries/DLQ/idempotência |
| Workflows | n8n para conectores específicos, não única fonte de verdade nem fronteira de segurança |
| IA | Adaptador de provider, budget, avaliações e conhecimento aprovado; substituível |
| Ficheiros/PDF | Worker/serviço PDF + storage privado e URLs assinadas |
| Monitorização | OpenTelemetry, Sentry e métricas/alertas; sem conteúdos/segredos nos logs |
| Pagamentos | Fornecedor autorizado para a entidade/país; checkout alojado e webhooks assinados; não presumir elegibilidade Stripe universal |
| QR | Gateway privado experimental separado da Vercel, sessões cifradas e acesso restrito |

Neon documenta branching, pooling, autoscaling e scale-to-zero; validar os recursos do plano, sem presumir recuperação gratuita ilimitada. [6](https://neon.com/docs/postgres/overview/) [2](https://neon.com/docs/get-started/production-checklist)

## Diagrama

```text
Utilizador → Next.js/BFF → identidade → membership/RBAC
                              ↓ transacção/contexto tenant
                         Neon pooled / role restrita
Meta/gateway → assinatura → routing privado → inbox + outbox [commit] → ACK
                                                   ↓ dispatcher
                                               fila / DLQ
                                                   ↓
                                          worker por conversa
                              conhecimento → IA → política de acções
                                                   ↓ outbox de envio
                                     WhatsApp / CRM / Calendar / ERP
                                                   ↓ receipts
                                       métricas + auditoria + PDF
```

Routing asset→tenant é privado e mantido pelo onboarding após prova de acesso. Não aceitar tenant_id de remetente; não dar BYPASSRLS à aplicação para resolver routing.

## Guia Neon Console

1. Criar projecto aprovado, por exemplo `bot-optimization-enterprise`, na região escolhida pelo mapa de dados/latência. Não converter automaticamente a base actual.
2. Produção na branch **main**, protegida contra resets quando suportado.
3. Criar **staging** com dados sintéticos/sanitizados. Branching replica estado: não copiar PII de produção para developers por conveniência.
4. Criar **feat/<ticket>** por funcionalidade/PR, a partir de staging sanitizada; apagar após merge/janela de rollback, controlar custo. Neon suporta branches isoladas. [6](https://neon.com/docs/postgres/overview/)
5. **Connect** → branch/database/role → pooling para aplicação. Neon usa PgBouncer em transaction mode; URL pooled vai para `DATABASE_URL` no secret store. [4](https://neon.com/docs/reference/glossary)
6. Criar role de runtime sem ownership/BYPASSRLS, membro do grupo `bot_app` da migração. Nunca usar a URL do owner no runtime.
7. URL **directa** do owner só no job protegido de migrações como `DIRECT_URL`. A documentação distingue pooling normal de ligações directas para migrações e dependências de sessão. [3](https://neon.com/docs/reference/compatibility)
8. SQL Editor em staging para inspecção; migração versionada em CI com aprovação para main. Confirmar branch antes de executar.
9. Compute inicial de orçamento: staging 0,25 CU; produção min 0,25–0,5/max 2 CU **se o plano suportar e os testes confirmarem**. Não é sizing garantido; alertas a 70/90% de consumo. Autoscaling e scale-to-zero configuram-se no compute. [1](https://neon.com/docs/manage/computes)
10. Configurar janela de recuperação do plano e ensaiar restore. Monitorizar compute, storage, ligações, query latency, queue lag e custo por tenant. Não manter consultas de health a cada segundo se pretende suspender compute.

**Scale-to-zero:** desenvolvimento/staging sim; primeiros pilotos de produção apenas se a latência de cold start for aceitável e a fila absorver eventos. Para SLO exigente, pagar always-active. A Neon documenta a latência de reactivação. [10](https://neon.com/docs/connect/connection-latency)

**Limites de consumo:** certas quotas configuradas podem suspender compute até intervenção/período seguinte; alertas não são iguais a cortes sem impacto. Não cortar produção sem plano de resposta. [20](https://neon.com/docs/guides/consumption-limits)

## Pooled na app, directa só em migrações

**Atenção ao legado:** `database.py` usa lock global de sessão e dá prioridade a DIRECT_URL. Não basta trocar para pooled. A nova arquitectura elimina esse lock, usando transacções, leases e idempotência.

`enterprise-kit/src/db.ts` usa `set_config('app.tenant_id', ..., true)` dentro da mesma transacção Drizzle que executa queries. O contexto termina com a transacção e não depende da sessão PgBouncer.

Actor = sessão assinada + membership verificada no backend. Nunca confiar no tenant/role do body. RLS é defesa adicional: não protege contra uma aplicação totalmente comprometida que possa escolher livremente o contexto.

**Migrações:** `npm ci`; `npm run db:migrate` com DIRECT_URL fornecida por secrets do runner. Runner transaccional com checksum e lock transaccional. Migração do kit é para base/branch nova; não transforma automaticamente o esquema legado.

**Migração futura do legado:** inventário → backup restaurado em staging → tenant por instalação → mapear contactos/conversas/mensagens/marcações → validar contagens e amostras → cutover curto → rollback. Importação não dispara envios.

## Esquema inicial entregue

`enterprise-kit/migrations/0001_enterprise.sql`:

| Tabela | Campos/finalidade |
|---|---|
| tenants | tenant_id, auth_org_id, estado, timezone, moeda, retenção |
| users | Identidade externa, email, role e activo, sempre por tenant |
| whatsapp_connections | Provider/asset, token cifrado, estado, aceitação QR |
| contacts | Telefone por empresa, consentimento/base de contacto e opt-out |
| conversations | Contacto/canal/responsável, pausa e última entrada |
| messages | ID externo único por tenant/provider, origem live/history/test, corpo cifrado |
| leads | Estágio, estimativa, receita confirmada, moeda, atribuição |
| appointments | Contacto, intervalo, pedido/confirmado, calendário externo |
| templates | Sector, conteúdo versionado e aprovação |
| audit_logs | Actor/acção/request_id/metadados saneados; sem UPDATE/DELETE para app |
| billing | Subscrição/plano/consumo do SaaS, sem cartão completo |
| onboarding_attempts | Actor, nonce hash, tenant, TTL e consumo |
| inbox_events | Webhook persistido/deduplicado antes do ACK |
| outbox_jobs | Job, idempotência, tentativas, disponibilidade e lease |

**Todas as 14 tabelas de aplicação:** tenant_id, RLS e FORCE RLS. PK/FK compostas impedem relacionar lead A com contacto B. Metadados administrativos de migração ficam noutro schema sem acesso da role da app.

O esquema é inicial: encomendas/itens/stock/invoices e knowledge chunks precisam de migrações próprias. Billing do SaaS e pagamentos dos clientes finais são domínios separados.

**Validação entregue:** PostgreSQL WASM/PGlite testa default deny sem contexto, leitura/escrita cruzada, FK composta e auditoria append-only. Repetir no Neon com roles reais; testar também BFF, workers, ficheiros, cache, retrieval e exportação. SQL testado não certifica tudo.

## Fila, jobs e operação

- Ingestão valida assinatura, grava inbox+outbox na mesma transacção, depois ACK.
- Dispatcher pode publicar mais de uma vez se cair antes de marcar; consumidor idempotente.
- Ordem por tenant/conversa, paralelismo entre conversas; claims com lease e `FOR UPDATE SKIP LOCKED` onde aplicável, sem lock de sessão global.
- Backoff sugerido 5 s/30 s/2 min/10 min/1 h com jitter; respeitar Retry-After; permissão/revogação não entra em loop.
- DLQ após cinco tentativas, alerta e replay autorizado/auditado.
- Saída: pending → submitting → accepted → delivered/failed/**unknown**. Timeout depois de enviar pode ser desconhecido; não reenviar cegamente nem prometer exactly-once externo.
- Budget por tenant, limite de passos da IA, allowlist de acções, opt-out e pausa quando humano assume.
- Métricas: lag, falhas, duplicados, delivery, tokens/custo, p90 de resposta, revogação, exportações, utilização. Alarmes iniciais: p95 lag >60 s por 5 min, lead sem dono >5 min, gasto diário >2× média.
- Logs por correlation_id/tenant_id, sem mensagens e segredos; conteúdo cifrado no armazenamento próprio.

## Backup/PITR e teste de recuperação

A restauração depende da janela e plano Neon; não presumir histórico ilimitado. [6](https://neon.com/docs/postgres/overview/) [2](https://neon.com/docs/get-started/production-checklist)

1. Configurar janela contratada, por exemplo sete dias se suportada; exportação cifrada diária independente e retenção acordada.
2. Inserir marcador sintético em staging em t0; eliminar em t1.
3. Restaurar numa branch entre t0 e t1; nunca resetar main por impulso.
4. Verificar dados, contagens, FKs, RLS/roles, anexos e acessos.
5. Recovery sem envios; reconciliar IDs externos antes de retomar jobs, para não repetir mensagens/pagamentos.
6. Medir RPO/RTO e guardar evidência. Mensalmente testar restore; trimestralmente simular indisponibilidade usando exportação independente.

## Estrutura de pastas-alvo

```text
apps/web/                     Next.js: marketing, auth, onboarding, inbox, dashboard
apps/web/app/api/              BFF e autorização por pedido
apps/worker/                   Python: ingestão, IA, envio, integrações e PDFs
packages/auth/                 sessão → membership → Actor verificado
packages/db/                   Drizzle, contexto RLS e repositórios
packages/contracts/            schemas e eventos versionados
packages/channels/{meta,qr}/    oficial e experimental separados
packages/knowledge/            importação autorizada, revisão e retrieval isolado
packages/sales/                leads, tarefas e atribuição
packages/integrations/         CRM, Calendar, ERP e pagamentos
packages/billing/              subscrição e limites do SaaS
packages/reports/              snapshots/PDF/entrega
packages/security/             cifragem, auditoria e redacção
infra/                         filas, storage, alertas e runbooks
migrations/                    SQL e testes negativos
```

## Construir com IA vs comprar

**Construir com IA e revisão:** UX, modelos, funil/tarefas, dashboard, relatórios, adapters específicos, avaliações e documentação. **Comprar/integrar:** identidade/MFA/SSO, conectividade oficial/BSP, KMS, e-mail, checkout, storage, fila, observabilidade e pentest. **Revisão profissional obrigatória:** autorização/isolamento, segredos, importação sensível, contratos, transferências e migração. IA não assume responsabilidade legal nem substitui ensaios.

---

# 9. Roadmap de 30 dias

**Meta:** uma venda paga ≥US$1.500 até dia 30; objectivo comercial, não garantia. Não condicionar a venda a todos os itens enterprise.

## Semana 1 — Dor, oferta e pipeline

- Dias 1–2: escolher vertical, entidade/contactos, piloto, ROI e proposta; lista de 60 contas e 15 apresentações pela rede.
- Dias 3–5: cinco entrevistas com decisores; volume/margem/perdas; três discovery calls seguintes; demo dedicada sintética. Iniciar provider/BSP e análise de dados.
- Dias 6–7: duas propostas de piloto; sponsor e baseline acessíveis legalmente; seleccionar CRM/conector.
- **Pronto:** ICP com exclusões, duas propostas enviadas, sponsor identificado, demo honesta e nenhum dado misturado.

## Semana 2 — Piloto seguro

- Dias 8–10: identidade/MFA para novo caminho; se partilha não estiver pronta, instalação/base dedicada. Canal oficial elegível e conhecimento aprovado. Se aprovação bloquear, sandbox e calendário renegociado, não QR no número principal.
- Dias 11–14: um fluxo de qualificação, uma integração suportada, uma sequência elegível, dono/handoff, inbox/outbox, budget cap; replay, opt-out, falha e restore.
- **Pronto:** teste oficial entregue; 30–50 cenários sem erro crítico; dados aprovados; eventos preservados em falha; restore ensaiado; piloto facturado/pago quando contratado.

## Semana 3 — Medir e gerir

- Dias 15–17: cohort limitada, revisão diária de 20 conversas, correcção de fontes e acções auditadas.
- Dias 18–21: relatório executivo assistido, custos e conversões confirmadas; três novas demos.
- **Pronto:** sete dias de dados com amostra explicitada, nenhuma proposta chamada receita, backlog conhecido e sponsor valida relatório. Proposta Profissional pronta.

## Semana 4 — Fechar e decidir continuidade

- Dias 22–24: revisão de ROI conservador, custos/limitações e plano de 60 dias com director.
- Dias 25–27: proposta, dados/jurídico, formação, suporte e aceite. Pedir testemunho só com resultado e autorização.
- Dias 28–30: receber ≥US$1.500, formalizar continuidade ou encerramento, preparar próxima cohort e avaliação.
- **Pronto:** dinheiro recebido + contrato/escopo + cliente/piloto operacional delimitado. Promessa verbal não conta.

**Caminho crítico:** instalação dedicada segura + provider comprado + workflow + medição + implementação. Multitenancy/RLS/CI em staging em paralelo, partilha só após testes. Não prometer SSO/ERP/white-label/previsão completos em 30 dias sozinho. Sem dor/sponsor até dia 10, ajustar segmento/oferta, não compensar com funcionalidades.

---

# 10. Entregáveis completos prontos a usar

**Regra de publicação:** os textos abaixo descrevem a oferta-alvo. Remover ou marcar “em implementação” o que ainda não está disponível. Substituir apenas campos entre parênteses rectos por dados verdadeiros. Não transformar cenário hipotético em prova social.

## 10.1 Landing page

### Header
BOT OPTIMIZATION · Como funciona · Resultados · Segurança · Planos
**CTA:** Pedir diagnóstico

### Hero
**Os seus clientes escrevem. Cada oportunidade precisa de seguimento.**

Transforme o WhatsApp da empresa numa operação comercial acompanhada: qualificação assistida por IA, responsáveis, próximas acções e resultados medidos no CRM.

**CTA principal:** Avaliar oportunidades perdidas
**CTA secundário:** Ver uma demonstração de 20 minutos

Para empresas cujo volume comercial justifica automação supervisionada. Sem promessas de vendas mágicas, stock inventado ou substituição total da equipa.

### Dor
**Responder não é acompanhar até à decisão.**
Um pedido chega fora de horas. Uma proposta fica sem próxima acção. O cliente fala com duas pessoas e repete tudo. No fim do mês, a administração vê mensagens, mas não sabe o que se perdeu.
O BOT OPTIMIZATION foi desenhado para organizar esse percurso e tornar a perda visível.

### Como funciona
**1. Identificamos a perda.** Volume, resposta, propostas e conversão com os seus números.
**2. Implementamos o processo.** Canal elegível, conhecimento aprovado, responsáveis e follow-ups.
**3. Acompanhamos o resultado.** Equipa na inbox/CRM, administração com actividade, conversões confirmadas e melhorias.

### Benefícios
- Menos oportunidades sem responsável.
- Respostas baseadas em catálogo e condições aprovadas.
- Pessoas assumem assuntos que exigem julgamento.
- Próximas acções registadas, não apenas mensagens guardadas.
- Consumos e custos transparentes, com limites acordados.

### Sectores
Lojas, serviços técnicos, imobiliárias, restauração, beleza, formação e outros negócios podem configurar catálogo e processo. A implementação começa por um caso de uso delimitado, não por uma IA que “sabe tudo”.

### ROI
**Só faz sentido se o retorno puder ser demonstrado.**
Com margem de US$180 por venda, cerca de 14 vendas adicionais cobrem um custo económico mensal de US$2.350 sem contar horas. Exemplo hipotético: calculamos o seu caso com os seus dados.
**CTA:** Calcular o meu break-even

### Confiança
**Dados, permissões e responsabilidade fazem parte do produto.**
Antes de abrir atendimento real, acordamos acessos, retenção, fornecedores e encaminhamento humano. API oficial é o caminho de produção; QR experimental não substitui esse compromisso.
Peça o dossier de segurança e a lista de capacidades disponíveis. Não anunciamos certificações que não possuímos.

### Oferta
**Comece com um piloto pago, limitado e mensurável.**
14 dias · um processo · até um número · critérios de aceitação.
**US$1.500**, creditados no setup Profissional conforme proposta. Consumos externos separados. Garantia de entrega do fluxo, não de vendas.
**CTA:** Marcar diagnóstico de 30 minutos

### Perguntas frequentes
**É só para clínicas?** Não. O conhecimento e o processo adaptam-se ao negócio.
**Lê todo o WhatsApp antigo?** Não automaticamente. Depende de mecanismo autorizado, elegibilidade e revisão.
**Substitui vendedores?** Não. Organiza tarefas repetitivas e encaminha decisões.
**Envia sem autorização?** O processo deve respeitar base legal, opt-out e políticas do canal.
**Posso sair?** Sim, segundo o contrato, com exportação e eliminação acordadas.
**Quando fica activo?** Após validação do canal, dados e testes. Aprovações externas podem prolongar prazo.

### Footer
BOT OPTIMIZATION · [Entidade legal/NIF/morada] · [Contacto profissional]
Privacidade · Termos · Segurança · Estado do serviço

## 10.2 Página de preços

# O nível de acompanhamento que a sua operação precisa

Não está a comprar mensagens ilimitadas. Está a contratar um processo implementado, limites transparentes e uma forma de avaliar retorno.

### Essencial — US$750/mês
Setup US$1.500. Para organizar o atendimento de uma equipa pequena.
- Um negócio, um número e três utilizadores.
- 1.500 respostas IA/mês.
- Inbox, conhecimento aprovado, qualificação e uma integração standard suportada.
- Resumo semanal e suporte em horário útil.
**CTA: Avaliar o Essencial.**

### Profissional — US$1.500/mês · Recomendado
Setup US$3.000. Para acompanhar conversão, não apenas responder.
- Um negócio, dois números e dez utilizadores.
- 5.000 respostas IA/mês e duas integrações standard suportadas.
- Funil, follow-ups elegíveis, painel de resultados e relatório executivo.
- Revisão mensal de 45 minutos.
**CTA: Pedir diagnóstico para o Profissional.**

### Enterprise — desde US$3.500/mês
Setup desde US$7.500. Governação e integração negociadas.
- Pacote-base de cinco números, 30 utilizadores e 20.000 respostas IA/mês.
- Quatro integrações standard, SSO e revisão de segurança conforme escopo disponível.
- Retenção, capacidade e suporte por contrato.
**CTA: Falar sobre requisitos enterprise.**

Impostos e Meta/BSP/terceiros separados salvo indicação. Excedentes só autorizados. Funcionalidades futuras não incluídas antes do marco de entrega.
Piloto de 14 dias por US$1.500, um processo e critérios acordados. Crédito no setup conforme proposta. Garantia técnica de entrega, não facturação.
**Antes do contrato, calculamos consigo quantas vendas adicionais tornam o programa rentável.**

## 10.3 Proposta comercial completa

**Proposta BO-001 — Piloto de operação comercial por WhatsApp**

**Fornecedor:** [Entidade legal, NIF, morada, representante, contacto].
**Cliente:** [Entidade legal, NIF, morada, decisor, contacto].
**Data:** [data]. **Validade:** 15 dias. Valores antes de impostos; moeda/meio de facturação no aceite.

### A. Situação
O cliente pretende reduzir contactos sem seguimento e medir pedido→proposta→decisão. Baseline registado/aprovado no início. Não se considera demonstrada perda ou melhoria antes dessa recolha.

### B. Objectivo
Implementar e testar durante 14 dias operacionais, após pré-requisitos, um fluxo supervisionado de resposta/qualificação e encaminhamento, com responsável e próxima acção.

### C. Incluído
1. Reunião inicial até 90 minutos e um caso de uso.
2. Ambiente de cliente isolado, um número elegível e dois utilizadores nomeados.
3. Até 30 FAQs/condições fornecidas e aprovadas pelo cliente.
4. Até 500 respostas IA no período, limites e handoff humano.
5. Uma integração standard já suportada, identificada no aceite. Se não existir conector adequado, é dependência/novo escopo, não promessa genérica.
6. Uma regra de atribuição e uma sequência de follow-up permitida pelo canal.
7. Relatório final de volume, resposta, qualificação, falhas e conversões confirmadas disponíveis.
8. Formação remota de 60 minutos e recomendação de continuidade.

### D. Exclusões
ERP à medida, reconstrução de CRM, campanhas massivas, importação irrestrita, aconselhamento regulado, confirmação autónoma de pagamentos, migração de número sem elegibilidade, SSO/pentest/SLA não contratados e garantia de vendas.

### E. Marcos e aceite
**M1 Prontidão:** acesso oficial, dados e responsável aprovados.
**M2 Teste:** mensagem e resposta entregues; conhecimento correcto; desconhecimento encaminhado; tarefa com responsável e rastreabilidade do fluxo disponível.
**M3 Revisão:** relatório e reunião de decisão.
Cliente valida ou documenta desvios em cinco dias úteis por marco. Fornecedor corrige desvios do escopo; novo trabalho requer alteração. Aceite técnico não equivale a retorno garantido.

### F. Responsabilidades
Cliente: dados comerciais verdadeiros, permissões/base de tratamento, contas, validação jurídica interna e equipa que assume conversas. Fornecedor: configuração, protecção de acessos, limitações, incidentes e não reutilização entre empresas.

### G. Investimento
**Piloto US$1.500**, no aceite, antes do início. Terceiros discriminados ou pagos pelo cliente. Avançando ao Profissional em até 30 dias do relatório: crédito de US$1.500 no setup US$3.000; saldo de setup US$1.500 + mensalidade US$1.500. Nenhuma conversão automática sem aceite.

### H. Garantia
M2 não entregue no prazo por falha do fornecedor, com pré-requisitos cumpridos: devolver taxa em dez dias úteis. Bloqueios externos permitem remarcar/cancelar trabalho não executado conforme contrato. Sem garantia de facturação.

### I. Dados e suporte
DPA e anexo de fornecedores antes de dados reais. Canal oficial em produção. Retenção/exportação/eliminação/localizações no anexo. Piloto: segunda a sexta, 08h–18h Africa/Luanda, feriados acordados; primeira resposta até um dia útil e contacto de escalamento crítico. Sem prevenção 24/7 implícita.

### J. Saída ou continuidade
Decisão explícita de avançar/ajustar/encerrar. Exportação acordada disponível 30 dias; revogar integrações e eliminar nos prazos do DPA, ressalvadas obrigações legais/backups. Não reter número/conta do cliente para forçar renovação.

### K. Aprovação
[Nome/cargo/assinatura fornecedor] · [Nome/cargo/assinatura cliente] · [Data].
Anexo: conector, número, datas, responsáveis e pré-requisitos. Não assinar campos essenciais vazios.

## 10.4 Três scripts de abordagem prontos

**WhatsApp**
> Olá, [Nome]. Sou [Seu nome], do BOT OPTIMIZATION. Trabalhamos com equipas que recebem pedidos pelo WhatsApp mas nem sempre acompanham cada proposta até à decisão. A ideia não é vender-lhe um chatbot: é medir oportunidades sem próxima acção e implementar um processo para as acompanhar. Faz sentido avaliarmos isso em 15 minutos? Se não for relevante, diga-me e não volto a contactar.

**LinkedIn**
> Olá, [Nome]. Tenho trabalhado na organização do processo comercial que começa no WhatsApp: pedido, qualificação, proposta e follow-up. Na [Empresa], conseguem ver quais pedidos ficaram sem responsável? Posso partilhar uma forma simples de medir essa perda antes de avaliar software.

**E-mail**
> Assunto: Quem acompanha os pedidos do WhatsApp até à decisão?
>
> Olá, [Nome],
> O BOT OPTIMIZATION ajuda a organizar resposta, qualificação e acompanhamento comercial, com IA supervisionada e integração ao processo da equipa.
> Antes da proposta, avaliamos contactos, conversão e margem. Se não houver retorno plausível para US$1.500/mês, dizemo-lo.
> Podemos usar 15 minutos para perceber se existem propostas sem seguimento na [Empresa]? Sugiro [dia/hora] ou [alternativa], hora de Luanda.
> [Seu nome, entidade, contacto]. Para não receber novo contacto, responda “retirar”.

## 10.5 Contrato/termos resumidos — minuta B2B

**Minuta de trabalho; requer revisão jurídica local, identidade/lei/foro e anexos antes de assinatura. Não é parecer jurídico nem contrato global automaticamente válido.**

1. **Partes/objecto:** [Fornecedor] presta a [Cliente] configuração e acesso ao BOT OPTIMIZATION para o processo da proposta assinada, que integra o contrato.
2. **Escopo:** canais, utilizadores, consumos, integrações, marcos e capacidades disponíveis constam da proposta. Roadmap não é obrigação sem anexo. IA opera com limites e pode errar.
3. **Pré-requisitos:** cliente mantém direitos do número, contas e legitimidade dos dados; aprova condições reais. Fornecedor não activa acções sem autorização ou com risco não mitigado conhecido.
4. **Preço:** valores/moeda/impostos/setup conforme proposta. Excedentes/trabalho extra autorizados. Notificar incumprimento antes de suspensão, preservando exportação/emergência conforme acordado.
5. **Prazo:** piloto não renova automaticamente. Subscrição mensal seguinte só com aceite; denúncia com 30 dias, excepto compromisso anual expressamente negociado.
6. **Decisões:** pagamentos, descontos, stock, reserva final e temas regulados exigem validação competente. Sem garantia de facturação, conversão ou imunidade a restrições de terceiros.
7. **Dados:** DPA define papéis, instruções, categorias, finalidades, subprocessadores, países, segurança, direitos, retenção e transferências. Sem venda/reutilização de conversas para outra empresa. Treino fora de instruções/base legal acordadas proibido.
8. **Segurança/incidentes:** acessos mínimos, contas individuais e protecção de segredos. Notificar cliente sem demora injustificada após conhecimento; objectivo contratual inicial até 24 h, sujeito a validação jurídica/capacidade, sem esperar pela investigação completa. Cliente mantém obrigações legais próprias.
9. **Serviço:** horários e primeiras respostas no anexo. SLA/créditos só se expressos; nenhum SLA enterprise implícito no piloto. Registar incidentes/dependências/mitigação.
10. **Titularidade/confidencialidade:** dados e materiais próprios do cliente continuam seus; fornecedor mantém software preexistente. Nome/logo/case só autorizados. Confidencialidade após termo, segredos enquanto protegíveis.
11. **Subcontratação:** lista e mecanismo de comunicação/oposição conforme DPA/lei; mudanças materiais de país/finalidade avaliadas antes da transferência.
12. **Garantia:** critérios técnicos e condições da proposta, sem excluir direitos imperativos. Reembolso conforme falha de entrega acordada; não garantia comercial.
13. **Responsabilidade:** propor cap de 12 meses de remunerações pagas, sujeito a negociação. Fraude/dolo, direitos inderrogáveis e violações de dados/confidencialidade precisam de tratamento específico por advogado. Não excluir por completo a responsabilidade pelo serviço principal.
14. **Saída:** exportação estruturada por 30 dias, revogar tokens e eliminar operacionalmente conforme DPA, respeitando retenções legais e expiração de backups.
15. **Lei/litígio:** [lei e foro a preencher após assessoria]. Negociação de boa-fé por 15 dias antes de procedimento, excepto urgências legais/segurança. Não afastar direitos imperativos de titulares.

**Anexo DPA a preencher:** titulares/dados, finalidade/instruções/duração, base para contactos/importação, países/subprocessadores, medidas técnicas, assistência a direitos, incidentes, auditoria proporcional, retorno/eliminação, transferências e contactos. Não deixar estas matérias implícitas.

## 10.6 Checklist de onboarding

### Antes de dados
- [ ] Entidade/NIF, decisor, sponsor e owner operacional.
- [ ] Volume, conversão, margem, dor e hipótese económica.
- [ ] Proposta, pagamento, escopo e aceite.
- [ ] DPA, países, fornecedores, retenção e utilização/contacto validados.
- [ ] Instalação isolada ou tenant partilhado testado.
- [ ] Identidades/permissões, MFA administradores e número autorizado.
- [ ] Opt-out, privacidade e suporte definidos.

### Configuração
- [ ] Canal oficial verificado; sem tokens por chat/email.
- [ ] Nome/timezone/idioma, horários/catálogo reais aprovados.
- [ ] FAQs com dono/validade e acções proibidas.
- [ ] Handoff, CRM, dono e sequência elegível configurados.
- [ ] Budget caps, consentimento e templates testados.
- [ ] Histórico apenas autorizado; separado de eventos novos.

### Aceitação
- [ ] Primeira resposta entregue comprovada por fornecedor.
- [ ] Desconhecimento passa para humano; pagamentos/descontos não executados sem validação.
- [ ] A não lê/escreve/exporta B, incluindo ficheiros/retrieval.
- [ ] Replay não duplica lead/franquia; CRM em falha não perde eventos.
- [ ] Opt-out bloqueia seguimento aplicável.
- [ ] Backup restaurado em teste, sem replay externo em recovery.
- [ ] Equipa formada, owner/suplente e contactos de escalamento.
- [ ] Baseline, revisão semanal e decisão agendados.

### Primeira revisão
- [ ] Separar testes/histórico de volume real.
- [ ] Auditar respostas/corrigir fontes.
- [ ] Confirmar receita por CRM/financeiro.
- [ ] Mostrar margem/capacidade, custos e limitações.
- [ ] Decidir continuar/ajustar/terminar pelos critérios.

---

## Os três passos para executar hoje

1. **Escolher 20 contas do ICP e marcar cinco conversas:** perguntar volume, margem e propostas sem próxima acção; não começar por “IA expert em tudo”.
2. **Preparar demo de um processo e proposta de piloto de US$1.500:** dados sintéticos identificados, handoff humano e break-even com margem real do prospect.
3. **Fechar o caminho seguro do primeiro cliente:** provider/BSP oficial, instalação/base isolada, owner de implementação e testes em staging. Não migrar produção nem prometer activação instantânea antes de provar elegibilidade, isolamento e entrega.
