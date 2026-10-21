import hashlib
import hmac
import json
import os
import tempfile

os.environ.update(DEMO_MODE='true', ADMIN_KEY='test-admin', DB_PATH=tempfile.mktemp(suffix='.db'))
from fastapi.testclient import TestClient
import bot

client = TestClient(bot.app)
AUTH = {'Authorization': 'Bearer test-admin'}


def setup_function():
    with bot.lock:
        for table in ('msgs', 'bookings', 'paused', 'seen', 'inbox'):
            bot.db.execute(f'DELETE FROM {table}')
        bot.db.commit()


def test_health_and_panel():
    assert client.get('/health').json()['mode'] == 'demo'
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').status_code == 200


def test_auth_required():
    assert client.get('/api/dashboard').status_code == 401
    assert client.get('/api/dashboard?key=test-admin').status_code == 401
    assert client.get('/api/dashboard', headers=AUTH).status_code == 200


def test_demo_and_handoff():
    assert client.post('/api/demo/message', headers=AUTH, json={'text': 'Qual é o horário?'}).status_code == 200
    d = client.get('/api/dashboard', headers=AUTH).json()
    assert d['stats']['messages'] == 2
    assert '08h' in d['conversations'][0]['messages'][-1]['text']
    client.post('/api/demo/message', headers=AUTH, json={'text': 'Quero um humano'})
    assert client.get('/api/dashboard', headers=AUTH).json()['stats']['paused'] == 1
    client.post('/api/demo/message', headers=AUTH, json={'text': 'Olá'})
    assert client.get('/api/dashboard', headers=AUTH).json()['stats']['messages'] == 5
    assert client.post('/api/conversations/244900000001/pause', headers=AUTH, json={'paused': False}).status_code == 200


def test_validation():
    assert client.post('/api/demo/message', headers=AUTH, json={'text': ''}).status_code == 422
    assert client.post('/api/demo/message', headers=AUTH, json={'text': 'x'*2001}).status_code == 422


def test_verification(monkeypatch):
    monkeypatch.setattr(bot, 'VERIFY_TOKEN', 'verify')
    assert client.get('/webhook?hub.mode=subscribe&hub.verify_token=verify&hub.challenge=123').text == '123'
    assert client.get('/webhook?hub.verify_token=verify').status_code == 403


def signed(body):
    return {'x-hub-signature-256': 'sha256='+hmac.new(b'secret', body, hashlib.sha256).hexdigest()}


def test_signature_and_duplicate(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'secret')
    calls = []
    monkeypatch.setattr(bot, 'responder', lambda *args: calls.append(args))
    body = json.dumps({'entry':[{'changes':[{'value':{'messages':[{'id':'m1','from':'244900000001','type':'text','text':{'body':'Olá'}}]}}]}]}).encode()
    assert client.post('/webhook', content=body).status_code == 403
    for _ in range(2):
        assert client.post('/webhook', content=body, headers=signed(body)).status_code == 200
    assert len(calls) == 1
    assert client.post('/webhook', content=b'[]', headers=signed(b'[]')).status_code == 400


def test_failed_message_can_retry(monkeypatch):
    with bot.lock:
        bot.db.execute("INSERT INTO inbox(id,payload) VALUES(?,?)", ('retry1', json.dumps({'from':'244900000001','type':'text','text':{'body':'Olá'}})))
        bot.db.commit()
    def fail(*args):
        raise RuntimeError('test')
    monkeypatch.setattr(bot, 'responder', fail)
    bot.processar_pendentes()
    assert bot.db.execute("SELECT status FROM inbox").fetchone()[0] == 'failed'
    monkeypatch.setattr(bot, 'responder', lambda *args: None)
    bot.processar_pendentes()
    assert bot.db.execute("SELECT status FROM inbox").fetchone()[0] == 'done'


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(bot, 'LIMITE_HORA', 1)
    bot.responder('244900000001', 'Olá')
    bot.responder('244900000001', 'Olá novamente')
    assert len(bot.historico('244900000001')) == 3
