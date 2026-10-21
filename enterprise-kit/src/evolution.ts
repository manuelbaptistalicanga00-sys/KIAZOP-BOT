import { z } from 'zod';
const QR = z.string().max(300000).regex(/^data:image\/png;base64,[A-Za-z0-9+/=]+$/);
export class EvolutionDemoAdapter {
  constructor(private baseUrl: string, private apiKey: string, private enabled: boolean,
    private http: typeof fetch = fetch) {
    if (new URL(baseUrl).protocol !== 'https:') throw new Error('Evolution exige HTTPS');
  }
  private async call(path: string, body?: object) {
    if (!this.enabled) throw new Error('QR_DEMO_DISABLED');
    const response = await this.http(new URL(path, this.baseUrl), {
      method: body ? 'POST' : 'GET', headers: { apikey: this.apiKey, 'Content-Type': 'application/json' },
      ...(body ? { body: JSON.stringify(body) } : {}), signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) throw new Error(`QR_HTTP_${response.status}`);
    return response.json();
  }
  async create(serverGeneratedName: string, riskAccepted: boolean) {
    if (!riskAccepted) throw new Error('QR_RISK_NOT_ACCEPTED');
    // Nome gerado pelo servidor, nunca aceitar nome de outra instância do navegador.
    if (!/^bo-[a-f0-9-]{36}$/.test(serverGeneratedName)) throw new Error('Instância inválida');
    return this.call('/instance/create', {
      instanceName: serverGeneratedName, integration: 'WHATSAPP-BAILEYS', qrcode: false,
    });
  }
  async qr(instance: string) {
    if (!/^bo-[a-f0-9-]{36}$/.test(instance)) throw new Error('Instância inválida');
    const data = z.object({ base64: QR }).parse(await this.call(`/instance/connect/${encodeURIComponent(instance)}`));
    return data.base64;
  }
  async state(instance: string) {
    if (!/^bo-[a-f0-9-]{36}$/.test(instance)) throw new Error('Instância inválida');
    const result = z.object({ instance: z.object({ state: z.string() }) }).parse(
      await this.call(`/instance/connectionState/${encodeURIComponent(instance)}`));
    return result.instance.state === 'open' ? 'connected' : 'reconnect_required';
  }
}
// Contrato de referência Evolution v2. Fixar versão e testar respostas no gateway real.
// Webhook autenticado, armazenamento de sessão e reconexão pertencem ao gateway privado,
// não à função Vercel. Nunca prometer que este atalho evita bloqueios do WhatsApp.
