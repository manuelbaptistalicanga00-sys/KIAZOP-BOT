# Piloto-staging — lote a partir de 5eafe03

Data: 21-10-2026. Branch real: `arena/21f7620d-kiazop-bot`; nome fixo da sessão.
“piloto-staging” é o âmbito do trabalho, não uma branch/projecto novo.
Base: `5eafe03`. Nenhum push, deploy, segredo real ou escrita em produção.
**Não aprovado para go-live. Não declara conformidade legal nem SLA.**

## Método e evidências antes/depois

Testes novos escritos e executados antes das mudanças de implementação. Logs em
[`staging-evidence/`](staging-evidence/), com espaços finais normalizados para Git.

- Execução inicial contra `5eafe03`: **19 failed, 4 passed**. Os quatro aprovados
  incluíam o teste genérico de cifragem, que já estava correcto, e três casos cujo
  harness de orçamento inicialmente aceitava Exception genérica. Esse harness foi
  apertado **antes da correcção**: `budget-red.txt` prova os quatro casos a falhar
  com as excepções esperadas, não um AttributeError aceite por engano.
- S1: 10 falhas → 10 aprovados; posteriormente nove imports reais em subprocesso
  confirmam erro em português **antes de abrir DB**, e whitespace-only ADMIN_KEY
  teve vermelho/verde próprio. Total S1 final: 20 testes.
- S2: health/idade sem capacidade → aprovado. Teste de UI com Node/DOM sintético
  teve harness corrigido para childNodes; vermelho foi reexecutado contra app.js
  de `5eafe03` via `git show`, sem mudar branch, e verde contra a implementação final.
  Não se apresenta esse teste como browser real. Total S2: 2 testes.
- S3: 2 falhas → aprovadas; duas provas adicionais de proxy confiável/não confiável.
- S4: 2 falhas → aprovadas; reforço posterior confirma reactivação reconhecendo
  falha ainda não tratada, endpoint idempotente e autenticação obrigatória.
- S5: 4 falhas corrigidas no harness → 4 aprovados, 4xx/ConnectError/ReadTimeout.
- S6: failed sem alerta → aprovado; reforço prova que failed não finaliza/reenvia.
- S7: Schedule inexistente → aprovado (1 s/12 s/180 s).
- S8: README sem roteiro exigido → aprovado.
- S9: teste genérico **já passou antes das alterações**. Preservado e reexecutado,
  sem introduzir defeito artificial nem alegar correcção desnecessária.

São 38 testes novos + 90 anteriores = **128**. O teste antigo que exigia bloquear
chave válida após cinco falhas foi actualizado explicitamente para o novo contrato:
continua a exigir 429 para a chave inválida, mas exige 200 para a válida.

## Comportamento entregue

### 1. Arranque

`settings.validate_startup` corre antes de criar Database. Produção exige PostgreSQL
em DATABASE_URL, excepto `ALLOW_SQLITE=true`, reservado a teste local. Valida presença
de APP_SECRET, VERIFY_TOKEN, WA_TOKEN, WA_PHONE_ID, ANTHROPIC_API_KEY e MODEL;
ADMIN_KEY >=32 e não só espaços; chaves Fernet válidas e URL de esquema PostgreSQL.
MODEL sem default silencioso em produção e com validação estrutural. Mensagens
em português sem valores secretos. Não verifica remotamente permissões/existência.

DEMO mantém execução local sem essas credenciais; sem chave Fernet pode guardar
em claro, por isso só dados sintéticos. ALLOW_SQLITE não é autorização de deploy
com SQLite. A flag tem de permanecer false no alojamento de produção.

### 2. Saúde e fila

`worker_heartbeats`: UUID por processo, upsert de epoch a cada 15 s por thread
independente da espera/IA/manutenção. Ao desligar normalmente remove o seu batimento;
queda abrupta fica detectável após 60 s. Várias instâncias: worker_alive significa
**pelo menos uma** instância recente, não que todas as réplicas estão saudáveis.

`/health` e `/api/dashboard` expõem worker_alive, worker_heartbeat_age_seconds,
oldest_pending_age_seconds e operations_alert. Idade inclui jobs por resolver
(pending/processing/prepared/sending/failed/uncertain), não done/cancelled.
Aviso se não houver batimento/>60 s ou idade >300 s. `status=ok` só prova API/DB.
Painel mostra estado positivo e negativo, idades e avisos; orçamento zero já não
cria aviso vermelho por si só. Actualização do painel é ao abrir/carregar Actualizar;
README pede monitor externo a cada 30 s. Não há push/polling automático no browser.
O tempo usa relógios do host: sincronizar relógios entre instâncias.

### 3. Autenticação, proxy e webhook

Chave válida é comparada em bytes UTF-8 antes de consultar o rate limit e nunca é
bloqueada por este. Não consome nem limpa o histórico de falhas. Só inválidas contam:
cinco em dez minutos, depois 429/Retry-After. Protecção volumétrica continua no proxy/WAF.

IP vem de request.client depois de Uvicorn validar o peer em --forwarded-allow-ips;
não se confia directamente em X-Forwarded-For. Duas provas com middleware Uvicorn
confirmam que header de proxy não confiável é ignorado. Configuração real do host:
**não verificado**. Não usar forwarded-allow-ips='*' em exposição directa.

Webhook mantém Content-Length/stream limitados a 1 MB, calcula HMAC e **só se inválido**
regista/limita falha. Assinatura válida passa mesmo após esgotar falhas daquele IP.
Payload assinado malformado dá 400, não consome o limite HMAC; ausência de configuração
continua 503. Corpo tem de ser lido para calcular HMAC: WAF/limite volumétrico externo
é necessário contra abuso distribuído; o limite de falhas não dispensa leitura limitada.

### 4. Notificações tratadas

Migração aditiva/idempotente acknowledged_at preserva registos. Sem OWNER_PHONE,
`notifications.schedule` não insere tentativa (pausa/handoff no painel mantém-se).
`POST /api/notifications/{id}/ack` exige admin, é idempotente, dá 404 se inexistente.
Lista mostra Tratada, não apaga histórico. Contadores failed/pending e needs_human
consideram apenas não reconhecidas. Reactivar conversa limpa pausa/razão e reconhece
notificações anteriores. Pending reconhecida não é enviada; um envio já em curso
pode terminar, mas permanece reconhecido. Reactivar não prova entrega nem desbloqueia
um job uncertain anterior: reconciliar separadamente, sem reenvio cego.

Pausas B3 continuam específicas: guardar perfil válido remove só profile_unready,
não manual. Sem dono não há notificação, mas existe pausa quando aplicável. Não se
usou WhatsApp real para validar templates, callbacks ou confirmação de entrega.

### 5. Reservas de IA

`Budget.call` envolve **cada tentativa**, incluindo retries:
- rejeição HTTP 4xx (excepto 408/timeout) ou ConnectError comprovado, inclusive causa
  de erro do SDK: settle(0), libertação idempotente da reserva;
- timeout, 408, 5xx ou ligação interrompida sem prova de não aceitação: conserva;
- sucesso com usage: acerta custo estimado; sucesso sem usage conserva reserva.

Retries não cobram a mesma reserva duas vezes; cada tentativa tem token próprio.
Contabilidade é estimativa com preços configurados, não garantia da factura.
Um crash antes da libertação pode conservar reserva até revisão; segurança antes de
reutilizar saldo não confirmado. Não se fez chamada facturável real.

### 6. Meta status failed

Inbox de receipts aceita failed, sem copiar mensagens de erro potencialmente sensíveis.
Correlaciona por callback opaco ou outgoing_id guardado; destinatário tem de corresponder.
Cria alerta visível e pausa para revisão; não altera done para reenviar e failed nunca
serve para finalização como entregue. Falha da notificação pode ser correlacionada pelo
ID de saída; se não houver correlação, há aviso global para revisão. HMAC continua obrigatório.
Receipt sent/delivered/read pode reconciliar registo como anteriormente; entrega real,
ordem de callbacks e permissões Meta: **não verificado**.

### 7–8. Worker e operação

Espera activa mínima 1 s/ciclo, mesmo se futures terminam cedo; ocioso 12 s. Retenção
agendada e manutenção pesada a cada 180 s; expurgo efectivo continua no máximo diário,
com adiamento se houver trabalho activo. Reconcile leve/claims seguem no ciclo normal.
Notificações têm executor separado; heartbeat não depende de nenhuma dessas tarefas.
SIGTERM pára novos claims e drena futures; host tem de conceder tempo suficiente.

README reescrito: web + worker + Neon, passos de 60 minutos condicionais, IP/proxy,
variáveis, operação, rollback a 5eafe03 e checklist. Removida a arquitectura antiga
mencionada no pedido. Não executámos o roteiro no alojamento nem o cronometrámos.

### 9. Cifragem genérica

`test_s9_complete_flow_all_protected_columns` guarda perfil, cria solicitação e
agendamento por tags simuladas, processa fila/envio e reconcilia job incerto. Usa engine
bruto, percorre **todas as tabelas/colunas de privacy.PROTECTED**, exige tabela coberta
(não teste vacuoso) e cada valor não nulo com prefixo enc:v1:. NULL é permitido.
Inclui business_config, msgs, inbox, jobs, bookings, requests e reconciliation_log.
Já verde em 5eafe03; não foi necessária mudança de cifragem neste lote.
Essa prova completa é SQLite. PostgreSQL real local mantém os três testes de fila/
leases/receipts/cifragem/migração anteriores; fluxo HTTP completo em Neon não provado.
Números/IDs/timestamps, backups e WAL não estão abrangidos pela asserção de conteúdo.

## Saída real dos comandos finais

```text
.venv/bin/python -m pytest -q
128 passed, 1 warning in 17.80s

.venv/bin/ruff check . --select E9,F63,F7,F82
All checks passed!

# enterprise-kit
npm ci
added 28 packages, audited 29 packages; found 0 vulnerabilities
npm run check
> tsc --noEmit
# exit 0
npm test
# tests 8
# pass 8
# fail 0
npm audit --audit-level=high
found 0 vulnerabilities
```

Logs integrais em staging-evidence. `node --check static/app.js` passou.
Warning conhecido: Starlette TestClient/httpx. CI remota/Python 3.12 não executados
neste ambiente; PostgreSQL real local descartável, não Neon. Fixtures eliminam URLs/
chaves de produção e usam dados sintéticos. Nenhum segredo real foi pedido/impresso.

## Tabela final

| ID | Problema | Correcção | Teste | Estado |
|---|---|---|---|---|
| 1 | Arranque incompleto/SQLite implícito | Validação pré-DB em português, PostgreSQL obrigatório salvo teste local explícito | 10 casos, 9 imports reais, chave em branco | Corrigido localmente; permissões reais não verificadas |
| 2 | Worker/fila sem observabilidade | Heartbeat 15 s, saúde/idades e alertas >60/>300 s | Health, stale/fila e JS/DOM sintético vermelho→verde | Corrigido localmente; monitor do host não verificado |
| 3 | Chave válida/webhooks válidos bloqueados | Só falhas limitadas; HMAC primeiro; IP de proxy confiável | 2 regressões + 2 cenários ProxyHeaders | Corrigido localmente; proxy real não verificado |
| 4 | Falhas sem reconhecimento/dono opcional | Tratada, não agendar sem dono, reconhecimento na reactivação, contadores filtrados | Sem dono, ack/idempotência/auth, reactivar | Corrigido localmente; entrega Meta não verificada |
| 5 | Reserva retida em rejeição conhecida | Budget.call liberta em não aceitação comprovada; mantém timeout | 4xx/ligação/timeout, 4 falhas→4 aprovados | Corrigido localmente; factura real não verificada |
| 6 | failed Meta ignorado | Receipt/alerta/pausa, sem finalização ou retry como entregue | Webhook HMAC sintético + failed não finaliza | Corrigido localmente; Meta real não verificada |
| 7 | Polling/manutenção excessivos | 1 s trabalho/12 s ocioso, manutenção 180 s | Schedule inexistente→aprovado, CLI anterior | Corrigido localmente; capacidade real não verificada |
| 8 | README desactualizado | Roteiro web/worker/Neon, proxy, rollback e checklist | Requisitos documentais falharam→passaram | Documentado; ensaio remoto não verificado |
| 9 | Falta de prova genérica da cifragem | Regressão exaustiva dos campos protegidos após fluxo sintético | Já verde em 5eafe03 e verde final | Verificado em SQLite; fluxo completo Neon não verificado |

## Riscos residuais e decisão

- **Altos:** Neon pooled, credenciais/permissões/modelo, Meta/templates/receipts reais,
  proxy e WAF do host, migração/restauro/rollback remoto **não verificados**. A presença
  de variáveis não prova que os valores funcionam. ALLOW_SQLITE=true tem de ser
  proibido operacionalmente no alojamento real.
- **Altos:** cifragem cobre conteúdo, não todos os metadados, snapshots/backups/WAL.
  Seguir política de chaves e retenção separada. Sem promessa de conformidade legal.
- **Médios:** painel actualiza manualmente; monitor externo obrigatório. Heartbeat
  de uma réplica não prova saúde de todas; relógios têm de estar sincronizados.
- **Médios:** orçamento estimado, ambiguidades mantêm reservas; pending reconhecida
  não cancela HTTP já em curso. Reactivar não reconcilia uncertain; decisão humana
  errada pode duplicar envio. Exactly-once externo não é garantido.
- Restantes itens F2/F3 fora deste lote mantêm-se. **Go-live continua bloqueado.**

Próximos passos: (1) ensaio de deploy/proxy/monitor/Neon em staging dedicado;
(2) testes autorizados Meta/Claude com número e credenciais de teste;
(3) restore/rollback/rotação ensaiados e restantes bloqueadores fechados antes da assinatura.
