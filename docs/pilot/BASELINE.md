# Fase 0 — baseline antes de alterações

Checkpoint local: `8805838` (branch `arena/21f7620d-kiazop-bot`).
Nenhum deploy, credencial real ou base de produção usados.

## Estrutura
- Existem `business.py`, `requirements.txt`, `requirements-dev.txt`, `tests/`, `static/`, `api/index.py`.
- Não existem `negócios.py`, `requisitos.txt`, `testes/`, `estático/`, `aplicativo/api`.
- Os imports e StaticFiles resolvem no TestClient; CI aponta para ficheiros existentes.
- `python` + `json.loads(Path('vercel.json').read_text())`: JSON completo; routes aponta para `/api/index.py`.
- Não foi necessário alterar nomes, imports ou vercel.json.

## Comandos executados e resultado real
Ambiente Python: `.venv/` activada logicamente pelo caminho dos executáveis.

```
.venv/bin/pip install -r requirements-dev.txt
# exit 0; requisitos instalados/satisfeitos

env -u DATABASE_URL -u DIRECT_URL -u VERCEL .venv/bin/python -m pytest -q
# 21 passed, 1 warning in 1.35s

.venv/bin/ruff check . --select E9,F63,F7,F82
# All checks passed!

cd enterprise-kit
npm ci
# added 28 packages; audited 29; found 0 vulnerabilities
npm run check
# tsc --noEmit; exit 0
npm test
# tests 8; pass 8; fail 0
npm audit --audit-level=high
# found 0 vulnerabilities
```

Warning Python: Starlette TestClient anuncia depreciação do transporte httpx usado
na versão instalada. Não é erro de teste; requer revisão de compatibilidade futura.

## Defeitos confirmados no checkpoint
- B1: `bot.receber` espera processamento em Vercel; `processar_pendentes`/`responder`
  fazem chamadas externas sob `with lock`; Database usa advisory lock de sessão global.
- B2: erro de notificação só gera warning; não há tabela nem contador/estado no painel.
- B3: `negocio()` devolve perfil neutro de ficheiro e produção continua a chamar IA.
- B4/B5 e fases 2/3 continuam fora deste primeiro lote; não constituem go-live aprovado.
