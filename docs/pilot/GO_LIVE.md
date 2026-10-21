# Checklist de go-live — ainda NÃO aprovado

Instalação/cliente: __________________  Ambiente: __________________
Responsável técnico: _______________  Responsável do cliente: _______________
Data prevista: _____________________  Revisão: _____________________________

- [x] Checkpoint local 8805838 antes das correcções.
- [x] Baseline e regressões B1–B3 executadas com dados sintéticos.
- [x] Webhook só persiste; worker separado, leases e quarentena implementados localmente.
- [x] Notificação falhada visível; perfil guardado condiciona IA.
- [x] B4 local: CSP/login/ADMIN_KEY/UTF-8/rate limiting e limites pré-leitura.
- [ ] Validar identidade de IP/proxy e protecção volumétrica no host.
- [x] B5 local: retenção/expurgo/exportação/eliminação/cifragem/rotação e auditoria.
- [ ] Ensaiar migração/rotação/restore remoto, descarte de plaintext histórico e política de backups.
- [x] F2 seleccionada local: env sem duplicados, MODEL/diagnóstico IA, erros, tags, budget, paginação.
- [ ] F2 restante: diagnósticos/provas reais, saúde da fila e UX não seleccionada.
- [ ] F3: defeitos reais do kit enterprise e contratos oficiais actuais.
- [x] PostgreSQL real local: claims/leases/recuperação/receipt e cifragem helper.
- [ ] Neon pooled, duas instâncias reais e recuperação provados em staging.
- [ ] Meta real de testes: envio/receipt/correlação/ambiguidade e template fora de janela.
- [ ] Perfil e factos confirmados pelo cliente; `/health.profile_ready=true`.
- [ ] API+worker sempre ligado, restart/drain e monitorização operacionais.
- [ ] Backup/restore e rollback ensaiados sem perda de idempotência.
- [ ] Custos/limites, acessos, finalidade e tratamento de dados aceites pelos responsáveis.
- [ ] Equipa acompanha painel; procedimento humano para incertos e notificações falhadas.

**Decisão actual: BLOQUEADO.** Testes unitários não aprovam uso pago com dados reais.
Nenhuma certificação, conformidade legal ou SLA é declarada.

Aprovação técnica (só após fechar itens): __________________ Data: __________
Aprovação do cliente: ____________________________________ Data: __________
Evidências e excepções aceites: ___________________________________________
