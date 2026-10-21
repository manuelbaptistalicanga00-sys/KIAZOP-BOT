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
        for table in ('msgs', 'bookings', 'paused', 'seen', 'inbox', 'business_config', 'requests', 'jobs', 'conversation_leases', 'ingested', 'delivery_receipts', 'notifications', 'alerts', 'handoff_reasons', 'reconciliation_log'):
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
    assert 'não configurado' in d['conversations'][0]['messages'][-1]['text']
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
    assert calls == []  # ACK durável, sem executar IA no processo HTTP
    assert bot.db.execute("SELECT count(*) FROM jobs WHERE id='m1'").fetchone()[0] == 1
    assert client.post('/webhook', content=b'[]', headers=signed(b'[]')).status_code == 400


def test_failed_message_can_retry(monkeypatch):
    import httpx
    bot.queue.enqueue([{'id': 'retry1', 'from': '244900000001', 'type': 'text', 'text': {'body': 'Olá'}}])

    def reject(*args):
        response = httpx.Response(429, request=httpx.Request('POST', 'https://example.invalid'))
        raise httpx.HTTPStatusError('synthetic rejection', request=response.request, response=response)

    monkeypatch.setattr(bot, 'enviar', reject)
    bot.processar_pendentes()
    assert bot.db.execute("SELECT status FROM inbox").fetchone()[0] == 'failed'
    assert client.post('/api/inbox/retry', headers=AUTH).status_code == 200
    # API só agenda. Worker faz a tentativa e reutiliza resposta já preparada.
    assert bot.db.execute("SELECT state FROM jobs").fetchone()[0] == 'pending'
    monkeypatch.setattr(bot, 'enviar', lambda *args: 'synthetic-id')
    bot.processar_pendentes()
    assert bot.db.execute("SELECT status FROM inbox").fetchone()[0] == 'done'


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(bot, 'LIMITE_HORA', 1)
    bot.responder('244900000001', 'Olá')
    bot.responder('244900000001', 'Olá novamente')
    assert len(bot.historico('244900000001')) == 3


def profile(sector='Loja'):
    return {
        'nome': 'Comércio Esperança', 'setor': sector,
        'informacoes': {'horario': 'Segunda a sexta 08h–17h',
                        'produtos': {'Camisa': '5.000 Kz'},
                        'pagamento': 'Multicaixa', 'entrega': 'Levantamento na loja',
                        'perguntas_frequentes': {'Fazem trocas?': 'Até 7 dias com recibo.'}},
        'operacoes': {'agendamentos': False, 'reservas': False, 'encomendas': True, 'orcamentos': True},
    }


def test_business_requires_auth_and_validates():
    assert client.put('/api/business', json=profile()).status_code == 401
    assert client.get('/api/business/templates').status_code == 401
    invalid = profile()
    invalid['nome'] = '   '
    assert client.put('/api/business', headers=AUTH, json=invalid).status_code == 422
    invalid = profile()
    invalid['informacoes']['api_secret'] = 'not-allowed'
    assert client.put('/api/business', headers=AUTH, json=invalid).status_code == 422


def test_profile_persists_and_drives_answers():
    assert client.put('/api/business', headers=AUTH, json=profile()).status_code == 200
    saved = client.get('/api/dashboard', headers=AUTH).json()['business']
    assert saved['nome'] == 'Comércio Esperança'
    assert saved['setor'] == 'Loja'
    assert '5.000 Kz' in bot.resposta_demo('Quais produtos têm?')
    assert '08h' in bot.resposta_demo('Qual o horário?')
    assert 'Multicaixa' in bot.resposta_demo('Como posso pagar?')
    assert '7 dias' in bot.resposta_demo('Fazem trocas?')
    assert 'nome, produto/variante, quantidade' in bot.resposta_demo('Quero encomendar')
    assert 'Não recolhemos' in bot.resposta_demo('Quero agendar')
    assert 'Clínica Sorriso' not in bot.sistema()
    assert 'Comércio Esperança' in bot.sistema()


def test_templates_without_invented_business_facts():
    profiles = client.get('/api/business/templates', headers=AUTH).json()
    assert len(profiles) == 9
    for item in profiles:
        assert not item['profile']['informacoes']['produtos']
        assert not item['profile']['informacoes']['horario']
    restaurant = next(t['profile'] for t in profiles if t['id'] == 'restaurante')
    client.put('/api/business', headers=AUTH, json=restaurant)
    assert 'quantidade de pessoas' in bot.resposta_demo('Quero reservar')
    assert 'Não recolhemos' in bot.resposta_demo('Quero agendar')


def test_profile_save_resets_ai_context_without_deleting_history():
    bot.responder('244900000001', 'Olá')
    assert len(bot.historico('244900000001')) == 2
    client.put('/api/business', headers=AUTH, json=profile())
    assert bot.historico('244900000001') == []
    assert client.get('/api/dashboard', headers=AUTH).json()['stats']['messages'] == 2
    bot.responder('244900000001', 'Quais produtos têm?')
    assert len(bot.historico('244900000001')) == 2


def test_general_requests_registered_and_deduplicated(monkeypatch):
    client.put('/api/business', headers=AUTH, json=profile())
    text = 'A equipa confirmará a sua solicitação. [SOLICITACAO]' + json.dumps({
        'tipo': 'encomenda', 'nome': 'Ana', 'descricao': '2 camisas tamanho M', 'preferencia': 'Levantamento'})
    monkeypatch.setattr(bot, 'resposta_demo', lambda _: text)
    for _ in range(2):
        bot.responder('244900000001', 'Confirmo os detalhes')
    d = client.get('/api/dashboard', headers=AUTH).json()
    assert d['stats']['requests'] == 1
    assert d['requests'][0]['tipo'] == 'encomenda'
    assert '[SOLICITACAO]' not in d['conversations'][0]['messages'][-1]['text']


def test_disabled_and_invalid_requests_not_saved(monkeypatch):
    client.put('/api/business', headers=AUTH, json=profile())
    for request in [
        {'tipo': 'reserva', 'nome': 'Ana', 'descricao': 'Mesa', 'preferencia': 'Amanhã'},
        {'tipo': 'encomenda', 'nome': '', 'descricao': 'Camisa'},
        {'tipo': 'encomenda', 'nome': 'Ana', 'descricao': 'x' * 1201},
        {'tipo': ['encomenda'], 'nome': 'Ana', 'descricao': 'Camisa'},
    ]:
        monkeypatch.setattr(bot, 'resposta_demo', lambda _, r=request: 'Pedido [SOLICITACAO]' + json.dumps(r))
        bot.responder('244900000001', 'Confirmo')
    assert client.get('/api/dashboard', headers=AUTH).json()['stats']['requests'] == 0


def test_legacy_clinic_config_remains_compatible():
    from business import BusinessProfile
    old = {'nome': 'Clínica Exemplo', 'tom': 'Profissional', 'informacoes': {'servicos': {'Avaliação': 'Sob consulta'}}}
    assert BusinessProfile.model_validate(old).informacoes.servicos['Avaliação'] == 'Sob consulta'


def test_each_operation_can_be_registered_when_enabled(monkeypatch):
    p = profile('Geral personalizado')
    p['operacoes'] = {key: True for key in ('agendamentos', 'reservas', 'encomendas', 'orcamentos')}
    client.put('/api/business', headers=AUTH, json=p)
    for kind in ('agendamento', 'reserva', 'encomenda', 'orcamento'):
        details = {'tipo': kind, 'nome': 'Cliente', 'descricao': 'Solicitação confirmada pelo cliente',
                   'preferencia': 'Amanhã às 10h' if kind in ('agendamento', 'reserva') else ''}
        monkeypatch.setattr(bot, 'resposta_demo', lambda _, r=details: 'A equipa confirmará. [SOLICITACAO]' + json.dumps(r))
        bot.responder('244900000001', 'Confirmo')
    d = client.get('/api/dashboard', headers=AUTH).json()
    assert d['stats']['requests'] == 4
    assert {r['tipo'] for r in d['requests']} == {'agendamento', 'reserva', 'encomenda', 'orcamento'}


def test_reservation_without_date_is_rejected(monkeypatch):
    p = profile()
    p['operacoes']['reservas'] = True
    client.put('/api/business', headers=AUTH, json=p)
    monkeypatch.setattr(bot, 'resposta_demo', lambda _: 'Pedido [SOLICITACAO]' + json.dumps({
        'tipo': 'reserva', 'nome': 'Ana', 'descricao': 'Mesa para duas pessoas', 'preferencia': ' '}))
    bot.responder('244900000001', 'Confirmo')
    assert client.get('/api/dashboard', headers=AUTH).json()['requests'] == []
