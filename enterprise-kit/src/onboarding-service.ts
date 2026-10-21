import { MetaFinishSchema, requireRole, type Actor } from './contracts.js';
import { MetaAdapter } from './meta.js';

export interface OnboardingRepository {
  // Claim atómico, TTL <= 10 min; valida tenant, utilizador, nonce e estado não consumido.
  claimAttempt(id: string, nonce: string, actor: Actor): Promise<{
    verifiedMode: 'standard' | 'coexistence';
    // Derivado de evento account_update assinado/consulta de servidor, nunca de um flag do browser.
    modeVerified: boolean;
  }>;
  saveConnection(actor: Actor, data: { wabaId: string; phoneNumberId: string; encryptedToken: string }): Promise<void>;
  audit(actor: Actor, action: string, metadata: object): Promise<void>;
  // Padrão outbox: grava evento de activação na mesma transacção do estado da ligação.
  activateWithOutbox(actor: Actor, externalId: string): Promise<void>;
}
export async function finishMeta(actor: Actor, body: unknown, repo: OnboardingRepository,
  meta: MetaAdapter, encrypt: (plaintext: string, tenantId: string) => Promise<string>,
  registrationPin: () => string) {
  requireRole(actor, ['owner', 'admin']);
  const input = MetaFinishSchema.parse(body);
  const attempt = await repo.claimAttempt(input.attemptId, input.nonce, actor);
  if (!attempt.modeVerified) throw new Error('A aguardar confirmação segura da Meta.');
  const grant = await meta.exchangeAndVerify(input.code, input.wabaId, input.phoneNumberId);
  await repo.saveConnection(actor, {
    wabaId: grant.wabaId, phoneNumberId: grant.phoneNumberId,
    encryptedToken: await encrypt(grant.token, actor.tenantId),
  });
  if (attempt.verifiedMode === 'standard') {
    await meta.registerStandardNumber(grant.phoneNumberId, grant.token, registrationPin());
  }
  await meta.subscribe(grant.wabaId, grant.token);
  // Não devolver o token ao cliente e não marcar o teste como entregue nesta fase.
  await repo.activateWithOutbox(actor, grant.phoneNumberId);
  await repo.audit(actor, 'whatsapp.connected', { provider: 'meta', phoneNumberId: grant.phoneNumberId });
  return { accepted: true };
}
