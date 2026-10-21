'use client';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { embeddedSignup } from './embedded-signup.js';
import { E164, StateSchema, TemplateSchema, type ConnectionState } from './contracts.js';
import './onboarding.css';

type Props = {
  // Host autenticado, por exemplo Next.js + Clerk. Isto NÃO cria autenticação por si só.
  account: { email: string } | null; renderSignIn: () => ReactNode;
  meta: { appId: string; configId: string; version: string }; supportPhone: string;
};
const drafts = {
  clinica: { name: 'Clínica', services: 'Consulta de avaliação — preço a confirmar', faq: 'Como marcar? Diga a sua preferência de dia e hora.' },
  salao: { name: 'Salão', services: 'Corte e penteado — preço a confirmar', faq: 'Posso marcar? Vamos recolher o serviço e a sua preferência.' },
  imobiliaria: { name: 'Imobiliária', services: 'Visita a imóvel — disponibilidade a confirmar', faq: 'Como visitar? Diga a zona e o tipo de imóvel que procura.' },
  restaurante: { name: 'Restaurante', services: 'Reserva de mesa — disponibilidade a confirmar', faq: 'Posso reservar? Diga o dia, hora e número de pessoas.' },
  loja: { name: 'Loja', services: 'Produtos do catálogo — confirmar stock e preços', faq: 'Como encomendar? Diga o produto, variante e quantidade.' },
  outro: { name: 'Outro negócio', services: 'Serviço principal — substitua pela informação real', faq: 'Como funciona? A equipa pode orientar o seu pedido.' },
};
async function api(path: string, body?: object) {
  const response = await fetch(`/api/onboarding/${path}`, {
    method: body ? 'POST' : 'GET', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}),
    signal: AbortSignal.timeout(25000),
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error('A sessão expirou. Entre novamente.');
    if (response.status === 429) throw new Error('Muitas tentativas. Aguarde um minuto.');
    throw new Error('Não conseguimos concluir. Tente novamente ou peça ajuda.');
  }
  return response.json();
}
export function OnboardingWizard({ account, renderSignIn, meta, supportPhone }: Props) {
  const [step, setStep] = useState(1), [elapsed, setElapsed] = useState(0);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [pollError, setPollError] = useState('');
  const [state, setState] = useState<ConnectionState>({ status: 'disconnected', provider: null, templateReady: false, firstAIReplyDelivered: false });
  const [risk, setRisk] = useState(false), [consent, setConsent] = useState(false), [confirmed, setConfirmed] = useState(false);
  const [sector, setSector] = useState<keyof typeof drafts>('loja');
  const [name, setName] = useState(''), [hours, setHours] = useState('Seg–Sex 09h–18h (exemplo: substitua)'),
    [services, setServices] = useState(drafts.loja.services), [phone, setPhone] = useState('');
  const inFlight = useRef(false);
  const retryAction = useRef<(() => Promise<void>) | null>(null);
  useEffect(() => { const start = Date.now(); const t = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000); return () => clearInterval(t); }, []);
  const refresh = useCallback(async () => { const result = StateSchema.parse(await api('state')); setState(result); setPollError(''); }, []);
  useEffect(() => {
    if (!account) return;
    let active = true, timer: ReturnType<typeof setTimeout>;
    let failures = 0;
    const poll = async () => {
      try { if (!document.hidden) { await refresh(); failures = 0; } }
      catch { failures++; if (active) setPollError('A ligação está lenta. Estamos a tentar novamente.'); }
      if (active) timer = setTimeout(poll, Math.min(30000, 2000 * 2 ** Math.min(failures, 4)));
    };
    void poll(); return () => { active = false; clearTimeout(timer); };
  }, [account, refresh]);
  async function run(action: () => Promise<void>) {
    if (inFlight.current) return;
    retryAction.current = action;
    inFlight.current = true; setBusy(true); setError('');
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : 'Tente novamente.'); }
    finally { inFlight.current = false; setBusy(false); }
  }
  const connected = state.status === 'connected';
  const templateValid = TemplateSchema.safeParse({ sector, businessName: name, hours, services, factsConfirmed: confirmed }).success;
  const help = /^\+?\d{7,15}$/.test(supportPhone) ? `https://wa.me/${supportPhone.replace('+','')}?text=${encodeURIComponent('Preciso de ajuda a ligar o BOT OPTIMIZATION. Não vou enviar credenciais.')}` : undefined;
  return <main className="bo-onboarding">
    <header><strong>BOT OPTIMIZATION</strong><span>{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')} decorridos</span></header>
    <progress max={4} value={step} aria-label={`Passo ${step} de 4`} />
    <p className="bo-muted">Passo {step} de 4 · Objectivo: primeira resposta em menos de 5 minutos, para contas elegíveis.</p>
    {step === 1 && <section><h1>Comece pela sua conta.</h1><p>Entre com Google ou e-mail. Sem formulário longo.</p>
      {account ? <p>Sessão verificada: {account.email}</p> : renderSignIn()}
      <button disabled={!account || busy} onClick={() => setStep(2)}>Continuar</button></section>}
    {step === 2 && <section><h1>Ligue o seu WhatsApp.</h1><p>API oficial para produção. QR apenas para testes conscientes do risco.</p>
      <button disabled={busy || connected} onClick={() => void run(async () => {
        const attempt = await api('meta/start', {});
        const result = await embeddedSignup(meta.appId, meta.configId, meta.version);
        await api('meta/finish', { ...result, attemptId: attempt.attemptId, nonce: attempt.nonce }); await refresh();
      })}>Ligar WhatsApp oficial</button>
      <details><summary>Atalho QR — experimental, sem SLA</summary><p role="note">Pode infringir os termos do WhatsApp e causar bloqueio do número. Não use o número principal nem dados de clientes.</p>
        <label><input type="checkbox" checked={risk} onChange={e => setRisk(e.target.checked)} />Compreendo e aceito o risco apenas para testes.</label>
        <button disabled={!risk || busy || connected} onClick={() => void run(async () => { await api('qr/start', { riskAccepted: true }); await refresh(); })}>Gerar QR de teste</button>
        {state.qrDataUrl && <img width={230} height={230} src={state.qrDataUrl} alt="QR temporário para ligação de teste" />}
      </details>
      <p aria-live="polite">{connected ? 'WhatsApp ligado.' : state.publicMessage || 'A aguardar ligação.'}</p>
      <button disabled={!connected || busy} onClick={() => setStep(3)}>Continuar</button></section>}
    {step === 3 && <section><h1>Escolha o sector e confirme os dados.</h1><p>Rascunho de exemplo. Nunca publicamos horários ou serviços sem a sua confirmação.</p>
      <label>Sector<select value={sector} onChange={e => { const s = e.target.value as keyof typeof drafts; setSector(s); setServices(drafts[s].services); setConfirmed(false); }}>
        {Object.entries(drafts).map(([key, value]) => <option key={key} value={key}>{value.name}</option>)}</select></label>
      <label>Nome real<input value={name} maxLength={160} onChange={e => { setName(e.target.value); setConfirmed(false); }} /></label>
      <label>Horário real<input value={hours} maxLength={500} onChange={e => { setHours(e.target.value); setConfirmed(false); }} /></label>
      <label>Serviços ou produtos<textarea value={services} maxLength={2400} onChange={e => { setServices(e.target.value); setConfirmed(false); }} /></label>
      <p>Resposta inicial sugerida: {drafts[sector].faq}</p>
      <label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />Confirmei os dados reais e autorizo a utilização deste perfil.</label>
      <button disabled={busy || !templateValid} onClick={() => void run(async () => {
        await api('template', { sector, businessName: name, hours, services, factsConfirmed: confirmed }); await refresh(); setStep(4);
      })}>Guardar e testar</button></section>}
    {step === 4 && <section><h1>Receba a primeira resposta.</h1><p>Use um telemóvel de teste diferente do número empresarial ligado.</p>
      <label>Telemóvel com indicativo<input type="tel" placeholder="+244…" value={phone} onChange={e => setPhone(e.target.value)} /></label>
      <label><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} />Autorizo uma mensagem de teste para este número.</label>
      <button disabled={busy || !consent || !E164.safeParse(phone).success || !connected || !state.templateReady} onClick={() => void run(async () => { await api('test', { phone, consent: true }); await refresh(); })}>Enviar teste autorizado</button>
      <p>Fora de uma janela válida, o envio exige um template aprovado. Se não estiver disponível, inicie a conversa abaixo e receba a resposta automática.</p>
      {state.inboundTestUrl && <a href={state.inboundTestUrl} target="_blank" rel="noreferrer">Abrir conversa de teste no WhatsApp</a>}
      <p aria-live="polite">{state.firstAIReplyDelivered ? 'Resposta da IA entregue, confirmada pelo fornecedor.' : 'A aguardar primeira resposta confirmada.'}</p>
      <button disabled={!state.firstAIReplyDelivered || busy} onClick={() => void run(async () => { await api('complete', {}); window.location.assign('/app'); })}>Está a funcionar → abrir painel</button></section>}
    {(error || pollError) && <div role="alert"><p>{error || pollError}</p><button disabled={busy} onClick={() => void run(error && retryAction.current ? retryAction.current : refresh)}>Tentar de novo</button></div>}
    {step > 1 && <button className="bo-secondary" disabled={busy} onClick={() => setStep(s => s - 1)}>Voltar</button>}
    <footer>{help ? <a href={help} target="_blank" rel="noreferrer">Preciso de ajuda por WhatsApp</a> : 'A equipa deve configurar o número de suporte.'}<p>Aprovações externas podem demorar mais do que o tempo indicado.</p></footer>
  </main>;
}
