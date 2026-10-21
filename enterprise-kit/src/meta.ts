import { z } from 'zod';

const Digits = z.string().regex(/^\d+$/);
const Token = z.object({ access_token: z.string().min(1) });
export type MetaSettings = { appId: string; appSecret: string; graphVersion: string };
export class MetaAdapter {
  constructor(private settings: MetaSettings, private http: typeof fetch = fetch) {
    Digits.parse(settings.appId);
    if (!/^v\d+\.\d+$/.test(settings.graphVersion)) throw new Error('Versão Meta inválida');
  }
  private async request(path: string, token?: string, body?: object) {
    const response = await this.http(`https://graph.facebook.com/${this.settings.graphVersion}/${path}`, {
      method: body ? 'POST' : 'GET',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), 'Content-Type': 'application/json' },
      ...(body ? { body: JSON.stringify(body) } : {}), signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) throw new Error(`META_HTTP_${response.status}`); // Nunca logar token/payload integral.
    return response.json();
  }
  async exchangeAndVerify(code: string, wabaId: string, phoneNumberId: string) {
    Digits.parse(wabaId); Digits.parse(phoneNumberId);
    // O SDK usa exchangeable code; só o servidor conhece o app_secret.
    const params = new URLSearchParams({ client_id: this.settings.appId,
      client_secret: this.settings.appSecret, code });
    const token = Token.parse(await this.request(`oauth/access_token?${params}`)).access_token;
    const debugParams = new URLSearchParams({ input_token: token });
    const debug = z.object({ data: z.object({ app_id: z.string(), is_valid: z.boolean() }) }).parse(
      await this.request(`debug_token?${debugParams}`, `${this.settings.appId}|${this.settings.appSecret}`));
    if (!debug.data.is_valid || debug.data.app_id !== this.settings.appId) throw new Error('META_INVALID_GRANT');
    // Confirmar no servidor que o número pertence à conta autorizada; IDs do browser não são prova.
    let path: string | undefined = `${wabaId}/phone_numbers?fields=id&limit=100`;
    let found = false;
    for (let page = 0; path && page < 20; page++) {
      const result = z.object({ data: z.array(z.object({ id: z.string() })),
        paging: z.object({ cursors: z.object({ after: z.string().optional() }).optional(), next: z.string().optional() }).optional(),
      }).parse(await this.request(path, token));
      if (result.data.some(p => p.id === phoneNumberId)) { found = true; break; }
      const after: string | undefined = result.paging?.next ? result.paging?.cursors?.after : undefined;
      // Nunca seguir URLs de paging arbitrários nem enviar token para outro domínio.
      path = after ? `${wabaId}/phone_numbers?fields=id&limit=100&after=${encodeURIComponent(after)}` : undefined;
    }
    if (!found) throw new Error('META_ASSET_NOT_AUTHORIZED');
    return { token, wabaId, phoneNumberId };
  }
  async subscribe(wabaId: string, token: string) {
    return this.request(`${Digits.parse(wabaId)}/subscribed_apps`, token, {});
  }
  async registerStandardNumber(phoneId: string, token: string, pin: string) {
    if (!/^\d{6}$/.test(pin)) throw new Error('PIN inválido');
    return this.request(`${Digits.parse(phoneId)}/register`, token, { messaging_product: 'whatsapp', pin });
  }
  async sendApprovedTest(phoneId: string, token: string, phone: string, templateName: string, language: string) {
    if (!/^\+[1-9]\d{6,14}$/.test(phone)) throw new Error('Telefone inválido');
    // Chamador tem de validar opt-in e aprovação/idioma/categoria do template.
    return this.request(`${Digits.parse(phoneId)}/messages`, token, {
      messaging_product: 'whatsapp', to: phone.slice(1), type: 'template',
      template: { name: templateName, language: { code: language } },
    });
  }
}
