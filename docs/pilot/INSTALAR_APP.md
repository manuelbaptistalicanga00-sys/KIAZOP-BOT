# KIAZOP instalável e instalações isoladas

## Arquitectura escolhida

Uma instalação por cliente, com base PostgreSQL, segredos, número WhatsApp e
worker próprios. Nunca apontar duas empresas para a mesma base. O software
continua single-business: isto NÃO implementa registo multiempresa, subscrições,
provisionamento automático nem uma plataforma SaaS completa.

A configuração Compose do worker é preparação, não um servidor contratado.
A activação exige alojamento e custos aprovados. Ver WORKER_E_ACESSO.md.

## Instalar a aplicação web (depois desta revisão estar publicada)

Endereço: https://kiazop-bot.vercel.app/painel

- Android/Chrome: abrir o endereço por HTTPS e usar «Instalar aplicação» ou
  «Adicionar ao ecrã inicial» no menu do navegador.
- iPhone/iPad/Safari: Partilhar → Adicionar ao ecrã principal → Abrir como app,
  quando essa opção estiver disponível.
- Computador Chrome/Edge: usar o ícone/menu de instalação, se disponível.

A opção exacta depende do navegador/sistema. Não há APK, IPA ou publicação numa
loja. Uma PWA é instalada através do navegador; não é um executável nativo.
A autenticação continua obrigatória. É necessária ligação à internet. O service
worker não intercepta pedidos nem mantém cache de conversas/chaves. Instalar a
PWA não configura perfil, não inicia worker e não activa WhatsApp ou IA reais.
O worker de instalação web e o worker Python de atendimento são processos
completamente diferentes: o primeiro NÃO processa a fila WhatsApp.

Se aparecer uma revisão antiga, actualizar a página. Se não houver opção de
instalação, confirmar a disponibilidade do manifest e HTTPS e seguir o menu do
navegador; não prometer um aviso de instalação em todos os dispositivos.

## Segurança e verificação

Três testes escritos primeiro falharam (manifest, rota do service worker e
metadados ausentes); depois passaram. Verificam manifesto, ícones PNG locais,
autenticação preservada e ausência de cache/intercepção de pedidos no service
worker. A instalação num dispositivo Android/iOS real ainda não foi verificada.
