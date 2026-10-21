# Operação assistida — um cliente por instalação

Estado: procedimento preparado, **não executado em produção nem garantia de activação em 60 minutos**.
B4/B5/F2/F3 ainda impedem aprovação de go-live. Não executar testes com bases/chaves reais.

## Preparação prevista (janela de trabalho de 60 min, após resolver bloqueadores)

1. **0–10 min:** operador confirma instalação dedicada, domínio HTTPS, responsáveis,
   plano de custos, regras de dados e acesso restrito. Instala requisitos em venv;
   configura variáveis pelo secret manager do alojamento, não por chat/Git/logs.
   `ADMIN_KEY` aleatória de pelo menos 32 caracteres é requisito operacional;
   a validação automática e protecção de login são B4, ainda pendente.
2. **10–20 min:** base dedicada. Neon: `DATABASE_URL` **pooled** de aplicação tanto
   na API como no worker. `DIRECT_URL` fica reservada a migrações externas e não é
   lida pelo bot. Sem advisory locks de sessão. Fazer backup antes da actualização;
   DDL desta versão é aditivo. Validar separadamente limites de conexões/compute.
   SQLite só no mesmo host com volume persistente partilhado, nunca disco efémero.
3. **20–30 min:** dois serviços independentes, mesma revisão/configuração/base:
   - API: `uvicorn bot:app --host 0.0.0.0 --port 8000`;
   - worker: `python worker.py --concurrency 4`, sempre ligado, restart on failure.
   Vercel pode alojar **apenas a API**, com PostgreSQL; exige worker externo.
   Não iniciar worker em startup FastAPI, BackgroundTasks, função ou cron efémero.
   Permitir drenagem no SIGTERM (sugestão conservadora: 600 segundos, verificar no host).
4. **30–40 min:** guardar perfil no painel, confirmar `/health.profile_ready=true`;
   nome diferente do genérico e horário OU catálogo OU contacto. `negocio.json`
   não habilita IA de produção. Uma validação estrutural não comprova veracidade:
   o cliente confirma os factos. Pausas manuais permanecem após guardar perfil.
5. **40–50 min:** configurar Meta/HMAC, subscrever `messages` e respectivos statuses,
   confirmar versão API/modelo em staging. Definir `OWNER_PHONE` e template **sem
   parâmetros** de alerta previamente aprovado, em `OWNER_TEMPLATE_NAME` e
   `OWNER_TEMPLATE_LANGUAGE`. Não existe criação/aprovação automática de templates.
   Sem template, texto livre ao dono só se existir entrada do dono nas últimas 24 h;
   caso contrário persiste `failed/approved_template_required` e aparece aviso vermelho.
6. **50–60 min:** executar cenários de staging abaixo, confirmar monitorização/backup,
   preencher checklist; parar se alguma prova faltar. A equipa deve acompanhar o painel:
   o alerta pelo WhatsApp não substitui essa responsabilidade.

## Estados, falhas e migração

- Webhook confirma só depois de guardar inbox+job; 503 pede reenvio à Meta.
- `pending → processing → prepared → sending → done`. Lease por conversa com
  heartbeat; outra conversa pode correr em paralelo. Transacções só para DB.
- Resposta e acções persistidas antes de envio. ID de entrada único; mensagem de
  cliente é registada uma vez. Rejeições 4xx conhecidas: `failed`, espera mínima
  30 s, até 3 tentativas; painel só reagenda estas falhas, nunca `uncertain`.
- Timeout, 5xx, queda após marcar `sending`, ou falha no commit depois de enviar:
  **uncertain**, sem reenvio automático. A conversa fica bloqueada por job anterior
  até prova/reconciliação. Pode perder uma resposta para evitar duplicar; não é exactly-once.
- Receipt assinado `sent/delivered/read` com `biz_opaque_callback_data=job:<id>` e
  destinatário correspondente permite finalizar o registo sem reenviar. Contrato Meta
  e permissões ainda precisam de teste real em staging; receipt pode não chegar.
- Notificações são linhas persistentes pending/sending/sent/failed. `sent` é aceite
  pela API, não lido. Resultado desconhecido não é reenviado automaticamente.
- Inbox de versões anteriores não tem prova de envio. Com serviços antigos parados:
  `python worker.py --migrate-legacy` coloca entradas pending/failed sem job em
  quarentena. Nunca migrar reenviando cegamente. Rever cada entrada com a equipa.
- O processo de testes limpa URLs/chaves e bloqueia sockets. Não remover essa
  protecção para testes live; usar ambiente de staging dedicado e roteiro manual.

## Reconciliação manual (acesso local restrito ao host)

1. Não carregar “reprocessar” esperando resolver incertos. Verificar statuses,
   logs do fornecedor e confirmação da equipa. Não pedir ao cliente tokens ou PINs.
2. Identificar o job por acesso administrativo à DB de **staging/instalação autorizada**.
   Não publicar exportações, telefones, payloads ou segredos. CLI requer acesso local
   aos segredos de aplicação; não é endpoint HTTP nem substitui controlo de acesso ao host.
3. Com prova de envio aceite e identificador de saída:
   `python reconcile.py JOB_ID --outcome sent --outgoing-id ID_SAIDA --operator OPERADOR --evidence 'Confirmação validada no fornecedor' --confirm-reviewed`.
   Apenas finaliza; não envia. Acções/notificação de handoff ficam persistidas.
4. **Só com prova de não envio:**
   `python reconcile.py JOB_ID --outcome not-sent --operator OPERADOR --evidence 'Fornecedor confirmou pedido não aceite' --confirm-reviewed`.
   Agenda resposta já preparada; worker fará a tentativa. Uma declaração errada
   pode duplicar envio. Sem prova suficiente, manter incerto e atendimento humano.
5. A decisão fica em `reconciliation_log`, com operador/evidência sem PII. Esta
   tabela não é uma auditoria imutável nem resolve B5. Notificações falhadas são
   tratadas no painel/equipa; não há botão de repetição cega de notificações.

## Provas de staging ainda obrigatórias (não executadas)

- PostgreSQL/Neon **não produção**: duas instâncias worker, mensagens concorrentes
  na mesma conversa e em conversas diferentes; observar leases/ordem/claims
  SKIP LOCKED e ausência de locks durante latência artificial. Reiniciar worker
  durante IA, antes do envio e depois do envio; registar resultado sem PII.
- Meta de testes: repetir message ID, injectar falha de DB depois de resposta HTTP
  aceite e confirmar receipt correlacionado; sem receipt, testar reconciliação.
- Template aprovado: dono sem janela activa, testar sucesso e template inválido/
  token revogado; confirmar contador/lista falhada e conversa “Precisa de humano”.
- Modelo: só depois de perfil pronto, validar acesso com chave exclusivamente
  staging; sem perfil, IA deve ter zero chamadas. Testar pausa manual vs perfil.
- Deploy, reinício e rollback: comprovar que API continua a persistir enquanto worker
  parado e que retoma sem duplicar. Monitorização de idade de fila ainda é F2.

## Rollback seguro

Checkpoint anterior: **8805838**, preservado na mesma branch. Não fazer downgrade
cego para ele: contém os defeitos B1–B3 e pode reenviar inbox incerta.
Parar novos claims, drenar/parar worker, suspender webhook/atendimento se necessário,
obter backup e exportar apenas metadados operacionais para acesso restrito. Preservar
DB actual e quarentena. Preferir redeploy da última revisão segura do novo fluxo;
se necessário código antigo, só num clone isolado, sem tokens/entradas novas, após
revisão dos estados por operador. Não apagar tabelas/IDs de deduplicação para “limpar”.
Este roteiro foi documentado, não ensaiado em alojamento real.
