# Estado — Fase 0 + Fase 1 B1–B3

Data: 21-10-2026. Instalação dedicada por cliente, não multi-tenant.
Checkpoint: `8805838`. Sem push/deploy, acesso a produção ou chamadas Meta/Claude.
**Não pronto para go-live.** Os contratos dependentes de credenciais continuam não verificados.

## Causa, mudança e prova

| ID | Causa raiz | Mudança / ficheiros | Prova executada | Estado |
|---|---|---|---|---|
| F0 | Suspeita de nomes/imports/configuração inconsistentes | Nenhuma reparação necessária; `BASELINE.md` preserva evidência | 21 Python + 8 TS baseline; Ruff/tsc/audit limpos | Verificado localmente |
| B1 | Webhook processava em Vercel; lock Python/advisory global abrangia IA/Meta; sem fronteira segura de envio | `database.py`, `jobqueue.py`, `worker.py`, `reconcile.py`, `bot.py`: transacções reais curtas, claims, leases, heartbeat, deduplicação, resposta preparada, incertos e receipts | ACK sem IA; duplicate→um envio; duas conversas paralelas; lease entre conexões; fencing/heartbeat; crash/commit/receipt/reconciliação; worker subprocesso | Corrigido localmente; PostgreSQL/Meta live não verificados |
| B2 | Excepção de notificação era engolida, sem estado no painel | `notifications.py`, `bot.py`, `static/*`: estados persistentes, template aprovado configurável, janela do dono, contador/lista/aviso vermelho | Falha de envio visível; template fora de janela; ausência de template; janela válida; notificação interrompida sem reenvio | Corrigido localmente; template real não verificado |
| B3 | Fallback `negocio.json` habilitava IA sem configuração guardada | `bot.py`, `static/*`: readiness do perfil guardado+validado, encaminhamento único/pausa, libertação só de pausas de perfil | Zero chamadas IA sem perfil; vazio/genérico/inválido bloqueados; guardar perfil válido permite IA e mantém pausa manual | Corrigido nos testes sintéticos |

Os quatro testes de regressão iniciais falharam **antes** da implementação (4 failed,
1 warning em 1.33 s). Não se confundem com os 21 testes de baseline aprovados.
Depois passam sem enfraquecer as quatro asserções de segurança. Dois testes antigos
que exigiam processamento HTTP síncrono/retry por monkeypatch de `responder` foram
actualizados para o contrato correcto de inbox durável + worker + rejeição conhecida.

## Resultados reais finais deste lote

```text
.venv/bin/python -m pytest -q
48 passed, 1 warning in 4.65s

.venv/bin/ruff check . --select E9,F63,F7,F82
All checks passed!

node --check static/app.js
exit 0

git diff --check
exit 0

# em enterprise-kit/
npm ci
added 28 packages, audited 29 packages; found 0 vulnerabilities
npm run check
tsc --noEmit; exit 0
npm test
tests 8; pass 8; fail 0
npm audit --audit-level=high
found 0 vulnerabilities
```

Python warning conhecido: depreciação do transporte httpx do Starlette TestClient.
`tests/conftest.py` força DB temporária, esvazia credenciais/URLs e bloqueia sockets;
o teste CLI filho herda esse ambiente sintético e `DEMO_MODE=true`.
SQL PostgreSQL é apenas verificado por compilação/adaptação; **não** se fez ligação
PostgreSQL/Neon, e PGlite no kit não prova os claims Python em PostgreSQL real.
CI existente já executa toda a suite Python em 3.11/3.12; a execução local foi 3.11,
não uma execução remota da CI nem prova de 3.12 neste ambiente.

## Riscos e fases restantes

- **Críticos para aprovação:** B4/B5 ainda pendentes (autenticação, CSP, limites,
  retenção/encriptação/eliminação). Não expor esta revisão como serviço aprovado.
- **Altos:** PostgreSQL concorrente, contratos Meta/receipts, template e modelo não
  verificados em staging. Sem receipt, incerto exige decisão humana; exactly-once
  externo é impossível de garantir. Replay errado pelo operador pode duplicar.
- **Altos:** orçamento/diagnósticos/idade de fila/retries classificados e parsing
  estrito de acções F2 pendentes. Templates só cobrem alerta do dono.
- **Médios:** F3 enterprise ainda não revisto neste lote; kit de referência continua
  sem integração de produção. Warning TestClient e testes reais de restore pendentes.

## Próximas três acções

1. Executar B4/B5 e respectivas regressões antes de exposição com dados reais.
2. Executar F2/F3 no âmbito pedido, sem converter referência enterprise em produção.
3. Validar `OPERACAO.md` em staging dedicado, ensaiar rollback e assinar `GO_LIVE.md`
   apenas depois de fechar os bloqueadores.
