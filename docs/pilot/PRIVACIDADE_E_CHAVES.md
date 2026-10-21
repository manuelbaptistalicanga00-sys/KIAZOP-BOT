# Conteúdo, retenção, migração e chaves

Documento técnico, **não declaração de conformidade legal**. Operador/cliente devem
validar finalidade, acessos, direitos, transferências, prazos e procedimentos com os
responsáveis competentes. Um negócio por instalação; API administrativa tem chave
única, não perfis de acesso nem aprovação de quatro olhos.

## Âmbito e limitações da cifragem

`MESSAGE_ENCRYPTION_KEYS`: lista de chaves Fernet separadas por vírgulas, **nova primeiro**.
A aplicação de produção falha no arranque sem chave. Chave inválida também falha.
DEMO sem chave permanece compatível em claro; nunca usar demo com dados reais.
Para demo persistente cifrada, configurar chave estável (não é gerada efemeramente).

Campos cifrados na escrita e descifrados na leitura pelo adaptador DB:

- `msgs.text`, `inbox.payload`, `jobs.reply/result`;
- `business_config.payload`;
- nomes/descrições/preferências em requests/bookings;
- operador/evidência em reconciliation_log.

Fernet autentica o conteúdo; chave errada/ciphertext adulterado não produz texto.
Chaves são externas à DB. IDs, números, timestamps, estados, índices e parte da
configuração operacional permanecem **em claro**; Fernet revela timestamp do token.
DBA/aplicação com chave podem descifrar. Não é encriptação ponta-a-ponta nem KMS.
SQL interno passa por adaptador de campos conhecidos; SQL directo/novas tabelas
podem contorná-lo e exigem revisão/teste. Acesso ao engine bruto fica reservado a
migração offline, testes e administração restrita; não existe endpoint SQL.

## Retenção e operações

Conteúdo e registos operacionais associados: **90 dias** por defeito (não ajustável
pelo cliente no painel). Worker tenta expurgo diário com estado persistente. Um
job/notificação activa impede eliminação; drenar/parar produtores e workers para
manutenção previsível. Expurgo manual: `POST /api/privacy/purge?confirm=purge`.

- `GET /api/privacy/{numero}`: exporta mensagens, jobs, solicitações, marcações,
  notificações e inbox associados, descifrados para administrador autenticado.
  Exportação contém dados pessoais e metadados internos: entregar só o necessário
  após revisão, nunca guardar no Git/chat. Exportar antes de eliminar quando adequado.
- `DELETE /api/privacy/{numero}?confirm=delete`: elimina dados associados na instalação,
  incluindo fila/inbox/leases/receipts/notificações e pausas; mantém prova pseudonimizada
  da operação em privacy_audit. Registo activo devolve 409; não corta envio em curso.
- Auditoria export/delete/purge contém acção, data e HMAC do número, não número bruto.
  Retenção da auditoria: 90 dias. Não é append-only/imutável; DBA pode alterá-la.
- Registos `seen` são removidos com os jobs correspondentes. IDs históricos órfãos,
  sem data/número nas versões antigas, exigem inventário no ensaio de migração; não
  se pode reconstruir a data original. São limitação de metadados legados, não uma
  promessa de expurgo integral histórico. Eliminar deduplicação permite que o provedor
  reintroduza conteúdo num replay posterior: webhook de origem também deve ser tratado.
- Não elimina cópias Meta/Anthropic, downloads/exportações, snapshots, logs do host,
  backups ou configuração pública do negócio. Esses suportes exigem política separada.
- Uvicorn access logs da aplicação mascaram números e querystrings. Proxy/WAF/log
  collector externo não é controlado por este código; validar redacção no host.

## Migração reversível (offline)

**Nunca iniciar sobre produção neste ambiente de desenvolvimento.** Procedimento do
operador: parar API/worker, fazer backup cifrado com acesso restrito, criar cópia
sintética/staging independente e só depois planear intervenção autorizada.

1. Guardar chaves em secret manager externo (não no Git, linha de comando ou relatório).
   Configurar a mesma chave na API e worker. Testar recuperação sem a máquina original.
2. Na cópia SQLite offline, executar:
   `python privacy_migrate.py --sqlite-copy CAMINHO_COPIA --mode encrypt --confirm-offline-copy`.
   A ferramenta lê chaves do ambiente, não imprime valores. Operação atómica;
   erro de chave/corrupção faz rollback. Repetir encrypt não cria dupla camada.
3. Testar leitura, envio simulado e raw SELECT sem texto claro. Só depois promover
   revisão/base/chaves em conjunto. `ALLOW_LEGACY_PLAINTEXT=false` em produção;
   se true, aceita leitura de dados antigos, mas **não** é estado de produção aprovado.
4. Reversão **na cópia**:
   `python privacy_migrate.py --sqlite-copy CAMINHO_COPIA --mode decrypt --confirm-offline-copy`.
   Devolve valores em claro; não destrói schema/IDs/estados. Requer todas as chaves
   necessárias. Não fazer downgrade para código antigo ligado à DB cifrada.
5. Para PostgreSQL, `privacy.migrate(Database(url_da_copia), Vault(chaves), modo)` usa
   transacção e SQL nativo, sem importar bot ou usar URLs implícitas. O helper foi
   testado em PostgreSQL local descartável; CLI fornecido é apenas SQLite. Neon e
   promoção de cópia/restauro em PostgreSQL remoto: **não verificados**, exigem roteiro
   operacional separado e confirmação explícita de alvo antes de qualquer escrita.

Prova: `test_b5_reversible_migration_on_synthetic_copy` cria original sintético,
faz backup SQLite para outra DB, cifra, roda chave, descifra e confirma original
inalterado. `test_b5_wrong_key_rolls_back_migration` confirma rollback integral.
`test_postgres_ciphertext_and_reversible_migration` prova helper em PostgreSQL local.
Não se usaram nem copiaram dados de produção.

**Cifrar por UPDATE não apaga versões anteriores em disco.** WAL/free pages SQLite,
MVCC/WAL PostgreSQL, snapshots e backups podem reter plaintext. Usar volumes/backups
cifrados; para SQLite offline, planear checkpoint/TRUNCATE e VACUUM numa nova cópia;
para PostgreSQL, planear reescrita/expiração de snapshots com DBA. Esses passos de
sanitização física e descarte seguro não foram ensaiados nem garantidos por este lote.

## Política proposta de rotação (operador deve aprovar)

- Rotação periódica proposta: **90 dias**, e imediatamente perante suspeita de exposição.
  Não há scheduler de rotação automática: evita perder chaves/dados por surpresa.
- Gerar chave nova no secret manager; distribuir `[nova, antigas...]` à API/worker,
  de forma coordenada. Novas escritas usam a primeira; leitura aceita as anteriores.
- Drenar serviços, backup cifrado, ensaio em cópia. `--mode rotate` recifra com a nova;
  confirmar leitura usando **só a nova** na cópia e reexecutar regressões.
- Guardar anteriores separadamente até expirar a última cópia/backup que as exige,
  mais o prazo operacional aprovado para rollback. Não retirar chave por calendário
  sem inventário de backups; não guardar chaves junto dos backups cifrados.
- Só retirar antiga da aplicação depois de migrar todos os campos/instâncias e
  validar restauro. Destruição final de chave só após autorização/inventário; perder
  a chave pode tornar o conteúdo irrecuperável. Rever acesso e registar responsável.
- Em incidente: revogar acessos/tokens conforme necessário, preservar evidências
  restritas e avaliar obrigações com responsáveis competentes. Não prometer prazo
  legal universal nem que recifrar resolve exposição anterior.
