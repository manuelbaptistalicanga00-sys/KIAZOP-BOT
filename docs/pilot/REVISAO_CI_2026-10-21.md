# Revisão de arranque e testes — 2026-10-21

## Correcção local: execução dos testes num checkout limpo

- Causa: o projecto tem módulos na raiz, sem pacote instalado. O executável
  `pytest` não incluía essa raiz no caminho de importação neste ambiente.
- Vermelho: `pytest -q` terminou com código 2 e sete erros de recolha
  (`ModuleNotFoundError` para `bot` e `database`). Os dois novos contratos de
  `tests/test_ci_config.py` também falharam antes da correcção (código 1).
- Alteração: `pytest.ini` configura `pythonpath = .`; o workflow Python usa
  `python -m pytest -q`, associado ao intérprete seleccionado pela matriz.
- Verde: execução directa de `pytest -q`: 133 aprovados, 1 aviso, 21,25 s.
  Ruff E9/F63/F7/F82, `node --check static/app.js` e `git diff --check`: aprovados.
- Ambiente: Python 3.11, dependências de requirements-dev.txt, DBs sintéticas.
  Python 3.12 e GitHub Actions com estas alterações ainda não verificados.
- Risco residual: aviso de depreciação Starlette/httpx; não impede os testes.
  Não se adicionou uma biblioteca alternativa nem se alteraram versões sem
  verificar a compatibilidade.

## Observações remotas (sem alteração de configuração nem envio de mensagens)

- Nova publicação de produção: `dpl_5tCVLYghmvr8p4Jbh7DRt4taJzBg`, READY/PROMOTED,
  commit `a683c9afe86ae75a4a93cd2d5e8fbf86809baa25`; origem redeploy.
- `/health?review=20261021b` respondeu com status ok, mode demo, version 3.2.0.
  O erro de arranque anterior já não se reproduziu nesta consulta.
- O painel e o CSS publicados foram recuperados com sucesso. Não foi testado
  login remoto; a chave administrativa não foi solicitada nem lida.
- Health: profile_ready=false, worker_alive=false, operations_alert=true.
  Estes estados não foram escondidos nem reinterpretados como serviço pronto.
- Próximos passos operacionais: responsável configura perfil real no painel;
  worker exige serviço separado sempre ligado (decisão de alojamento/custos).
  Não desactivar DEMO_MODE antes de preparar integrações e segredos necessários.
- Nenhuma credencial foi desencriptada; nenhuma operação administrativa na DB,
  envio Meta/IA, push, merge ou nova publicação foi executada nesta correcção.
