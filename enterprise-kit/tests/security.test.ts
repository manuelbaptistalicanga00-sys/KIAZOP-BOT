import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { validMetaSignature, metaWebhook } from '../src/webhook.js';
import { MetaAdapter } from '../src/meta.js';
import { QRStartSchema, TestSchema, TemplateSchema, requireRole, type Actor } from '../src/contracts.js';
import { EvolutionDemoAdapter } from '../src/evolution.js';

const actor: Actor = { tenantId: '11111111-1111-4111-8111-111111111111', userId: '22222222-2222-4222-8222-222222222222', role: 'agent' };
test('RBAC bloqueia agentes na gestão de ligações', () => {
  assert.throws(() => requireRole(actor, ['owner', 'admin']));
  assert.doesNotThrow(() => requireRole({ ...actor, role: 'admin' }, ['admin']));
});
test('opt-in, risco QR, telefone e factos têm de ser explícitos', () => {
  assert.equal(QRStartSchema.safeParse({ riskAccepted: false }).success, false);
  assert.equal(TestSchema.safeParse({ phone: '+244900000001', consent: false }).success, false);
  assert.equal(TestSchema.safeParse({ phone: '900000001', consent: true }).success, false);
  assert.equal(TestSchema.safeParse({ phone: '+244900000001', consent: true }).success, true);
  assert.equal(TemplateSchema.safeParse({ sector: 'loja', businessName: 'Loja A', hours: '09–17', services: 'Café', factsConfirmed: false }).success, false);
  assert.equal(TemplateSchema.safeParse({ sector: 'loja', businessName: 'Loja A', hours: '09–17 (exemplo: substitua)', services: 'Café', factsConfirmed: true }).success, false);
});
test('HMAC verifica bytes e nunca aceita assinatura ausente', () => {
  const raw = Buffer.from('{"entry":[]}');
  const sig = 'sha256=' + createHmac('sha256', 'test-secret').update(raw).digest('hex');
  assert.equal(validMetaSignature(raw, sig, 'test-secret'), true);
  assert.equal(validMetaSignature(Buffer.from('{}'), sig, 'test-secret'), false);
  assert.equal(validMetaSignature(raw, null, 'test-secret'), false);
});
test('webhook só confirma depois de guardar o evento', async () => {
  const body = '{"entry":[]}';
  const sig = 'sha256=' + createHmac('sha256', 'test-secret').update(body).digest('hex');
  const request = () => new Request('https://example.test/webhooks/meta', { method: 'POST', body, headers: { 'x-hub-signature-256': sig } });
  let persisted = false;
  const ok = await metaWebhook(request(), 'test-secret', { async persistAndSchedule() { persisted = true; } });
  assert.equal(ok.status, 200); assert.equal(persisted, true);
  const failed = await metaWebhook(request(), 'test-secret', { async persistAndSchedule() { throw Error('DB unavailable'); } });
  assert.equal(failed.status, 503);
});
test('token de outra app é rejeitado antes de subscrever ou registar número', async () => {
  let calls = 0;
  const mock = (async () => {
    calls++;
    return Response.json(calls === 1 ? { access_token: 'server-token' } : { data: { app_id: '999', is_valid: true } });
  }) as typeof fetch;
  const meta = new MetaAdapter({ appId: '123', appSecret: 'server-secret', graphVersion: 'v26.0' }, mock);
  await assert.rejects(() => meta.exchangeAndVerify('one-time-code', '321', '456'), /INVALID_GRANT/);
  assert.equal(calls, 2);
});
test('número fora da WABA autorizada é rejeitado', async () => {
  let calls = 0;
  const mock = (async () => {
    calls++;
    return Response.json(calls === 1 ? { access_token: 'server-token' } : calls === 2
      ? { data: { app_id: '123', is_valid: true } } : { data: [{ id: '789' }] });
  }) as typeof fetch;
  const meta = new MetaAdapter({ appId: '123', appSecret: 'server-secret', graphVersion: 'v26.0' }, mock);
  await assert.rejects(() => meta.exchangeAndVerify('code', '321', '456'), /ASSET_NOT_AUTHORIZED/);
});
test('QR não chama o fornecedor sem aceitação do risco', async () => {
  let called = false;
  const qr = new EvolutionDemoAdapter('https://gateway.example.test', 'server-secret', true,
    (async () => { called = true; return Response.json({}); }) as typeof fetch);
  await assert.rejects(() => qr.create('bo-11111111-1111-4111-8111-111111111111', false), /RISK/);
  assert.equal(called, false);
});
