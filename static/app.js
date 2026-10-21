'use strict';
const $ = id => document.getElementById(id);
let conversationPage=1, requestPage=1;
let token = sessionStorage.getItem('kiazop-key') || '', data, selected, tab = 'overview';
const names = {overview:['Visão geral','O seu negócio, em perspectiva.'], conversations:['Conversas','Cada conversa merece atenção.'], bookings:['Solicitações','Pedidos, reservas e novas oportunidades.'], simulator:['Laboratório','Um espaço para experimentar.'], settings:['O meu negócio','Um assistente à medida do seu negócio.']};
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
function metricIcon(name){
 const paths={clients:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',messages:'M21 11a8 8 0 0 1-8 8H8l-5 3 1-6a8 8 0 0 1-1-5 9 9 0 0 1 18 0M8 10h8M8 14h5',requests:'M8 3h8M9 3v3h6V3M7 4H5v17h14V4h-2M8 11h8M8 15h8',paused:'M7 21v-3a5 5 0 0 1 10 0v3M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0'};
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('fill','none');svg.setAttribute('stroke','currentColor');svg.setAttribute('stroke-width','1.5');svg.setAttribute('aria-hidden','true');const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',paths[name]);path.setAttribute('stroke-linecap','round');path.setAttribute('stroke-linejoin','round');svg.append(path);return svg;
}
async function api(path, options={}) {
 const res = await fetch(path, {...options, headers:{'Authorization':`Bearer ${token}`, 'Content-Type':'application/json', ...options.headers}});
 if(res.status===401){ sessionStorage.removeItem('kiazop-key'); showLogin(); throw Error('Chave de administração inválida.'); }
 if(!res.ok) throw Error('Não foi possível concluir a operação. Tente novamente.');
 return res.json();
}
function showLogin(){ $('login').hidden=false; $('workspace').hidden=true; }
function switchTab(name){ tab=name; document.querySelectorAll('.tab').forEach(n=>n.hidden=n.id!==name); document.querySelectorAll('nav button').forEach(n=>n.classList.toggle('active',n.dataset.tab===name)); $('breadcrumb').textContent=names[name][0]; $('title').textContent=names[name][1]; if(name==='settings')loadTemplates().catch(e=>$('business-feedback').textContent=e.message); }
document.querySelectorAll('[data-tab]').forEach(n=>n.addEventListener('click',()=>switchTab(n.dataset.tab)));
$('open-simulator').onclick=()=>switchTab('simulator');
$('logout').onclick=()=>{businessDirty=false;token='';sessionStorage.removeItem('kiazop-key');data=null;showLogin();};
$('login-form').onsubmit=async e=>{e.preventDefault();token=$('key').value; $('login-error').textContent='';try{await refresh();sessionStorage.setItem('kiazop-key',token);$('key').value='';}catch(err){$('login-error').textContent=err.message;}};
$('refresh').onclick=()=>refresh().catch(err=>$('notice').textContent=err.message);
function badge(paused){return el('span',paused?'Com a equipa':'Assistente ativo','badge'+(paused?' human':''));}
function renderChat(container, messages){container.replaceChildren(); if(!messages.length){container.append(el('div','Nenhuma mensagem ainda.','empty'));return;} messages.forEach(m=>{const b=el('div',m.text,'bubble '+m.role);b.append(el('small',`${m.role==='user'?'Cliente':'Assistente'} · ${m.ts} UTC`));container.append(b);});container.scrollTop=container.scrollHeight;}
async function refresh(){
 $('refresh').disabled=true;
 try{data=await api(`/api/dashboard?page=${conversationPage}&request_page=${requestPage}&page_size=25`);$('login').hidden=true;$('workspace').hidden=false;
 $('business').replaceChildren(document.createTextNode(data.business.nome),el('small',data.business.setor || 'Central de atendimento'));
 $('business-initials').textContent=data.business.nome.split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();
 $('mode').textContent=data.demo?'● Ambiente de demonstração':'● Modo produção';
 $('notice').textContent=data.demo?'Modo demonstração: dados deste ambiente, respostas locais e nenhum envio externo.':(data.stats.failed?`${data.stats.failed} mensagem(ns) com falha. `:'');
 if(data.stats.failed){const b=el('button','Agendar falhas com rejeição conhecida','outline');b.onclick=async()=>{try{await api('/api/inbox/retry',{method:'POST'});$('notice').textContent='Reprocessamento solicitado. Atualize os dados dentro de instantes.';}catch(e){$('notice').textContent=e.message;}};$('notice').append(b);}
 renderSetup();renderSafety();
 $('metrics').replaceChildren();
 [['Clientes atendidos',data.stats.clients,'Clientes únicos neste ambiente','clients'],['Mensagens',data.stats.messages,'Mensagens guardadas no histórico','messages'],['Solicitações',data.stats.bookings+data.stats.requests,'Pedidos a confirmar pela equipa','requests'],['Com a equipa',data.stats.paused,'Conversas com o bot em pausa','paused']].forEach(([label,note,desc,icon])=>{const card=el('div',undefined,'metric');const l=el('div',label,'metric-label');const mark=el('span',undefined,'icon');mark.append(metricIcon(icon));l.append(mark);card.append(l,el('strong',String(note).padStart(2,'0')),el('small',desc));$('metrics').append(card);});
 $('recent').replaceChildren();data.conversations.slice(0,4).forEach(c=>{const row=el('div',undefined,'recent-row');const info=el('div');info.append(el('strong','+'+c.phone),el('p',c.messages.at(-1)?.text||''));row.append(el('span','CL','avatar'),info,badge(c.needs_human));$('recent').append(row);});if(!data.conversations.length)$('recent').append(el('div','Ainda não existem conversas neste ambiente. Inicie uma conversa no Laboratório para testar o atendimento.','empty'));
 $('booking-rows').replaceChildren();
 const kindLabels={agendamento:'Agendamento',reserva:'Reserva',encomenda:'Encomenda',orcamento:'Orçamento'};
 const requests=data.solicitations;
 requests.forEach(b=>{const tr=el('tr');[kindLabels[b.tipo]||b.tipo,b.nome,b.descricao,b.preferencia||'—','+'+b.phone,'A confirmar'].forEach(v=>tr.append(el('td',v)));$('booking-rows').append(tr);});
 if(!requests.length){const td=el('td','Sem solicitações por enquanto.');td.colSpan=6;const tr=el('tr');tr.append(td);$('booking-rows').append(tr);}
 if(!businessDirty)fillBusiness(data.business);
 if(!data.profile_ready){const b=el('button','Configurar o meu negócio','outline');b.onclick=()=>switchTab('settings');$('notice').append(document.createTextNode(' Configure os dados reais antes de atender clientes. '),b);}

 renderConversations();renderDemo();renderPagination();
 }finally{$('refresh').disabled=false;}
}
function renderPagination(){
 const setup=(id,meta,change)=>{let node=$(id);if(!node){node=el('div',undefined,'pagination');node.id=id;(id==='conversation-pager'?$('conversation-list').parentElement:$('booking-rows').closest('.panel')).append(node);}node.replaceChildren();const prev=el('button','Anterior'),next=el('button','Seguinte');prev.disabled=meta.page<=1;next.disabled=meta.page*meta.page_size>=meta.total;for(const [button,delta] of [[prev,-1],[next,1]])button.onclick=async()=>{button.disabled=true;try{await change(meta.page+delta);await refresh();}catch(error){$('notice').textContent=error.message;}finally{button.disabled=false;}};node.append(prev,el('span',`Página ${meta.page} · ${meta.total} registos`),next);};
 setup('conversation-pager',data.pagination.conversations,async p=>{conversationPage=p;selected=undefined;$('thread').replaceChildren(el('p','Seleccione uma conversa.'));});
 setup('request-pager',data.pagination.solicitations,async p=>{requestPage=p;});
}
function renderSetup(){
 const setup=$('setup-status');setup.replaceChildren();
 setup.append(el('h2','Preparação do atendimento'));
 setup.append(el('p','Login confirmado nesta sessão — os dados protegidos do painel foram carregados.'));
 setup.append(el('p',data.profile_ready?'Perfil guardado — confirme que os dados continuam correctos.':'Perfil por configurar — Guarde os dados reais do negócio: nome e horário, catálogo ou contacto.'));
 setup.append(el('p',data.worker_alive?'Worker activo — batimento recente recebido.':`Worker inactivo — ${data.demo?'o laboratório local pode ser usado sem worker; o processamento da fila requer um serviço separado sempre ligado.':'o processamento automático não está pronto; é necessário iniciar o worker num serviço separado sempre ligado.'}`));
 if(!data.profile_ready){const button=el('button','Preencher os dados do negócio','outline');button.type='button';button.onclick=()=>{switchTab('settings');$('cfg-name').focus();};setup.append(button);}
 if(!data.worker_alive)setup.append(el('p','O Vercel aloja o painel/API, não o worker. O responsável técnico deve configurar o serviço com a mesma base PostgreSQL e confirmar o batimento antes de atender clientes.'));
 if(data.demo)setup.append(el('p','Modo demo: isto não confirma envios reais para WhatsApp nem chamadas à IA.'));
}
function renderSafety(){
 const warning=$('safety-alerts');warning.replaceChildren();if(!data.worker_alive)warning.append(el('p','Alerta: worker sem batimento há mais de 60 segundos ou ainda não iniciado.'));if(data.oldest_pending_age_seconds>300)warning.append(el('p',`Alerta: mensagem por resolver há ${Math.floor(data.oldest_pending_age_seconds/60)} minutos.`));$('worker-status').textContent=`${data.worker_alive?'Worker activo':'Worker inactivo'} · Batimento: ${data.worker_heartbeat_age_seconds==null?'não recebido':data.worker_heartbeat_age_seconds+' s'} · Mais antiga por resolver: ${data.oldest_pending_age_seconds==null?'nenhuma':data.oldest_pending_age_seconds+' s'}`;
 $('budget-status').textContent='';if(data.ai_budget){const b=data.ai_budget;$('budget-status').textContent=`Orçamento IA estimado (${b.day}): $${(b.spent_micro_usd/1e6).toFixed(3)} / $${(b.limit_micro_usd/1e6).toFixed(2)}. Reservas ambíguas podem estar incluídas.`;if(b.spent_micro_usd>=b.limit_micro_usd*0.8)warning.append(el('p','Orçamento de IA reservado/usado igual ou superior a 80%.'));}
 if(!data.demo&&!data.profile_ready)warning.append(el('p','Atendimento automático bloqueado: guarde um nome real e horário, catálogo ou contacto em O meu negócio.'));
 for(const item of data.alerts||[])warning.append(el('p',item.detail));
 if(data.stats.notifications_failed)warning.append(el('p',`${data.stats.notifications_failed} notificação(ões) à equipa falharam. Verifique a lista e assuma os atendimentos pendentes.`));
 warning.hidden=!warning.childNodes.length;
 const items=data.notifications||[];$('notification-panel').hidden=!items.length;
 $('notification-summary').textContent=`Pendentes/em envio: ${data.stats.notifications_pending||0}. Falhadas: ${data.stats.notifications_failed||0}. Enviado significa aceite pelo fornecedor, não lido pela equipa.`;
 $('notification-list').replaceChildren();
 const labels={pending:'Pendente',sending:'Em envio',sent:'Enviada',failed:'Falhada'};
 const errors={approved_template_required:'É necessário configurar um template aprovado fora da janela de 24 horas.',owner_not_configured:'Contacto da equipa não configurado.',delivery_unknown:'Entrega desconhecida; verificar antes de repetir.',provider_failure_or_unknown:'Falha do fornecedor ou resultado desconhecido; verificar antes de repetir.'};
 for(const item of items){const li=el('li',`+${item.phone} — ${labels[item.status]||item.status}${item.error?' — '+(errors[item.error]||'Verifique a configuração e o fornecedor.'):''}`,item.status==='failed'&&!item.acknowledged_at?'needs-human':'');if(!item.acknowledged_at){const ack=el('button','Tratada');ack.onclick=async()=>{ack.disabled=true;try{await api(`/api/notifications/${encodeURIComponent(item.id)}/ack`,{method:'POST'});await refresh();}catch(e){$('notice').textContent=e.message;}finally{ack.disabled=false;}};li.append(ack);}else{li.append(el('span',' · Tratada'));}$('notification-list').append(li);}
}
function renderConversations(){
 $('conversation-list').replaceChildren();const filtered=data.conversations.filter(c=>c.phone.includes($('search').value.trim()));filtered.forEach(c=>{const b=el('button','+'+c.phone,'conversation-item'+(selected===c.phone?' selected':''));b.classList.toggle('needs-human',!!c.needs_human);b.append(el('small',c.needs_human?'Precisa de humano':'Assistente ativo'));b.onclick=()=>{selected=c.phone;renderConversations();};$('conversation-list').append(b);});if(!filtered.length)$('conversation-list').append(el('div','Nenhuma conversa encontrada.','empty'));
 const c=data.conversations.find(c=>c.phone===selected);if(!c)return;
 $('thread').replaceChildren();const heading=el('div',undefined,'panel-heading');heading.append(el('h3','+'+c.phone));if(c.needs_human)heading.append(el('span','Precisa de humano','badge needs-human'));const button=el('button',c.paused?'Reativar assistente':'Assumir conversa');button.onclick=async()=>{button.disabled=true;try{await api(`/api/conversations/${encodeURIComponent(c.phone)}/pause`,{method:'POST',body:JSON.stringify({paused:!c.paused})});await refresh();}catch(e){$('notice').textContent=e.message;}finally{button.disabled=false;}};heading.append(button);const chat=el('div',undefined,'chat');$('thread').append(heading,chat);renderChat(chat,c.messages);const pager=el('div',undefined,'pagination');$('thread').append(pager);let page=1;const load=async()=>{try{const result=await api(`/api/conversations/${encodeURIComponent(c.phone)}/messages?page=${page}`);if(selected!==c.phone)return;renderChat(chat,result.messages);pager.replaceChildren();const newer=el('button','Mais recentes'),older=el('button','Mais antigas');newer.disabled=page<=1;older.disabled=page*result.page_size>=result.total;newer.onclick=()=>{page--;load();};older.onclick=()=>{page++;load();};pager.append(newer,el('span',`Página ${page} · ${result.total} mensagens`),older);}catch(error){$('notice').textContent=error.message;}};load();
}
$('search').oninput=()=>data&&renderConversations();
function renderDemo(){const c=data.conversations.find(c=>c.phone==='244900000001');if(c)renderChat($('demo-chat'),c.messages);$('demo-form').hidden=!data.demo; if(!data.demo)$('demo-chat').replaceChildren(el('div','O laboratório está disponível apenas em DEMO_MODE. O atendimento real continua no WhatsApp.','empty'));if(c?.paused&&data.demo){const b=el('button','Reativar assistente de teste','outline');b.onclick=async()=>{try{await api('/api/conversations/244900000001/pause',{method:'POST',body:JSON.stringify({paused:false})});await refresh();}catch(e){$('notice').textContent=e.message;}};$('demo-chat').append(b);}}
$('demo-form').onsubmit=async e=>{e.preventDefault();const text=$('demo-text').value.trim();if(!text)return;const button=e.target.querySelector('button');button.disabled=true;try{await api('/api/demo/message',{method:'POST',body:JSON.stringify({text})});$('demo-text').value='';await refresh();}catch(err){$('notice').textContent=err.message;}finally{button.disabled=false;}};
$('suggestions').onclick=e=>{const button=e.target.closest('button');if(button){$('demo-text').value=button.dataset.prompt||button.textContent.replace('↗','').trim();$('demo-text').focus();}};
let businessDirty=false, sectorTemplates=[], templatesPromise;
const fields={name:'nome',sector:'setor',tone:'tom',extra:'extra'};
const infoFields={contact:'contacto',address:'morada',hours:'horario',payment:'pagamento',delivery:'entrega',policies:'politicas'};
const dictionaryFields={products:'produtos',services:'servicos',faq:'perguntas_frequentes'};
const operationFields=['agendamentos','reservas','encomendas','orcamentos'];
function fillBusiness(profile){
 Object.entries(fields).forEach(([id,key])=>$('cfg-'+id).value=profile[key]||'');
 Object.entries(infoFields).forEach(([id,key])=>$('cfg-'+id).value=profile.informacoes[key]||'');
 Object.entries(dictionaryFields).forEach(([id,key])=>$('cfg-'+id).value=Object.entries(profile.informacoes[key]||{}).map(([k,v])=>k+' | '+v.replace(/\n/g,' ')).join('\n'));
 operationFields.forEach(key=>$('cfg-'+key).checked=!!profile.operacoes[key]);
}
function parseDictionary(text){
 const result=Object.create(null);
 for(const line of text.split('\n').filter(l=>l.trim())){
  const sep=line.indexOf('|'); const key=line.slice(0,sep).trim(); const value=line.slice(sep+1).trim();
  if(sep<1||!key||!value)throw Error('Catálogo e perguntas frequentes: use uma linha por item no formato Nome | descrição.');
  if(Object.hasOwn(result,key))throw Error('Existe um item repetido: '+key);
  result[key]=value;
 }
 return result;
}
$('business-form').oninput=()=>{businessDirty=true;$('business-feedback').textContent='Alterações por guardar.';};
async function loadTemplates(){
 if(sectorTemplates.length)return;
 if(!templatesPromise){templatesPromise=api('/api/business/templates').then(items=>{
 sectorTemplates=items;
 sectorTemplates.forEach(t=>{const o=el('option',t.label);o.value=t.id;$('profile-template').append(o);});
 }).catch(error=>{templatesPromise=undefined;throw error;});}
 return templatesPromise;
}
$('profile-template').onfocus=()=>loadTemplates().catch(e=>$('business-feedback').textContent=e.message);
$('load-template').onclick=async()=>{
 try{await loadTemplates();const template=sectorTemplates.find(t=>t.id===$('profile-template').value);
 if(!template){$('business-feedback').textContent='Escolha um modelo de setor primeiro.';return;}
 if(!confirm('Aplicar o modelo limpa os campos do formulário, mas só altera o negócio depois de guardar. Continuar?'))return;
 fillBusiness(template.profile);businessDirty=true;$('business-feedback').textContent='Modelo aplicado. Preencha os dados reais e guarde.';
 }catch(e){$('business-feedback').textContent=e.message;}
};
$('business-form').onsubmit=async e=>{
 e.preventDefault();$('save-business').disabled=true;$('business-feedback').textContent='A guardar…';
 try{const profile={informacoes:{},operacoes:{}};
 Object.entries(fields).forEach(([id,key])=>profile[key]=$('cfg-'+id).value.trim());
 Object.entries(infoFields).forEach(([id,key])=>profile.informacoes[key]=$('cfg-'+id).value.trim());
 Object.entries(dictionaryFields).forEach(([id,key])=>profile.informacoes[key]=parseDictionary($('cfg-'+id).value));
 operationFields.forEach(key=>profile.operacoes[key]=$('cfg-'+key).checked);
 await api('/api/business',{method:'PUT',body:JSON.stringify(profile)});businessDirty=false;await refresh();$('business-feedback').textContent=data.profile_ready?'Negócio guardado. Perfil pronto para atendimento.':'Guardado, mas incompleto: preencha nome real e horário, catálogo ou contacto.';
 }catch(err){$('business-feedback').textContent=err.message;}finally{$('save-business').disabled=false;}
};
if(token)refresh().catch(e=>$('login-error').textContent=e.message);else showLogin();
