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
