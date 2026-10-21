# Integração de funcionalidades — API oficial preservada

## Decisão confirmada

Em 2026-10-21, o responsável escolheu **manter a API oficial**. Não substituir
FastAPI/Cloud API por OpenWA, não activar ligação QR não oficial, não ligar
números nem contratar alojamento. Um negócio por instalação permanece a regra.
«Premium/ultra» descreve a intenção de qualidade, não certificação, SLA ou paridade.

## Fonte efectivamente revista

- Repositório: https://github.com/manuelbaptistalicanga00-sys/KIAZOP-BOT-whatsapp
- Revisão consultada: `2d6f25ab29fff9f16bc97ac308e22eb468822ad4`.
- A branch predefinida consultada foi
  `dependabot/npm_and_yarn/dashboard/minor-and-patch-ee154b349c`.
- README, package.json e inventários dashboard/src/pages e src/modules lidos via
  GitHub. O conteúdo identifica-se como OpenWA 0.25.0 (NestJS, React, Node >=22.19,
  licença MIT), com motores whatsapp-web.js/Baileys. Isto é inspecção de fonte,
  não prova de execução das funcionalidades anunciadas pelo outro projecto.
- Não foi importado código externo nem executado postinstall do repositório.
  Se houver reutilização posterior, preservar licença/autoria e rever dependências.

## Matriz de adaptação inicial

| Área na fonte | Situação neste projecto / próximo passo |
| --- | --- |
| Dashboard/estatísticas | Já existe painel premium responsivo; métricas locais, não facturação oficial |
| Chats/pesquisa/filtros | Etapa 1: pesquisa telefónica global e filtros humano/sem pendência humana, autenticados e paginados |
| Sessões, QR, pairing, takeover, proxy por sessão | Não importar o motor não oficial; conexão oficial requer desenho próprio e configuração Meta |
| Histórico, paginação e takeover humano | Histórico local paginado, pausa e reactivação já existem; não equivalem a sincronizar todo o histórico WhatsApp |
| Textos e recibos de mensagem | Envio/fila e recibos já existem via Cloud API; verificação real de fornecedor ainda pendente |
| Media e arquivo (chat-media/media) | Pendente: desenho de upload/download autorizado, limites, tipos e retenção; não copiar rotas incompatíveis |
| Reacções/edição/mensagens especiais | Pendente de confirmar suporte oficial e criar contratos específicos; não prometer equivalência |
| Templates/testador | Laboratório local já existe; gerir templates aprovados pela Meta é etapa separada, não confundir com modelos de sector |
| Contactos, catálogo e etiquetas | Perfil/catálogo informativo já existe; CRM, etiquetas locais e catálogo Meta são funcionalidades distintas, ainda pendentes |
| Grupos, chamadas, canais/newsletters, statuses | Sem paridade estabelecida; confirmar capacidades/elegibilidade oficiais actuais antes de implementar |
| Envio em lote/automação | Não importar disparo indiscriminado; depende de consentimento, políticas, limites e aprovação operacional |
| Webhooks/events | Entrada HMAC e recibos existem; webhooks de saída/eventos em tempo real não importados |
| API keys, roles e escopos por chat | Chave administrativa existente não equivale a RBAC; desenho/migração e testes de isolamento pendentes |
| Audit/logs | Reconciliação/privacidade e logs filtrados existem; trilho administrativo completo e interface de logs pendentes |
| Plugins, integrações, MCP | Não importados; exigir fronteiras de autorização e confirmar APIs de cada integração |
| Queue, health, metrics | Fila durável, leases, batimento e alertas já existem; worker remoto ainda depende de alojamento autorizado |
| Infra/settings/Docker | PostgreSQL e preparação Docker existentes; não transplantar painel de controlo de infra com privilégios elevados |
| Redis, S3, backups/import-export | Não copiar configurações da fonte; backup/restauro e migração devem ter testes próprios e aprovação |
| Perfil WhatsApp | Diferente do perfil de conhecimento KIAZOP; gerir dados do número requer endpoints oficiais próprios |

A existência de um módulo na fonte não comprova que funcione nem significa que
seja permitido pelo canal oficial. Nenhuma linha pendente está marcada como pronta.

## Etapa 1 implementada

- `GET /api/dashboard` aceita `phone_query` (máx. 30 caracteres: dígitos, espaços
  e um + inicial) e `conversation_state=all|human|assistant`.
- Pesquisa em todos os telefones registados antes de paginar; sem pesquisa no
  conteúdo cifrado, desencriptação em massa ou procura no WhatsApp remoto.
- Humano = pausa manual OU notificação pendente/em envio/falhada não reconhecida.
  Sem pendência humana não significa que o worker, o perfil ou o canal estejam prontos.
- Contagem filtrada separada das métricas globais. Ordenação determinística.
  Recentes na visão geral reflectem os resultados/filtros actuais.
- Filtros explícitos «Aplicar»/«Limpar», reinício na página 1 e indicação do total.
  O laboratório mantém acesso à sua conversa sintética mesmo sem resultados.
- Sem schema novo, alteração de dados de produção, nova credencial ou envio real.

## Evidência e limites

Antes do backend: 8 testes novos falharam e o de autenticação já passou. Depois:
9 passaram. Dois testes adicionais de ligação ao painel/preservação do laboratório
falharam antes das alterações correspondentes; depois os 11 passaram.
Dados exclusivamente sintéticos. Sem activar Claude, Meta ou números reais.
Os contratos de apresentação não substituem verificação completa em navegador.
Testes Cloud API reais e validação de todos os módulos da fonte continuam pendentes.

## Sequência proposta após esta etapa

1. Etiquetas/notas locais e respostas guardadas (não templates Meta aprovados).
2. Envio humano e multimédia pela fila oficial, com controlo da janela e permissões.
3. Gestão de templates Meta e conexão oficial com contratos actualizados.
4. Operadores/permissões, auditoria e integrações autorizadas.

Cada etapa exige testes primeiro e revisão de migração/privacidade. Não executar
este plano inteiro como uma cópia monolítica nem anunciar paridade completa.
