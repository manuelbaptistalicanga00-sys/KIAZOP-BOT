'use strict';
const $ = id => document.getElementById(id);
let token = sessionStorage.getItem('kiazop-key') || '', data, selected, tab = 'overview';
const names = {overview:['Visão geral','Uma visão clara do seu negócio.'], conversations:['Conversas','Cada conversa merece atenção.'], bookings:['Agendamentos','Organize os próximos encontros.'], simulator:['Laboratório','Um espaço para experimentar.']};
const el = (tag, text, cls) => { const node = document.createElement(tag); if(text !== undefined) node.textContent = text; if(cls) node.className = cls; return node; };
async function api(path, options={}) {
 const res = await fetch(path, {...options, headers:{'Authorization':`Bearer ${token}`, 'Content-Type':'application/json', ...options.headers}});
 if(res.status===401){ sessionStorage.removeItem('kiazop-key'); showLogin(); throw Error('Chave de administração inválida.'); }
 if(!res.ok) throw Error('Não foi possível concluir a operação. Tente novamente.');
 return res.json();
}
function showLogin(){ $('login').hidden=false; $('workspace').hidden=true; }
function switchTab(name){ tab=name; document.querySelectorAll('.tab').forEach(n=>n.hidden=n.id!==name); document.querySelectorAll('nav button').forEach(n=>n.classList.toggle('active',n.dataset.tab===name)); $('breadcrumb').textContent=names[name][0]; $('title').textContent=names[name][1]; }
document.querySelectorAll('[data-tab]').forEach(n=>n.addEventListener('click',()=>switchTab(n.dataset.tab)));
$('open-simulator').onclick=()=>switchTab('simulator');
$('logout').onclick=()=>{token='';sessionStorage.removeItem('kiazop-key');data=null;showLogin();};
$('login-form').onsubmit=async e=>{e.preventDefault();token=$('key').value; $('login-error').textContent='';try{await refresh();sessionStorage.setItem('kiazop-key',token);$('key').value='';}catch(err){$('login-error').textContent=err.message;}};
$('refresh').onclick=()=>refresh().catch(err=>$('notice').textContent=err.message);
function badge(paused){return el('span',paused?'Com a equipa':'Assistente ativo','badge'+(paused?' human':''));}
function renderChat(container, messages){container.replaceChildren(); if(!messages.length){container.append(el('div','Nenhuma mensagem ainda.','empty'));return;} messages.forEach(m=>{const b=el('div',m.text,'bubble '+m.role);b.append(el('small',`${m.role==='user'?'Cliente':'Assistente'} · ${m.ts} UTC`));container.append(b);});container.scrollTop=container.scrollHeight;}
async function refresh(){
 $('refresh').disabled=true;
 try{data=await api('/api/dashboard');$('login').hidden=true;$('workspace').hidden=false;
 $('business').replaceChildren(document.createTextNode(data.business.nome),el('small','Central de atendimento'));
 $('mode').textContent=data.demo?'● Demonstração local':'● Modo produção';
 $('notice').textContent=data.demo?'Modo demonstração: dados deste ambiente, respostas locais e nenhum envio externo.':(data.stats.failed?`${data.stats.failed} mensagem(ns) com falha. `:'');
 if(data.stats.failed){const b=el('button','Reprocessar falhas','outline');b.onclick=async()=>{try{await api('/api/inbox/retry',{method:'POST'});$('notice').textContent='Reprocessamento solicitado. Atualize os dados dentro de instantes.';}catch(e){$('notice').textContent=e.message;}};$('notice').append(b);}
 $('metrics').replaceChildren();
 [['Clientes atendidos',data.stats.clients,'Clientes únicos neste ambiente','♙'],['Mensagens',data.stats.messages,'Mensagens guardadas no histórico','☷'],['Marcações',data.stats.bookings,'Solicitações a confirmar pela equipa','▦'],['Com a equipa',data.stats.paused,'Conversas com o bot em pausa','♧']].forEach(([label,note,desc,icon])=>{const card=el('div',undefined,'metric');const l=el('div',label,'metric-label');l.append(el('span',icon,'icon'));card.append(l,el('strong',String(note).padStart(2,'0')),el('small',desc));$('metrics').append(card);});
 $('recent').replaceChildren();data.conversations.slice(0,4).forEach(c=>{const row=el('div',undefined,'recent-row');const info=el('div');info.append(el('strong','+'+c.phone),el('p',c.messages.at(-1)?.text||''));row.append(el('span','CL','avatar'),info,badge(c.paused));$('recent').append(row);});if(!data.conversations.length)$('recent').append(el('div','Ainda está tudo tranquilo por aqui. Experimente o laboratório para iniciar a primeira conversa.','empty'));
 $('booking-rows').replaceChildren();data.bookings.forEach(b=>{const tr=el('tr');[b.nome,b.servico,b.data_hora,'+'+b.phone,'A confirmar'].forEach(v=>tr.append(el('td',v)));$('booking-rows').append(tr);});if(!data.bookings.length){const td=el('td','Sem solicitações de marcação.');td.colSpan=5;const tr=el('tr');tr.append(td);$('booking-rows').append(tr);}
 renderConversations();renderDemo();
 }finally{$('refresh').disabled=false;}
}
function renderConversations(){
 $('conversation-list').replaceChildren();const filtered=data.conversations.filter(c=>c.phone.includes($('search').value.trim()));filtered.forEach(c=>{const b=el('button','+'+c.phone,'conversation-item'+(selected===c.phone?' selected':''));b.append(el('small',c.paused?'Atendimento humano':'Assistente ativo'));b.onclick=()=>{selected=c.phone;renderConversations();};$('conversation-list').append(b);});if(!filtered.length)$('conversation-list').append(el('div','Nenhuma conversa encontrada.','empty'));
 const c=data.conversations.find(c=>c.phone===selected);if(!c)return;
 $('thread').replaceChildren();const heading=el('div',undefined,'panel-heading');heading.append(el('h3','+'+c.phone));const button=el('button',c.paused?'Reativar assistente':'Assumir conversa');button.onclick=async()=>{button.disabled=true;try{await api(`/api/conversations/${encodeURIComponent(c.phone)}/pause`,{method:'POST',body:JSON.stringify({paused:!c.paused})});await refresh();}catch(e){$('notice').textContent=e.message;}finally{button.disabled=false;}};heading.append(button);const chat=el('div',undefined,'chat');$('thread').append(heading,chat);renderChat(chat,c.messages);
}
$('search').oninput=()=>data&&renderConversations();
function renderDemo(){const c=data.conversations.find(c=>c.phone==='244900000001');if(c)renderChat($('demo-chat'),c.messages);$('demo-form').hidden=!data.demo; if(!data.demo)$('demo-chat').replaceChildren(el('div','O laboratório está disponível apenas em DEMO_MODE. O atendimento real continua no WhatsApp.','empty'));if(c?.paused&&data.demo){const b=el('button','Reativar assistente de teste','outline');b.onclick=async()=>{try{await api('/api/conversations/244900000001/pause',{method:'POST',body:JSON.stringify({paused:false})});await refresh();}catch(e){$('notice').textContent=e.message;}};$('demo-chat').append(b);}}
$('demo-form').onsubmit=async e=>{e.preventDefault();const text=$('demo-text').value.trim();if(!text)return;const button=e.target.querySelector('button');button.disabled=true;try{await api('/api/demo/message',{method:'POST',body:JSON.stringify({text})});$('demo-text').value='';await refresh();}catch(err){$('notice').textContent=err.message;}finally{button.disabled=false;}};
document.querySelectorAll('#suggestions button').forEach(b=>b.onclick=()=>{$('demo-text').value=b.textContent;$('demo-text').focus();});
if(token)refresh().catch(e=>$('login-error').textContent=e.message);else showLogin();
