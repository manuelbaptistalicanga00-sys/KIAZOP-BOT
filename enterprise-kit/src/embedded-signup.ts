type SDK = { init(options: object): void; login(callback: (r: { authResponse?: { code?: string } }) => void, options: object): void };
declare global { interface Window { FB?: SDK; fbAsyncInit?: () => void } }
let loading: Promise<SDK> | undefined;
export function loadMetaSDK(appId: string, graphVersion: string): Promise<SDK> {
  if (!loading) loading = new Promise<SDK>((resolve, reject) => {
    const init = () => {
      if (!window.FB) { reject(new Error('Não foi possível carregar a Meta.')); return; }
      window.FB.init({ appId, version: graphVersion, xfbml: false, autoLogAppEvents: false });
      resolve(window.FB);
    };
    if (window.FB) { init(); return; }
    window.fbAsyncInit = init;
    const script = document.createElement('script'); script.src = 'https://connect.facebook.net/pt_PT/sdk.js';
    script.async = true; script.crossOrigin = 'anonymous';
    script.onerror = () => { loading = undefined; reject(new Error('A Meta não carregou. Verifique a ligação e tente novamente.')); };
    document.head.append(script);
  });
  return loading;
}
export async function embeddedSignup(appId: string, configId: string, graphVersion: string) {
  const sdk = await loadMetaSDK(appId, graphVersion);
  return new Promise<{ code: string; wabaId: string; phoneNumberId: string }>((resolve, reject) => {
    let code: string | undefined, assets: { wabaId: string; phoneNumberId: string } | undefined;
    const cleanup = () => { clearTimeout(timer); window.removeEventListener('message', listen); };
    const fail = (message: string) => { cleanup(); reject(new Error(message)); };
    const complete = () => { if (code && assets) { cleanup(); resolve({ code, ...assets }); } };
    const listen = (event: MessageEvent) => {
      // Comparação exacta: nunca endsWith('facebook.com') (aceitaria evilfacebook.com).
      if (!['https://www.facebook.com', 'https://web.facebook.com'].includes(event.origin)) return;
      let value;
      try { value = typeof event.data === 'string' ? JSON.parse(event.data) : event.data; } catch { return; }
      if (!value || value.type !== 'WA_EMBEDDED_SIGNUP') return;
      if (value.event === 'CANCEL') { fail('Ligação cancelada. Pode tentar novamente.'); return; }
      if (value.event === 'ERROR') { fail('A Meta não concluiu a ligação. Tente novamente ou contacte a equipa.'); return; }
      if (['FINISH', 'FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING'].includes(value.event)
          && /^\d+$/.test(value.data?.waba_id) && /^\d+$/.test(value.data?.phone_number_id)) {
        assets = { wabaId: value.data.waba_id, phoneNumberId: value.data.phone_number_id }; complete();
      }
    };
    const timer = setTimeout(() => fail('A ligação demorou mais que o esperado. Pode tentar novamente.'), 120000);
    window.addEventListener('message', listen);
    sdk.login(response => {
      if (!response.authResponse?.code) { fail('Não foi possível autorizar o WhatsApp. Tente novamente.'); return; }
      code = response.authResponse.code; complete();
    }, { config_id: configId, response_type: 'code', override_default_response_type: true, extras: { setup: {} } });
  });
}
