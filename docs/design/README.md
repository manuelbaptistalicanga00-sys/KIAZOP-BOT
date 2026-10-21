# Layout premium — KIAZOP

Redesign do workspace existente, sem alterar o backend/autenticação/CSP:
sidebar verde-escuro, superfícies claras, Manrope variável auto-alojada (licença OFL
em static/fonts), ícones SVG próprios, login editorial, diagrama conceptual sem
métricas inventadas, cartões reais, formulários/tabelas/chat e navegação mobile.
Alertas operacionais e a distinção demo/produção foram preservados.

## Evidências

- `tests/test_premium_layout.py`: **3 falhas antes**, 3 aprovados depois;
  saída vermelha em `layout-tests-red.txt`.
- Suite final: **131 passed, 1 warning in 18.07s**.
- Ruff: **All checks passed!**
- `node --check static/app.js`, `git diff --check`: exit 0.
- Chromium real local: login, cinco secções, clique em ícone aninhado de sugestão,
  resposta no laboratório, viewport 390px e formulário de configurações sem overflow;
  sem pageerror. Backend e worker DEMO dedicados em base /tmp sintética, sem
  fornecedores, credenciais ou dados reais. Nenhum deploy/push.

Capturas **reais da interface**, não mockups gerados:
- `premium-dashboard.png`: desktop 1440px;
- `premium-login.png`: página de entrada;
- `premium-mobile.png`: 390px, depois da conversa de teste.
Contadores/telefone que aparecem são do fluxo sintético, identificados como demo.

## Reproduzir navegador (opcional, não dependência de produção)

Instalar playwright-core e @sparticuz/chromium num prefixo temporário exterior ao
Git; disponibilizar bibliotecas de sistema exigidas pelo Chromium. Neste ambiente,
libnspr/nss vieram do bundle al2023 do pacote, com LD_LIBRARY_PATH=/tmp/al2023/lib.
Não é necessário desactivar os headers de segurança da aplicação.

Com API/worker DEMO numa base descartável, a porta 8002 e ADMIN_KEY sintética
`design-preview-only`, correr:

```bash
NODE_PATH=CAMINHO_TEMPORARIO/node_modules \
  node scripts/check-premium-ui.cjs
```

O script recusa URL não local e mode diferente de demo. Usa apenas chave sintética
fixa, nunca de produção. UI_SCREENSHOT_DIR permite mudar destino das capturas.
O prefixo temporário/npm/browser não é incluído no repositório.

A versão pública não foi actualizada. Publicação/ensaio no alojamento real e
integrações Meta/Claude continuam fora desta alteração visual.
