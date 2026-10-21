# KIAZOP — piloto assistido de atendimento WhatsApp

Um negócio por instalação: FastAPI + worker sempre ligado + PostgreSQL/Neon,
com IA Claude, perfil do negócio, solicitações a confirmar e transferência humana.
Não é exclusivo para clínicas nem um SaaS multi-tenant.

**Âmbito actual: piloto-staging, a partir de `5eafe03`. Não aprovado para go-live.**
A branch da sessão é `arena/21f7620d-kiazop-bot` (nome fixo). Não houve deploy
neste lote. Provas locais não substituem testes com fornecedores em staging.

## Piloto em 60 minutos

Janela de trabalho proposta, **não garantia de activação em 60 minutos**. Pré-requisitos:
conta/número de teste Meta prontos, permissões aprovadas, acesso ao modelo, alojamento
com dois serviços sem suspensão, base Neon dedicada, operador e aprovação de custos.
Sem esses pré-requisitos, parar no ponto pendente; não usar credenciais/dados de produção.

### 0–10 min — instalação e segredos

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configurar valores reais **apenas no secret manager do alojamento**. Não colocar
segredos no Git, chat, URLs ou logs. API e worker têm a mesma revisão/configuração/base.
Com `DEMO_MODE=false`, o arranque valida, antes de abrir a DB:

- `DATABASE_URL` PostgreSQL;
- `MESSAGE_ENCRYPTION_KEYS`: chaves Fernet válidas, nova primeiro;
- `ADMIN_KEY`: pelo menos 32 caracteres;
- `APP_SECRET`, `VERIFY_TOKEN`, `WA_TOKEN`, `WA_PHONE_ID`, `ANTHROPIC_API_KEY`, `MODEL`.

Ausência/erro aborta com mensagem em português sem revelar valores. Validação local
não comprova permissões Meta/Claude. `MODEL` é validado estruturalmente; diagnóstico
administrativo remoto continua obrigatório. Chaves de cifragem devem ser estáveis,
guardadas separadamente dos backups; não rodar sem ensaio de restauro.

### 10–20 min — Neon e dados

Criar base/projecto de **staging dedicado**. Usar a ligação **pooled** em
`DATABASE_URL` para web e worker; confirmar quotas, conexões, custos e backup.
A aplicação usa transacções curtas e PostgreSQL `FOR UPDATE SKIP LOCKED`.
Não faz chamadas IA/Meta durante transacções. Não copiar dados reais para testes.

Se já existem dados, não ligar uma nova revisão cegamente: seguir a
[migração reversível e rotação](docs/pilot/PRIVACIDADE_E_CHAVES.md), numa cópia offline.
A adição de `notifications.acknowledged_at` é idempotente e não apaga registos.

### 20–30 min — dois serviços independentes

Web, com HTTPS terminado no proxy do alojamento:

```bash
uvicorn bot:app --host 0.0.0.0 --port 8000 \
  --proxy-headers --forwarded-allow-ips="IP_OU_REDE_DO_PROXY_CONFIAVEL"
```

**Substituir** o exemplo pelos IPs/CIDRs reais do proxy. Não usar `*` num serviço
exposto directamente. Uvicorn só deve aplicar forwarded headers de peers confiáveis;
a aplicação usa `request.client`, não interpreta X-Forwarded-For por conta própria.
Não confundir o IP público do cliente com o IP do proxy. Validar o contrato do host
em staging; não há uma lista universal segura de proxies.

Worker, noutro serviço sempre ligado:

```bash
python worker.py --concurrency 4
```

Configurar restart em falha e drenagem SIGTERM (janela conservadora: 600 segundos;
validar no host). Não iniciar o worker como tarefa em background da API, cron efémero
ou serviço com auto-sleep. Ambos ligam à mesma base e usam as mesmas chaves.
O worker dorme 1 s com trabalho, 12 s sem trabalho; manutenção a cada 180 s.
Heartbeat separado a cada 15 s, inclusive enquanto processa IA/notificações.

### 30–40 min — perfil e atendimento humano

Abrir `/painel`, autenticar e guardar nome real mais horário OU catálogo OU contacto.
Sem perfil pronto, produção não chama IA: encaminha uma vez e pausa a conversa.
Guardar perfil válido liberta **só pausas automáticas de perfil**; pausas manuais
mantêm-se. Não repete mensagens antigas; a próxima entrada pode usar IA.

`OWNER_PHONE` é opcional: sem ele, não se agenda notificação. O handoff continua
visível no painel e a equipa tem de o acompanhar. Com dono configurado, usar
`OWNER_TEMPLATE_NAME`/`OWNER_TEMPLATE_LANGUAGE` para alerta aprovado sem parâmetros
fora da janela de 24 h; não cria/aprova templates automaticamente.
Botão **Tratada** reconhece a notificação sem a apagar; contador de falhadas conta
apenas não reconhecidas. Reactivar conversa reconhece notificações anteriores e
limpa `needs_human`; não resolve por si só jobs incertos nem prova entrega.

### 40–50 min — Meta, IA e orçamento

Configurar `https://DOMINIO/webhook`, token de verificação e subscrição `messages`.
Validar HMAC, mensagens e statuses com número/chaves exclusivamente de staging.
HMAC válido nunca consome o limite de falhas; limite aplica-se só a assinaturas
inválidas. Corpo continua limitado a 1 MB antes/durante leitura.

`POST /api/diagnostics/ai` exige administração, consulta metadados sem gerar texto.
Confirmar `WA_API_VERSION`, `MODEL`, preços e orçamento diário no alojamento.
`AI_DAILY_BUDGET_USD` é limite de contabilidade estimada local, não garantia da factura.
80% alerta; nova reserva que exceda saldo bloqueia geração. Rejeições 4xx e falhas
comprovadas de abertura da ligação libertam a reserva; timeout/resultado ambíguo
mantêm-na. Cada retry tem reserva própria. Confirmar limites também no fornecedor.

### 50–60 min — verificação e decisão

`/health` e painel mostram `worker_alive`, idade do heartbeat e idade do job por
resolver mais antigo. Aviso vermelho se heartbeat ausente/>60 s ou fila >300 s.
`status=ok` significa API/DB respondem, **não** que worker/fornecedores estão prontos.
Painel actualiza ao entrar/carregar em **Actualizar dados**; configurar monitor
externo de `/health` a cada 30 s, com alerta ao operador.
Testar assinatura inválida/válida, duplicados, pausa/reactivação, notificação tratada,
falha de envio, receipt failed e fila/worker parado. Preencher checklist abaixo.

## API administrativa

Rotas `/api/*` exigem `Authorization: Bearer ...`; sem chave por querystring.
Chave válida nunca é bloqueada pelo rate limit; só tentativas inválidas contam
(cinco em dez minutos, depois 429 com Retry-After). Protecção volumétrica/WAF é do host.

- `GET /api/dashboard?page=1&page_size=25&request_page=1`: dados/saúde e paginação.
- `GET /api/conversations/{numero}/messages?page=1&page_size=50`: histórico paginado.
- `POST /api/conversations/{numero}/pause`: `{"paused":true}` ou `false`.
- `POST /api/notifications/{id}/ack`: notificação tratada; idempotente.
- `POST /api/inbox/retry`: reagenda só rejeições conhecidas, nunca envios incertos.
- `GET /api/privacy/{numero}`: exportação sensível para administrador.
- `DELETE /api/privacy/{numero}?confirm=delete`: eliminação; 409 se há envio activo.
- `POST /api/privacy/purge?confirm=purge`: expurgo de 90 dias, com auditoria.

Pedido recolhido **não é reserva/venda/pagamento confirmado**. A equipa confirma.
Sem receipt, envio incerto exige [reconciliação manual](docs/pilot/OPERACAO.md).
Receipt Meta `failed` cria alerta visível; não causa reenvio automático nem é prova
de entrega. Não há promessa de exactly-once.

## Demonstração e teste local

`DEMO_MODE=true`, `DB_PATH=demo.db`, chave administrativa local e, para dados
persistentes cifrados, chave Fernet estável. Demo sem chave **não cifra** os dados:
usa só dados sintéticos. Arrancar web e worker como acima (sem proxy em local).
Laboratório usa regras, não Claude nem WhatsApp. `python simular.py` é alternativa.

Para testar o fluxo não-demo com SQLite, só localmente: `ALLOW_SQLITE=true`,
`DEMO_MODE=false`, base sintética e todas as restantes variáveis obrigatórias.
**Nunca usar ALLOW_SQLITE=true no alojamento de produção.** Fora dessa excepção,
produção exige PostgreSQL. Docker usa dois serviços com comandos separados;
SQLite local requer mesmo ficheiro/volume no mesmo host, nunca disco efémero.

## Rollback seguro

Antes de actualizar: drenar/parar worker, suspender entradas quando necessário,
backup cifrado e inventário de jobs `sending/uncertain`, receipts e IDs de deduplicação.
Checkpoint deste lote: `5eafe03` (rollback do código, não automático dos dados).

Voltar para imagem/revisão anterior só após testar compatibilidade numa cópia.
Preservar DB/chaves/novas colunas e estados; não apagar inbox para “limpar”. A coluna
de reconhecimento é aditiva e não precisa de ser removida. Código antigo pode voltar
a bloquear chave válida ou agendar notificações sem dono: avaliar esses riscos.
Código anterior à cifragem não lê os dados cifrados; ensaiar reversão na cópia,
nunca descifrar produção por conveniência. Sem prova de envio, manter quarentena e
atendimento humano. Rollback/restore remoto: **não verificado**.

## Checklist antes de go-live

- [ ] Base/serviços/segredos dedicados; staging sem dados reais.
- [ ] Arranque recusa variáveis obrigatórias ausentes; SQLite não autorizado em produção.
- [ ] Web + worker sem auto-sleep; heartbeat saudável e fila <=5 min; alerta externo.
- [ ] Proxy de confiança/IP de cliente e WAF verificados no host.
- [ ] Modelo/Meta/templates/statuses reais provados em staging.
- [ ] Falhas/replays/timeouts e reconciliação ensaiados sem duplicar respostas.
- [ ] Notificações tratadas e reactivação verificadas pela equipa.
- [ ] Preços/limites e reservas IA verificados; custos aceites pelo responsável.
- [ ] Migração/rotação/retencão/backup/restore/rollback ensaiados e autorizados.
- [ ] Acessos/finalidades/prazos de dados revistos; restante âmbito F2/F3 fechado.

Sem certificação, conformidade legal ou SLA declarados. Cifragem de conteúdo não
cifra números/IDs/timestamps nem apaga versões em WAL/snapshots/backups. Ver
[política e limitações](docs/pilot/PRIVACIDADE_E_CHAVES.md).

## Testes e documentação

```bash
pip install -r requirements-dev.txt
python -m pytest -q
ruff check . --select E9,F63,F7,F82
cd enterprise-kit
npm ci
npm run check
npm test
npm audit --audit-level=high
```

Testes limpam URLs/chaves reais; PostgreSQL real **local descartável** testa fila e
cifragem, não prova Neon ou contratos Meta. Restantes cenários completos são SQLite.
Provas deste lote: [relatório staging](docs/pilot/PILOTO_STAGING.md).
Histórico: [B1–B3](docs/pilot/ESTADO.md), [B4/B5/F2](docs/pilot/B4_B5_F2.md).

[Plano premium](docs/enterprise/PLANO_PREMIUM.md),
[proposta PDF](docs/enterprise/PROPOSTA_COMERCIAL.pdf) e
[enterprise-kit](enterprise-kit/README.md) mantidos como referência, não integração
enterprise de produção nem criação de outro projecto.
