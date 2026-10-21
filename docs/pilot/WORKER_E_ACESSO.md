# Perfil, acesso e worker separado

Esta preparação não contrata alojamento nem activa o worker. Requer um servidor
Linux sempre ligado, Docker Engine e o plugin Docker Compose. O worker não tem
porta pública e não deve executar numa função Vercel. Confirmar custos, região
(e eventual transferência de dados) e autorização antes de activar.

## 1. Perfil e login — pelo responsável

1. Abrir https://kiazop-bot.vercel.app/painel.
2. Entrar com ADMIN_KEY, sem a enviar em chat, URL ou captura de ecrã.
3. Confirmar que o painel mostra dados e permite abrir as suas secções.
4. Na configuração do negócio, preencher nome real, sector e informação factual
   (serviços/produtos, horário, contacto público, políticas e operações permitidas).
5. Guardar. Nunca usar dados fictícios apenas para apagar o aviso.
6. Consultar https://kiazop-bot.vercel.app/health: profile_ready deverá ser true
   depois de guardar um perfil válido. Isso não verifica o worker nem integrações.

Um perfil pronto exige nome diferente de «O meu negócio» e pelo menos horário,
contacto, produtos ou serviços. Não inventar informação para cumprir esse mínimo.
Se o login falhar, comunicar apenas o erro apresentado, nunca a chave.

## 2. Preparar o servidor (sem execução automática)

Obter o código desta revisão no servidor e criar o ficheiro privado:

```sh
cp .env.example .env.worker
chmod 600 .env.worker
```

Editar com um editor local/gestor de segredos. Não guardar valores reais em Git.
Usar DATABASE_URL PostgreSQL da mesma instalação da API; não usar SQLite nem
uma cópia da base. Uma URL PostgreSQL sintacticamente válida não prova que é a
base correcta. Confirmar o destino com o responsável antes de iniciar.

Manter DEMO_MODE=true enquanto a API estiver em demo. Usar a mesma ADMIN_KEY e,
se configuradas na API, exactamente as mesmas MESSAGE_ENCRYPTION_KEYS, na mesma
ordem. Não gerar novas chaves de cifragem só para o worker. Não copiar variáveis
VERCEL para este serviço. O worker recusa arrancar se VERCEL estiver definida.

Para modo real, preparar e validar todos os parâmetros de .env.example nos dois
serviços (incluindo modelo, Meta, IA, cifragem e limites) antes de mudar o modo.
O arranque pode criar tabelas e o worker processa jobs/retencão/notificações:
**não é uma verificação apenas de leitura**. Rever jobs existentes e política de
retenção antes da activação autorizada. Nunca testar com mensagens de clientes.

## 3. Activar apenas depois da aprovação

```sh
# Validar estrutura e campos obrigatórios sem imprimir configuração/segredos:
docker compose --env-file .env.worker -f compose.worker.yaml config --quiet
# Activa o processamento, apenas quando autorizado:
docker compose --env-file .env.worker -f compose.worker.yaml up -d --build
docker compose --env-file .env.worker -f compose.worker.yaml ps
```

Não executar `config` sem `--quiet` nem partilhar logs sem remover dados pessoais.
`.env.worker` está excluído do Git e do contexto Docker; os segredos são injectados
apenas no container em execução. O servidor e os administradores do Docker
continuam a ter acesso aos segredos: restringir acessos e cópias de segurança.

Consultar /health na API e confirmar worker_alive=true e heartbeat recente.
Em demo isso não comprova chamadas reais a Meta/IA. Um heartbeat ausente exige
verificar a base partilhada, configuração e processo, não esconder o alerta.

## 4. Parar/reverter

```sh
docker compose --env-file .env.worker -f compose.worker.yaml stop
```

Parar não desfaz mensagens, retenção ou trabalhos já executados. Não apagar a
base nem volumes. Usar uma revisão anterior aprovada para rollback do código.

## Verificação desta preparação

Dois contratos offline escritos antes das alterações falharam: .env.worker
entrava no contexto Docker e faltava a configuração do worker. Correcções:
`.dockerignore` exclui .env.*; compose.worker.yaml define worker separado,
PostgreSQL obrigatório, reinício e encerramento gracioso, sem porta pública.
Os testes de contrato não substituem construir/arrancar o container num servidor.
Login remoto e perfil dependem do responsável; alojamento/activação pendentes.
