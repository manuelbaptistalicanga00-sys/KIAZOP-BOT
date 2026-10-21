# KIAZOP · Central de atendimento inteligente

Assistente multissetor WhatsApp Cloud API + Claude, com painel responsivo em português,
histórico de conversas, transferência para a equipa e solicitações de agendamento,
reserva, encomenda e orçamento. Não é exclusivo para clínicas.

## Estado deste lote: Fase 0 + B1–B3 (3.2.0)

**Não aprovado para go-live.** Implementação local de inbox/worker, notificações
persistentes e bloqueio por perfil. B4/B5 e fases 2–3 continuam pendentes;
PostgreSQL/Neon e contratos Meta não foram testados com credenciais reais.
Uma instalação dedicada por cliente; o enterprise-kit continua apenas referência.
Consulte [estado e evidências](docs/pilot/ESTADO.md),
[operação/rollback](docs/pilot/OPERACAO.md) e
[checklist de go-live](docs/pilot/GO_LIVE.md).

## Executar sem credenciais (demonstração)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Em `.env`, configure `DEMO_MODE=true`, `DB_PATH=demo.db` e uma `ADMIN_KEY`
forte escolhida por si. Depois:

```bash
uvicorn bot:app --host 0.0.0.0 --port 8000
```

Abra `/painel` e introduza a chave. No **Laboratório**, teste serviços, horários,
localização e transferência para humano. A demonstração usa regras locais, não
Claude, não envia WhatsApp e começa sem clientes fictícios. Não use a mesma base
de dados de produção. Configure as informações reais em **O meu negócio**. O perfil inicial é neutro e não contém preços, horários ou moradas fictícios.

## Configurar atendimento real

1. Defina `DEMO_MODE=false` e use uma base de dados exclusiva de produção.
2. Preencha `ANTHROPIC_API_KEY`, `WA_TOKEN`, `WA_PHONE_ID`, `VERIFY_TOKEN`,
   `APP_SECRET`, `ADMIN_KEY` e, opcionalmente, `OWNER_PHONE`.
3. Em **O meu negócio**, guarde um nome real e pelo menos horário, catálogo ou contacto. Sem perfil guardado e validado, não há IA: há um único encaminhamento neutro e pausa por conversa.
4. Publique em HTTPS e configure `https://SEU-DOMINIO/webhook` na Meta,
   usando o mesmo `VERIFY_TOKEN`. Subscreva o campo `messages`.
5. Execute **um serviço worker sempre ligado**, separado da API: `python worker.py --concurrency 4`. A API Vercel sozinha não processa mensagens. Ambos usam a mesma `DATABASE_URL` pooled; para SQLite, o mesmo ficheiro persistente no mesmo host.
6. Configure `OWNER_PHONE` e `OWNER_TEMPLATE_NAME` (alerta sem parâmetros aprovado na Meta); fora da janela de 24 h do dono não enviamos texto livre. Falhas exigem acompanhamento no painel.
7. Confirme o acesso ao modelo escolhido em `MODEL` e a versão Graph em
   `WA_API_VERSION` antes de ativar o serviço.

O webhook recusa mensagens sem assinatura HMAC válida e fica indisponível sem
`APP_SECRET`. Credenciais são carregadas de `.env` e nunca devem ir para o Git.
O painel não indica ligação verificada aos fornecedores: “produção” é o modo
configurado, não uma garantia de disponibilidade externa.

## Painel e API

- `/` e `/painel`: painel com métricas reais, pesquisa de conversas, histórico,
  pausa/reativação do assistente e lista de solicitações de marcação.
- `/health`: saúde local da aplicação/base de dados (não testa fornecedores).
- `GET /api/dashboard`: dados operacionais.
- `POST /api/conversations/{telefone}/pause`: `{"paused": true}` ou `false`.
- `POST /api/inbox/retry`: agendar só falhas com rejeição conhecida; nunca reenviar envios incertos.
- `POST /api/demo/message`: simulador, apenas no modo demo.

As rotas `/api/*` exigem `Authorization: Bearer SUA_ADMIN_KEY`.
A chave do painel permanece apenas em `sessionStorage` até sair/fechar a sessão;
não é colocada no URL. Os antigos links administrativos com `?key=` foram
removidos por segurança. As ações que alteram dados agora usam POST.

## Robustez e limites operacionais

- Webhook valida HMAC e responde 200 **só após commit da inbox**. Sem IA/Meta
  síncrona nem tarefas serverless em background; falha de persistência devolve 503.
- Worker com concorrência entre conversas e lease renovável por conversa. Chamadas
  externas fora de transacções; PostgreSQL usa `FOR UPDATE SKIP LOCKED`;
  SQLite usa transacções curtas e mantém compatibilidade local.
- IDs de mensagem deduplicados. Resposta preparada antes de enviar; rejeições
  conhecidas têm até 3 tentativas, com espera; timeout/5xx/crash após início do
  envio ficam **incertos, sem repetição automática**. Não prometemos exactly-once.
- Receipts assinados com correlação podem finalizar registos sem reenviar. Sem
  receipt, operador usa [reconciliação auditada](docs/pilot/OPERACAO.md).
- Notificações à equipa em pending/sending/sent/failed; lista, contadores e aviso
  vermelho no painel. `sent` significa aceite pela API, não lido pela equipa.
- Sem perfil pronto em produção: não chama IA, encaminha uma vez e pausa. Guardar
  perfil pronto liberta apenas pausas automáticas de perfil, não pausas manuais.
- Limite por cliente/hora e histórico de 20 mensagens. Pedidos dependem de
  confirmação pela equipa; imagens/áudios não são transcritos.

**Limites restantes:** autenticação/rate limiting/CSP B4, retenção/encriptação B5,
budget/diagnóstico/robustez de IA F2 e revisão enterprise F3. Templates só de
alerta ao dono, não uma solução geral para mensagens de cliente fora da janela.
Custos Meta/Anthropic são do operador. Não há alegação de conformidade ou SLA.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q
ruff check . --select E9,F63,F7,F82
```

O simulador terminal `python simular.py` também está disponível. Para respostas
locais use `DEMO_MODE=true`; para Claude configure a chave e um perfil guardado no painel.
Os testes forçam base temporária/chaves vazias e bloqueiam sockets externos.

## Docker

```bash
docker build -t kiazop .
docker run --rm -p 8000:8000 --env-file .env -v kiazop-data:/data kiazop
# Noutro serviço/processo, com a mesma configuração/volume:
docker run --rm --env-file .env -v kiazop-data:/data kiazop python worker.py --concurrency 4
```

Use um volume persistente em `/data`, proteja o painel com HTTPS e backups
regulares. O `.dockerignore` exclui segredos e bases locais da imagem.

## PostgreSQL e Vercel

O projeto suporta agora duas opções: SQLite para desenvolvimento local e
PostgreSQL gerido quando `DATABASE_URL` está definida. Na Vercel, PostgreSQL é
obrigatório: o arranque recusa SQLite para evitar perda de dados no filesystem
serverless. As tabelas e índices são criados automaticamente no primeiro arranque.
Uma base SQLite existente **não é migrada automaticamente** para PostgreSQL.

### Configuração no fornecedor de base de dados

1. Crie uma base PostgreSQL (por exemplo, Neon ou Supabase).
2. Copie a ligação **direta** ou de um pool em **modo sessão** para a variável
   segura `DATABASE_URL` na Vercel. Preserve as opções TLS do fornecedor
   (por exemplo, `sslmode=require`). Não use pool em modo transação: a exclusão
   entre instâncias utiliza um advisory lock de sessão PostgreSQL.
3. Use uma base separada para Preview e Production. Não publique credenciais
   no código, no Git nem no chat. Nunca use prefixos públicos para segredos.

### Deploy na Vercel

1. Conecte a sua conta Vercel ao Arena ou importe este repositório no painel
   da Vercel. Selecione a branch desta sessão para testar as alterações.
2. O ficheiro `vercel.json` encaminha as rotas para `api/index.py` (FastAPI).
3. Defina nas **Environment Variables** do projeto: `DATABASE_URL`, `ADMIN_KEY`
   e `DEMO_MODE=true` para começar pelo teste local de respostas.
4. Faça o deploy e verifique `/health`, depois abra `/painel` e autentique-se.
5. Para produção, configure as credenciais WhatsApp/Anthropic descritas acima,
   altere `DEMO_MODE=false`, faça novo deploy e configure o webhook da Meta
   com o domínio HTTPS da Vercel.

Não é necessário executar uvicorn na Vercel. O painel e `negocio.json` são
incluídos no bundle da função. A disponibilidade e os limites de duração da
função dependem do plano Vercel.

### Limitações serverless importantes

Na Vercel, o webhook processa as mensagens **antes de terminar a resposta**,
para não depender de tarefas em background que possam ser suspensas. Isto pode
provocar reenvios da Meta quando a IA demora; os IDs recebidos são deduplicados
na base partilhada. Um advisory lock serializa o processamento entre instâncias,
mas não transforma o serviço numa fila distribuída. Para alto volume, use um
worker externo durável e devolva a confirmação do webhook após persistir a inbox.
Interrupções entre envio e registo continuam a poder gerar respostas duplicadas.

O pool tem até três ligações por instância; dimensione o limite do fornecedor
para a concorrência prevista. Os testes locais validam SQLite e a tradução SQL;
a ligação PostgreSQL real e o deploy devem ser validados com o ambiente conectado.

Quando `DIRECT_URL` está definida, tem prioridade sobre `DATABASE_URL`. Isto permite
manter a URL do pool fornecida pela integração e usar uma ligação direta para os locks
de sessão. Configure estas variáveis no ambiente Production antes do deploy.


## Versão 3.1 — Um assistente para diferentes tipos de negócio

No painel, abra **O meu negócio**. Há modelos para comércio, restauração, beleza,
oficinas, serviços, ensino, alojamento e saúde, além de um perfil geral. O setor
é um campo livre: também pode configurar negócios que não estejam nesta lista.
Os modelos sugerem operações, mas não inventam catálogo nem condições comerciais.
Aplicar um modelo só altera o formulário; é preciso **Guardar negócio** para ativar.

Configure:
- Nome, setor, tom, contacto, localização e horários.
- Produtos/menu e serviços no formato `Nome | preço ou descrição`, um por linha.
- Formas de pagamento, entrega, levantamento e políticas reais.
- Perguntas frequentes no formato `Pergunta | resposta`, uma por linha.
- Operações permitidas: agendamentos, reservas, encomendas e orçamentos.

O perfil é validado e persistido em `business_config` no PostgreSQL/SQLite, sem
precisar de editar código nem republicar. Se ainda não guardou um perfil, o bot
usa `negocio.json` como configuração inicial. Perfis antigos de clínicas continuam
compatíveis; os históricos e marcações existentes não são apagados.
Cada gravação reinicia a memória usada pela IA, evitando levar os dados do negócio
anterior para o novo atendimento. O histórico continua visível no painel.

A aba **Solicitações** reúne as novas operações e as marcações antigas. No modo
com Claude, o bot recolhe dados e regista solicitações estruturadas após confirmação
do cliente. Todas continuam **a confirmar pela equipa**: não há integração automática
com stock, pagamentos, transportadoras ou calendários. Operações desativadas não
são registadas, mesmo se o modelo emitir uma ação inválida.

O laboratório adapta as respostas locais ao perfil escolhido (catálogo, horários,
pagamento, entrega e pedidos de dados), mas **não simula o diálogo completo de
recolha nem cria pedidos automaticamente**. A captura estruturada é validada nos
testes com respostas de IA simuladas, sem custos externos.

Esta versão suporta **um negócio ativo por instalação**, e não um serviço SaaS
com várias empresas isoladas no mesmo painel. Mudar de perfil não separa históricos,
contactos nem pedidos. Para operar várias empresas em simultâneo, use instalações
e bases separadas até existir gestão multitenant com autenticação por empresa.

## Plano premium e evolução enterprise

O plano de produto/comercial em dez etapas está em
[`docs/enterprise/PLANO_PREMIUM.md`](docs/enterprise/PLANO_PREMIUM.md).
Inclui pricing, ROI hipotético, textos prontos, arquitectura Neon e onboarding WhatsApp.
A proposta em PDF encontra-se em `docs/enterprise/PROPOSTA_COMERCIAL.pdf`.

O [`enterprise-kit/`](enterprise-kit/README.md) é um kit **separado de referência**:
componente React, adapters Meta/QR, SQL com RLS e contexto Drizzle, runner de migrações
e testes. Não altera a instalação existente, não é uma migração automática nem um
SaaS enterprise de produção completo. Ver bloqueadores de go-live no seu README.
