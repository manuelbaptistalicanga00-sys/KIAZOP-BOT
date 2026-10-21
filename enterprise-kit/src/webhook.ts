import { createHmac, timingSafeEqual } from 'node:crypto';
export function validMetaSignature(raw: Buffer, signature: string | null, secret: string) {
  if (!secret || !signature || !/^sha256=[a-f0-9]{64}$/.test(signature)) return false;
  const expected = 'sha256=' + createHmac('sha256', secret).update(raw).digest('hex');
  const a = Buffer.from(signature), b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}
export interface DurableIngress {
  // Implementar com inbox + outbox na MESMA transacção e UNIQUE(provider,event_id).
  // Resolver tenant por asset verificado num registo privado, não pelo JSON do chamador.
  persistAndSchedule(body: unknown): Promise<void>;
}
export async function metaWebhook(request: Request, secret: string, ingress: DurableIngress) {
  // O reverse proxy também deve limitar o corpo ANTES de o carregar em memória.
  const raw = Buffer.from(await request.arrayBuffer());
  if (raw.length > 1000000) return new Response('Payload demasiado grande', { status: 413 });
  if (!validMetaSignature(raw, request.headers.get('x-hub-signature-256'), secret))
    return new Response('Assinatura inválida', { status: 403 });
  let body: unknown;
  try { body = JSON.parse(raw.toString('utf8')); }
  catch { return new Response('Evento inválido', { status: 400 }); }
  try { await ingress.persistAndSchedule(body); }
  catch { return new Response('Tente novamente', { status: 503 }); }
  return Response.json({ ok: true }); // ACK só após persistência, não após a IA responder.
}
