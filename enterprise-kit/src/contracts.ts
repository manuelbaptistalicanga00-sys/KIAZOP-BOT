import { z } from 'zod';

export const UUID = z.string().uuid();
export const E164 = z.string().regex(/^\+[1-9]\d{6,14}$/);
export const ActorSchema = z.object({
  tenantId: UUID, userId: UUID,
  role: z.enum(['owner', 'admin', 'manager', 'agent', 'analyst']),
});
export type Actor = z.infer<typeof ActorSchema>;
export type ConnectionStatus = 'disconnected' | 'connecting' | 'qr_pending' | 'connected' | 'reconnect_required' | 'failed';
export const StateSchema = z.object({
  status: z.enum(['disconnected', 'connecting', 'qr_pending', 'connected', 'reconnect_required', 'failed']),
  provider: z.enum(['meta', 'qr']).nullable(),
  // QR é um segredo temporário de emparelhamento: nunca persistir em analytics.
  qrDataUrl: z.string().max(300000).regex(/^data:image\/png;base64,[A-Za-z0-9+/=]+$/).optional(),
  templateReady: z.boolean(), firstAIReplyDelivered: z.boolean(),
  inboundTestUrl: z.string().url().refine(v => new URL(v).hostname === 'wa.me').optional(),
  publicMessage: z.string().max(300).optional(),
});
export type ConnectionState = z.infer<typeof StateSchema>;
export const MetaFinishSchema = z.object({
  attemptId: UUID, nonce: z.string().min(32).max(256), code: z.string().min(1).max(4096),
  wabaId: z.string().regex(/^\d+$/), phoneNumberId: z.string().regex(/^\d+$/),
});
export const QRStartSchema = z.object({ riskAccepted: z.literal(true) });
export const TestSchema = z.object({ phone: E164, consent: z.literal(true) });
export const TemplateSchema = z.object({
  sector: z.enum(['clinica', 'salao', 'imobiliaria', 'restaurante', 'loja', 'outro']),
  businessName: z.string().trim().min(2).max(160),
  hours: z.string().trim().min(1).max(500).refine(value => !/exemplo|substitua/i.test(value), 'Substitua o horário de exemplo pelos dados reais.'),
  services: z.string().trim().min(1).max(2400),
  factsConfirmed: z.literal(true),
});
export function requireRole(actor: Actor, allowed: Actor['role'][]) {
  if (!allowed.includes(actor.role)) throw new Error('FORBIDDEN');
}
// Resolver Actor exclusivamente a partir da sessão assinada + membership verificada
// no backend. Nunca aceitar tenantId/role/userId enviados no JSON pelo navegador.
export interface Identity { requireActor(request: Request): Promise<Actor> }
export interface Audit {
  append(actor: Actor, action: string, safeMetadata: Record<string, unknown>): Promise<void>;
}
