# Changelog

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
