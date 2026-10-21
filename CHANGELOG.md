# Changelog

## Lote B4/B5 + F2 seleccionada — 2026-10-21 — não publicado

- B4 `security.py`/`bot.py`: CSP/XFO, UTF-8, validação de ADMIN_KEY no arranque,
  rate limiting persistente, backoff Retry-After, limites de corpo em streaming.
- B5 `privacy.py`/`privacy_migrate.py`/`database.py`/`worker.py`: Fernet/MultiFernet,
  migração offline reversível/atómica, rotação, retenção diária 90 dias,
  export/delete/purge com auditoria e recusa de dados activos; access logs mascarados.
- F2 seleccionada: `.env.example` único; `ai_service.py` valida MODEL e classifica
  falhas/retries; endpoint admin de diagnóstico; `actions.py` tags Pydantic estritas;
  `budget.py` reservas/acerto diário e alertas; `bot.py`/`static/*` paginação.
- Testes escritos/executados antes das alterações: logs vermelho/verde em
  `docs/pilot/evidence/`. Final: 90 Python aprovados, 8 kit, Ruff/tsc/audit limpos.
- `test_postgres_queue.py`: PostgreSQL real local descartável, não Neon. Sem chamadas
  reais de fornecedores. Relatório: `docs/pilot/B4_B5_F2.md`; limites/migração/chaves:
  `docs/pilot/PRIVACIDADE_E_CHAVES.md`. Sem declaração de conformidade ou go-live.

## 3.2.0 — 2026-10-21 — lote local, não aprovado para go-live

- **F0:** baseline documentada em `docs/pilot/BASELINE.md`; checkpoint `8805838`.
  Nenhuma alteração de nomes/imports/vercel.json necessária.
- **B1:** `database.py` substitui mutex/advisory de sessão por transacções curtas
  por thread; `jobqueue.py` persiste jobs, resposta preparada, leases/heartbeat,
  deduplicação, estados incertos e receipts. `worker.py` sempre ligado separado
  da API; `reconcile.py` permite decisão local explícita com evidência/auditoria.
  `bot.py` webhook só confirma após commit e não chama IA/Meta/background tasks.
- **B2:** `notifications.py` persiste pending/sending/sent/failed, falha visível,
  template de alerta ao dono configurável ou texto livre só dentro da janela.
  `static/*` mostra contadores/lista e “Precisa de humano” a vermelho.
- **B3:** `bot.py` exige perfil guardado/validado para IA em produção; sem perfil,
  um encaminhamento neutro e pausa. Health/painel indicam readiness. Guardar
  perfil válido não remove pausas manuais. `simular.py` adapta assinatura de envio.
- **Provas:** `tests/test_pilot_blockers.py`, `tests/test_database.py` e testes
  actualizados de inbox; 48 Python aprovados, 8 kit aprovados, Ruff/tsc/audit limpos.
  Testes sem credenciais/rede por `tests/conftest.py`. Procedimentos e riscos em
  `docs/pilot/ESTADO.md`, `OPERACAO.md`, `GO_LIVE.md`; README e `.env.example` actualizados.
- **Pendente/não verificado:** B4/B5/F2/F3; PostgreSQL real/Neon, Meta e Claude live;
  deploy/restore/rollback real. Nenhum deploy/push neste lote.

## Piloto-staging a partir de 5eafe03 — 2026-10-21 — não publicado

- S1 `settings.py`/`security.py`/`bot.py`: arranque pré-DB com variáveis obrigatórias,
  PostgreSQL por defeito e SQLite apenas por excepção explícita de teste local.
- S2 `worker_health.py`/`worker.py`/`bot.py`/`static/*`: batimento independente,
  worker_alive, idades e avisos operacionais; estado saudável explícito no painel.
- S3 `security.py`/`bot.py`: chave válida nunca bloqueada; falhas apenas, HMAC antes
  do limite e documentação/provas de proxy de confiança.
- S4 `notifications.py`/`bot.py`/`static/*`: coluna aditiva de reconhecimento, endpoint
  Tratada, sem agendamento sem dono, reactivação reconhece notificações e contadores filtrados.
- S5 `budget.py`/`bot.py`: libertação por rejeição conhecida/abertura falhada;
  timeout/ambiguidade conservam reserva. S6 `jobqueue.py`/`bot.py`: status failed
  persistente, alerta visível, nunca tratado como entregue nem reenviado automaticamente.
- S7 `worker.py`: esperas adaptativas 1/12 s e manutenção 180 s. S8 README novo
  web+worker+Neon, roteiro 60 min condicionado, rollback e checklist.
- S9 teste genérico de todos os campos protegidos após fluxo completo: já aprovado
  em 5eafe03, preservado. Testes em `tests/test_staging.py`; 128 Python aprovados,
  8 kit aprovados, Ruff/tsc/audit limpos. Evidências em `docs/pilot/staging-evidence`.
- Relatório e limites em `docs/pilot/PILOTO_STAGING.md`. Sem deploy/credenciais
  reais, sem certificação/conformidade/SLA/go-live declarados.
