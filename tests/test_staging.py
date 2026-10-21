import hashlib
import hmac
import json
import os
import time
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

import bot

AUTH={'Authorization':'Bearer test-admin'}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(bot,'DEMO',True)
    monkeypatch.setattr(bot,'ADMIN_KEY','test-admin')
    monkeypatch.setattr(bot,'OWNER_PHONE','')
    with bot.db:
        for table in inspect(bot.db.engine).get_table_names():
            bot.db.execute(f'DELETE FROM {table}')


def message(mid='staging-1'):
    return {'id':mid,'from':'244900000001','type':'text','text':{'body':'Olá'}}


@pytest.mark.parametrize('missing',['DATABASE_URL','MESSAGE_ENCRYPTION_KEYS','ADMIN_KEY','APP_SECRET','VERIFY_TOKEN','WA_TOKEN','WA_PHONE_ID','ANTHROPIC_API_KEY','MODEL'])
def test_s1_required_configuration(missing):
    from settings import validate_startup
    config={key:'synthetic' for key in ('DATABASE_URL','MESSAGE_ENCRYPTION_KEYS','APP_SECRET','VERIFY_TOKEN','WA_TOKEN','WA_PHONE_ID','ANTHROPIC_API_KEY')}
    config.update(ADMIN_KEY='x'*32,MODEL=bot.MODEL,MESSAGE_ENCRYPTION_KEYS=os.environ['MESSAGE_ENCRYPTION_KEYS'],DATABASE_URL='postgresql://unused/synthetic')
    config[missing]=''
    with pytest.raises(ValueError,match=missing):
        validate_startup(False,config)


def test_s1_sqlite_explicit_only():
    from settings import validate_startup
    config={key:'synthetic' for key in ('APP_SECRET','VERIFY_TOKEN','WA_TOKEN','WA_PHONE_ID','ANTHROPIC_API_KEY')}
    config.update(ADMIN_KEY='x'*32,MODEL=bot.MODEL,MESSAGE_ENCRYPTION_KEYS=os.environ['MESSAGE_ENCRYPTION_KEYS'],ALLOW_SQLITE='true')
    validate_startup(False,config)
    config['ALLOW_SQLITE']='false'
    with pytest.raises(ValueError,match='DATABASE_URL'):
        validate_startup(False,config)


def test_s2_heartbeat_health_and_queue_age():
    client=TestClient(bot.app)
    assert client.get('/health').json()['worker_alive'] is False
    bot.worker_health.beat('synthetic-worker')
    bot.queue.enqueue([message()])
    bot.db.execute('UPDATE jobs SET created_at=?',(time.time()-301,))
    result=client.get('/health').json()
    assert result['worker_alive'] is True
    assert result['oldest_pending_age_seconds']>=300
    data=client.get('/api/dashboard',headers=AUTH).json()
    assert data['worker_alive'] is True
    assert data['operations_alert'] is True
    bot.db.execute('UPDATE worker_heartbeats SET last_seen=?',(time.time()-61,))
    assert client.get('/health').json()['worker_alive'] is False


def test_s3_login_valid_never_blocked():
    client=TestClient(bot.app)
    for _ in range(5):
        assert client.get('/api/dashboard',headers={'Authorization':'Bearer wrong'}).status_code==401
    assert client.get('/api/dashboard',headers={'Authorization':'Bearer wrong'}).status_code==429
    assert client.get('/api/dashboard',headers=AUTH).status_code==200


def test_s3_valid_webhooks_not_rate_limited(monkeypatch):
    monkeypatch.setattr(bot,'DEMO',False)
    monkeypatch.setattr(bot,'APP_SECRET','synthetic')
    monkeypatch.setenv('WEBHOOK_RATE_PER_MINUTE','2')
    client=TestClient(bot.app)
    for _ in range(3):
        client.post('/webhook',content=b'{}')
    raw=json.dumps({'entry':[{'changes':[{'value':{'messages':[message()]}}]}]}).encode()
    signature='sha256='+hmac.new(b'synthetic',raw,hashlib.sha256).hexdigest()
    for _ in range(3):
        assert client.post('/webhook',content=raw,headers={'x-hub-signature-256':signature}).status_code==200


def test_s4_no_owner_no_notification():
    bot.responder('244900000001','Quero um humano')
    assert bot.db.execute('SELECT count(*) FROM notifications').fetchone()[0]==0


def test_s4_ack_and_resume_clear_needs_human(monkeypatch):
    monkeypatch.setattr(bot,'OWNER_PHONE','244900000099')
    monkeypatch.setattr(bot,'enviar',lambda *args:'synthetic')
    bot.responder('244900000001','Quero um humano')
    bot.db.execute("UPDATE notifications SET status='failed'")
    client=TestClient(bot.app)
    mid=bot.db.execute('SELECT id FROM notifications').fetchone()[0]
    assert client.post(f'/api/notifications/{mid}/ack',headers=AUTH).status_code==200
    assert client.get('/api/dashboard',headers=AUTH).json()['stats']['notifications_failed']==0
    assert client.post('/api/conversations/244900000001/pause',json={'paused':False},headers=AUTH).status_code==200
    assert client.get('/api/dashboard',headers=AUTH).json()['conversations'][0]['needs_human'] is False


@pytest.mark.parametrize('error,release',[(httpx.ConnectError('synthetic'),True),(httpx.ReadTimeout('synthetic'),False),(401,True),(429,True)])
def test_s5_budget_rejection_release(error,release):
    from budget import Budget
    budget=Budget(bot.db,lambda _:None,limit_micro=100)
    def operation():
        if isinstance(error,int):
            response=httpx.Response(error,request=httpx.Request('POST','https://synthetic.invalid'))
            raise httpx.HTTPStatusError('synthetic',request=response.request,response=response)
        raise error
    with pytest.raises(httpx.HTTPStatusError if isinstance(error,int) else type(error)):
        budget.call(50,operation)
    assert budget.status()['spent_micro_usd']==(0 if release else 50)


def test_s6_failed_receipt_alert(monkeypatch):
    monkeypatch.setattr(bot,'DEMO',False)
    monkeypatch.setattr(bot,'APP_SECRET','synthetic')
    bot.queue.enqueue([message()])
    raw=json.dumps({'entry':[{'changes':[{'value':{'statuses':[{'id':'out','recipient_id':'244900000001','status':'failed','biz_opaque_callback_data':'job:staging-1','errors':[{'code':131026,'message':'Do not persist provider text'}]}]}}]}]}).encode()
    signature='sha256='+hmac.new(b'synthetic',raw,hashlib.sha256).hexdigest()
    client=TestClient(bot.app)
    assert client.post('/webhook',content=raw,headers={'x-hub-signature-256':signature}).status_code==200
    data=client.get('/api/dashboard',headers=AUTH).json()
    assert any(alert['code']=='meta_delivery_failed' for alert in data['alerts'])


def test_s7_adaptive_schedule():
    from worker import Schedule
    schedule=Schedule()
    assert schedule.delay(True)==1
    assert 10<=schedule.delay(False)<=15
    assert schedule.maintenance_due(1000)
    assert not schedule.maintenance_due(1001)
    assert schedule.maintenance_due(1181)


def test_s8_readme_deployment_plan():
    from pathlib import Path
    text=Path('README.md').read_text()
    assert '## Piloto em 60 minutos' in text
    assert 'DIRECT_URL' not in text
    assert 'forwarded-allow-ips' in text


def test_s9_complete_flow_all_protected_columns(monkeypatch):
    from privacy import PROTECTED
    from reconcile import review
    monkeypatch.setattr(bot,'OWNER_PHONE','244900000099')
    monkeypatch.setattr(bot,'enviar',lambda *args:'synthetic')
    client=TestClient(bot.app)
    client.put('/api/business',headers=AUTH,json={'nome':'Loja Sintética','informacoes':{'horario':'08h–17h'},'operacoes':{'encomendas':True}})
    for tag,data in [('[SOLICITACAO]',{'tipo':'encomenda','nome':'Ana','descricao':'Camisa','preferencia':''}),('[AGENDAMENTO]',{'nome':'Ana','servico':'Corte','data_hora':'Amanhã'})]:
        monkeypatch.setattr(bot,'resposta_demo',lambda _,t=tag,d=data:'A equipa confirmará. '+t+json.dumps(d))
        bot.responder('244900000001','Confirmo')
    bot.queue.enqueue([message('review')])
    job=bot.queue.claim()
    bot.queue.save_reply(job,{'reply':'Resposta sintética','raw':''})
    bot.queue.before_send(job)
    bot.queue.fail(job,'unknown',uncertain=True)
    review(bot,'review','sent','operador sintético','Verificação sintética de envio','synthetic-out')
    for table,fields in PROTECTED.items():
        with bot.db.engine.connect() as conn:
            rows=conn.exec_driver_sql(f'SELECT {",".join(fields)} FROM {table}').fetchall()
        assert rows, f'Fluxo não cobriu {table}'
        for row in rows:
            assert all(value is None or value.startswith('enc:v1:') for value in row),table


@pytest.mark.parametrize('trusted,ip',[(True,'198.51.100.10'),(False,'testclient')])
def test_s3_proxy_ip_only_when_trusted(trusted,ip):
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    app=ProxyHeadersMiddleware(bot.app,trusted_hosts=['testclient'] if trusted else ['127.0.0.1'])
    client=TestClient(app)
    assert client.get('/api/dashboard',headers={'Authorization':'Bearer wrong','x-forwarded-for':'198.51.100.10'}).status_code==401
    assert bot.db.execute('SELECT 1 FROM rate_limits WHERE id=?',(bot.gate.key('login',ip),)).fetchone()


@pytest.mark.parametrize('missing',['DATABASE_URL','MESSAGE_ENCRYPTION_KEYS','ADMIN_KEY','APP_SECRET','VERIFY_TOKEN','WA_TOKEN','WA_PHONE_ID','ANTHROPIC_API_KEY','MODEL'])
def test_s1_actual_import_stops_before_database(missing,tmp_path):
    import subprocess
    import sys
    env=dict(os.environ,DEMO_MODE='false',ALLOW_SQLITE='false',DATABASE_URL='postgresql://unused/synthetic',ADMIN_KEY='x'*32,MODEL=bot.MODEL)
    for key in ('APP_SECRET','VERIFY_TOKEN','WA_TOKEN','WA_PHONE_ID','ANTHROPIC_API_KEY'):
        env[key]='synthetic-only'
    env[missing]=''
    script="import database\ndef denied(*a,**k):\n raise RuntimeError('Base de dados não deve abrir')\ndatabase.Database.__init__=denied\nimport bot"
    result=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode!=0
    assert 'Configuração de arranque inválida' in result.stderr
    assert missing in result.stderr
    assert 'Base de dados não deve abrir' not in result.stderr


def test_s4_resume_also_acknowledges_unhandled_failed(monkeypatch):
    monkeypatch.setattr(bot,'OWNER_PHONE','244900000099')
    monkeypatch.setattr(bot,'enviar',lambda *args:'synthetic')
    bot.responder('244900000001','Quero humano')
    bot.db.execute("UPDATE notifications SET status='failed'")
    client=TestClient(bot.app)
    assert client.post('/api/conversations/244900000001/pause',json={'paused':False},headers=AUTH).status_code==200
    data=client.get('/api/dashboard',headers=AUTH).json()
    assert data['stats']['notifications_failed']==0
    assert not data['conversations'][0]['needs_human']
    mid=data['notifications'][0]['id']
    assert client.post(f'/api/notifications/{mid}/ack',headers=AUTH).status_code==200
    assert client.post(f'/api/notifications/{mid}/ack').status_code==401


def test_s6_failed_receipt_does_not_finalize_or_retry():
    bot.queue.enqueue([message()])
    job=bot.queue.claim()
    bot.queue.save_reply(job,{'reply':'Teste'})
    bot.queue.before_send(job)
    statuses=[{'id':'out','recipient_id':job['phone'],'status':'failed','biz_opaque_callback_data':'job:staging-1'}]
    bot.queue.receipts(statuses)
    bot.record_delivery_failures(statuses)
    assert bot.queue.reconcile(lambda _:pytest.fail('failed não é entrega'))==0
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0]=='sending'
    assert bot.db.execute('SELECT 1 FROM paused WHERE phone=?',(job['phone'],)).fetchone()


def test_s2_panel_healthy_state_is_explicit_and_not_red():
    import subprocess
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const nodes={};const node=()=>({hidden:false,textContent:'',value:'',childNodes:[],append(...items){this.childNodes.push(...items);},replaceChildren(){this.childNodes=[];},classList:{toggle(){}}});
const document={getElementById(id){return nodes[id]||(nodes[id]=node());},querySelectorAll(){return [];},createElement:node};
const context=vm.createContext({document,sessionStorage:{getItem(){return '';},removeItem(){}},console});
vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
vm.runInContext("data={worker_alive:true,worker_heartbeat_age_seconds:2,oldest_pending_age_seconds:null,demo:false,profile_ready:true,alerts:[],stats:{notifications_failed:0},notifications:[],ai_budget:{day:'synthetic',spent_micro_usd:0,limit_micro_usd:1000000}};renderSafety();",context);
assert.ok((nodes['worker-status']?.textContent||'').includes('Worker activo'));
assert.equal(nodes['safety-alerts'].hidden,true);
"""
    result=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr


def test_s1_whitespace_admin_key_is_not_a_secret():
    from security import validate_admin
    with pytest.raises(ValueError,match='ADMIN_KEY'):
        validate_admin(False,' '*32)
