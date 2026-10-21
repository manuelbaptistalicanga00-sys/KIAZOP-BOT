# Bot de Atendimento IA para WhatsApp

## Instalar (local, para testar)
1. `pip install -r requirements.txt`
2. Copia `.env.example` para `.env`, preenche e carrega as variáveis (ou exporta-as).
3. `uvicorn bot:app --port 8000`
4. Expõe com `ngrok http 8000` e no Meta for Developers (WhatsApp > Configuration) define o webhook `https://SEU-URL/webhook` com o VERIFY_TOKEN e subscreve o campo `messages`.

## Colocar em produção
Railway, Render ou um VPS pequeno (~5-10 USD/mês). Usa um volume para guardar `bot.db`.

## Personalizar para cada cliente
Edita só `negocio.json` (nome, tom, serviços, horários, perguntas frequentes). Sem reiniciar.

## Funções
- Responde e tira dúvidas com base no negocio.json
- Recolhe agendamentos e avisa o dono por WhatsApp
- Passa para humano e pausa o bot nessa conversa (`/retomar/NUMERO?key=ADMIN_KEY` reativa)
- Lista de agendamentos em `/agendamentos?key=ADMIN_KEY`
- Memória das últimas 20 mensagens por cliente

## Limites (diz sempre ao cliente)
- Só responde ao que estiver no negocio.json
- Mensagens fora da janela de 24h exigem templates aprovados pela Meta
- Custos da Meta e da API Claude são pagos pelo cliente

## Novidades da versão 2
- **Painel visual** em `/painel?key=ADMIN_KEY`: agendamentos, conversas, botão para assumir uma conversa (pausa o bot) e reativá-lo
- **Simulador** `python simular.py`: testa a IA no terminal sem Meta nem ngrok
- **Segurança:** valida a assinatura da Meta (APP_SECRET), ignora mensagens duplicadas, limita mensagens por hora por cliente
- **Robustez:** se a IA falhar, o cliente recebe uma resposta educada e o dono é avisado
- **Áudio/imagens:** resposta educada a pedir texto
- **Docker:** `docker build -t bot . && docker run -p 8000:8000 -v bot-data:/data --env-file .env bot`
