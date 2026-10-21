"""Regressões sintéticas para Fase 1 B1-B3. Não usam contas externas."""
import hashlib
import hmac
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient

import bot


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', True)
    monkeypatch.setattr(bot, 'ADMIN_KEY', 'test-admin')
    monkeypatch.setattr(bot, 'OWNER_PHONE', '')
    with bot.db:
        # Novas tabelas são limpas quando estiverem implementadas.
        for name in ('jobs', 'conversation_leases', 'ingested', 'delivery_receipts', 'notifications', 'alerts', 'handoff_reasons', 'reconciliation_log'):
            if bot.db.postgres:
                continue
            if bot.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone():
                bot.db.execute(f'DELETE FROM {name}')
        for name in ('msgs', 'bookings', 'paused', 'seen', 'inbox', 'business_config', 'requests'):
            bot.db.execute(f'DELETE FROM {name}')
    yield


def signed_messages(messages):
    raw = json.dumps({'entry': [{'changes': [{'value': {'messages': messages}}]}]}).encode()
    headers = {'x-hub-signature-256': 'sha256=' + hmac.new(b'synthetic-secret', raw, hashlib.sha256).hexdigest()}
    return raw, headers


def test_webhook_ack_does_not_process_ai(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')
    calls = []
    monkeypatch.setattr(bot, 'responder', lambda *args: calls.append(args))
    raw, headers = signed_messages([{'id': 'ack-1', 'from': '244900000001', 'type': 'text', 'text': {'body': 'Olá'}}])
    assert TestClient(bot.app).post('/webhook', content=raw, headers=headers).status_code == 200
    assert calls == [], 'ACK não pode esperar pela IA nem executar processamento em background da função web'
    assert bot.db.execute("SELECT status FROM inbox WHERE id='ack-1'").fetchone()[0] == 'pending'


def test_two_conversations_generate_in_parallel(monkeypatch):
    active = maximum = 0
    guard = threading.Lock()

    def reply(_):
        nonlocal active, maximum
        with guard:
            active += 1
            maximum = max(maximum, active)
        time.sleep(0.15)
        with guard:
            active -= 1
        return 'Resposta sintética.'

    monkeypatch.setattr(bot, 'resposta_demo', reply)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(bot.responder, '244900000001', 'Olá')
        b = pool.submit(bot.responder, '244900000002', 'Olá')
        a.result(timeout=5)
        b.result(timeout=5)
    assert maximum == 2, 'Não pode existir lock global durante IA/HTTP'


def test_failed_owner_notification_is_visible(monkeypatch):
    monkeypatch.setattr(bot, 'OWNER_PHONE', '244900000099')

    def send(phone, text, *args, **kwargs):
        if phone == bot.OWNER_PHONE:
            raise httpx.ConnectError('synthetic')
        return 'synthetic-message-id'

    monkeypatch.setattr(bot, 'enviar', send)
    bot.responder('244900000001', 'Quero falar com humano')
    dashboard = TestClient(bot.app).get('/api/dashboard', headers={'Authorization': 'Bearer test-admin'}).json()
    assert dashboard['stats'].get('notifications_failed', 0) == 1
    assert dashboard['notifications'][0]['status'] == 'failed'
    assert dashboard['conversations'][0]['needs_human'] is True


def test_unready_production_profile_never_calls_ai_and_notifies_once(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    calls, sends = [], []

    def forbidden_client(*args, **kwargs):
        calls.append(True)
        raise RuntimeError('AI must not be called')

    monkeypatch.setattr(bot, 'Anthropic', forbidden_client)
    monkeypatch.setattr(bot, 'enviar', lambda *args, **kwargs: sends.append(args) or 'synthetic-id')
    bot.responder('244900000001', 'Olá')
    bot.responder('244900000001', 'Está aí?')
    assert calls == []
    assert len(sends) == 1
    assert 'O meu negócio' not in sends[0][1]
    assert TestClient(bot.app).get('/health').json()['profile_ready'] is False


def message(mid='queued-1', phone='244900000001'):
    return {'id': mid, 'from': phone, 'type': 'text', 'text': {'body': 'Olá'}}


def dashboard():
    return TestClient(bot.app).get('/api/dashboard', headers={'Authorization': 'Bearer test-admin'}).json()


def test_duplicate_webhooks_produce_one_send_after_worker(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')
    calls = []
    raw, headers = signed_messages([message()])
    for _ in range(3):
        assert TestClient(bot.app).post('/webhook', content=raw, headers=headers).status_code == 200
    monkeypatch.setattr(bot, 'DEMO', True)
    monkeypatch.setattr(bot, 'enviar', lambda *args: calls.append(args) or 'sent-id')
    bot.processar_pendentes()
    bot.processar_pendentes()
    assert len(calls) == 1
    assert bot.db.execute('SELECT count(*) FROM ingested').fetchone()[0] == 1
    assert bot.db.execute("SELECT count(*) FROM msgs WHERE role='assistant'").fetchone()[0] == 1


def test_persistence_failure_returns_503_not_ack(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')

    def fail(_):
        raise RuntimeError('synthetic unavailable database')

    monkeypatch.setattr(bot.queue, 'enqueue', fail)
    raw, headers = signed_messages([message()])
    assert TestClient(bot.app).post('/webhook', content=raw, headers=headers).status_code == 503


def test_send_commit_gap_is_quarantined_and_receipt_reconciles(monkeypatch):
    calls = []
    monkeypatch.setattr(bot, 'enviar', lambda *args: calls.append(args) or 'wamid.synthetic')
    original = bot.finalize_job

    def crash_commit(_):
        raise RuntimeError('synthetic commit failure after accepted send')

    monkeypatch.setattr(bot, 'finalize_job', crash_commit)
    bot.queue.enqueue([message()])
    bot.processar_pendentes()
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'uncertain'
    assert dashboard()['conversations'][0]['needs_human'] is True
    bot.processar_pendentes()
    assert len(calls) == 1
    assert TestClient(bot.app).post('/api/inbox/retry', headers={'Authorization': 'Bearer test-admin'}).status_code == 200
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'uncertain'
    monkeypatch.setattr(bot, 'finalize_job', original)
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')
    raw = json.dumps({'entry': [{'changes': [{'value': {'statuses': [{
        'id': 'wamid.synthetic', 'status': 'sent', 'recipient_id': '244900000001',
        'biz_opaque_callback_data': 'job:queued-1',
    }]}}]}]}).encode()
    headers = {'x-hub-signature-256': 'sha256=' + hmac.new(b'synthetic-secret', raw, hashlib.sha256).hexdigest()}
    client = TestClient(bot.app)
    assert client.post('/webhook', content=raw, headers=headers).status_code == 200
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'uncertain'  # Só persistiu receipt
    bot.processar_pendentes()
    bot.processar_pendentes()
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'done'
    assert len(calls) == 1
    assert bot.db.execute("SELECT count(*) FROM msgs WHERE role='assistant'").fetchone()[0] == 1
    assert bot.db.execute('SELECT count(*) FROM paused').fetchone()[0] == 0


def test_crash_after_sending_state_never_auto_resends(monkeypatch):
    bot.queue.enqueue([message()])
    job = bot.queue.claim()
    bot.queue.save_reply(job, {'reply': 'Preparado', 'raw': ''})
    assert bot.queue.before_send(job)
    with bot.db:
        bot.db.execute('UPDATE jobs SET lease_until=0')
        bot.db.execute('UPDATE conversation_leases SET expires_at=0')
    calls = []
    monkeypatch.setattr(bot, 'enviar', lambda *args: calls.append(args))
    bot.processar_pendentes()
    assert calls == []
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'uncertain'
    assert dashboard()['alerts'][0]['code'] == 'delivery_unknown'


def test_lease_fences_stale_worker_and_reuses_prepared_reply():
    from jobqueue import LeaseLost
    bot.queue.enqueue([message()])
    old = bot.queue.claim()
    bot.queue.save_reply(old, {'reply': 'Já preparado', 'raw': ''})
    with bot.db:
        bot.db.execute('UPDATE jobs SET lease_until=0')
        bot.db.execute('UPDATE conversation_leases SET expires_at=0')
    new = bot.queue.claim()
    assert new['owner'] != old['owner']
    assert new['reply'] == 'Já preparado'
    with pytest.raises(LeaseLost):
        bot.queue.before_send(old)
    assert bot.queue.before_send(new)


def test_same_conversation_is_exclusive_other_phone_claims():
    bot.queue.enqueue([message('a'), message('b'), message('c', '244900000002')])
    first = bot.queue.claim()
    second = bot.queue.claim()
    assert first['phone'] != second['phone']
    assert bot.queue.claim() is None


def test_separate_database_instances_share_atomic_conversation_lease():
    from database import Database
    from jobqueue import JobQueue
    other = Database(path=bot.DB_PATH)
    try:
        q2 = JobQueue(other)
        bot.queue.enqueue([message('a'), message('b')])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda q: q.claim(), (bot.queue, q2)))
        assert sum(job is not None for job in results) == 1
    finally:
        other.engine.dispose()


def test_heartbeat_renews_during_slow_provider(monkeypatch):
    monkeypatch.setattr(bot.queue, 'lease_seconds', 0.3)
    bot.queue.enqueue([message('a'), message('b')])
    job = bot.queue.claim()
    with bot.queue.heartbeat(job):
        time.sleep(0.5)
        assert bot.queue.claim() is None
        assert bot.db.execute('SELECT expires_at FROM conversation_leases').fetchone()[0] > time.time()


def test_ai_and_send_execute_without_transaction(monkeypatch):
    def reply(_):
        assert not bot.db.in_transaction
        return 'Olá.'

    def send(*args):
        assert not bot.db.in_transaction
        return 'synthetic'

    monkeypatch.setattr(bot, 'resposta_demo', reply)
    monkeypatch.setattr(bot, 'enviar', send)
    bot.responder('244900000001', 'Olá')
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'done'


def test_production_owner_outside_window_requires_template(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'OWNER_PHONE', '244900000099')
    sends = []
    monkeypatch.setattr(bot, 'enviar', lambda *args: sends.append(args) or 'synthetic')
    bot.responder('244900000001', 'Olá')
    assert len(sends) == 1  # Só encaminhamento ao cliente, nunca texto livre ao dono sem janela.
    notification = dashboard()['notifications'][0]
    assert notification['status'] == 'failed'
    assert notification['error'] == 'approved_template_required'


def test_approved_template_is_used_outside_window(monkeypatch):
    monkeypatch.setenv('OWNER_TEMPLATE_NAME', 'pilot_attention_approved')
    monkeypatch.setenv('OWNER_TEMPLATE_LANGUAGE', 'pt_PT')
    payloads = []

    def post(url, **kwargs):
        assert not bot.db.in_transaction
        payloads.append(kwargs['json'])
        return httpx.Response(200, json={'messages': [{'id': 'wamid.template'}]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(bot.httpx, 'post', post)
    with bot.db:
        bot.notifications.schedule('event', '244900000001', 'handoff', '244900000099')
    bot.notifications.process('244900000099', False, lambda *args: pytest.fail('Texto livre proibido'))
    assert payloads[0]['type'] == 'template'
    assert payloads[0]['template']['name'] == 'pilot_attention_approved'
    assert dashboard()['notifications'][0]['status'] == 'sent'


def test_recent_owner_inbound_allows_free_text():
    with bot.db:
        bot.db.execute("INSERT INTO msgs(phone,role,text) VALUES(?,'user','Olá')", ('244900000099',))
        bot.notifications.schedule('event', '244900000001', 'handoff', '244900000099')
    sent = []
    bot.notifications.process('244900000099', False, lambda *args: sent.append(args) or 'synthetic')
    assert len(sent) == 1
    assert dashboard()['notifications'][0]['status'] == 'sent'


def test_expired_notification_send_fails_visibly_without_retry():
    with bot.db:
        bot.notifications.schedule('event', '244900000001', 'handoff', '244900000099')
        bot.db.execute("UPDATE notifications SET status='sending',lease_until=0")
    bot.notifications.process('244900000099', False, lambda *args: pytest.fail('Não repetir envio incerto'))
    assert dashboard()['notifications'][0]['error'] == 'delivery_unknown'


def test_saved_valid_profile_enables_ai_and_only_releases_profile_pause(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'enviar', lambda *args: 'synthetic')
    bot.responder('244900000001', 'Olá sem perfil')
    client = TestClient(bot.app)
    auth = {'Authorization': 'Bearer test-admin'}
    client.post('/api/conversations/244900000002/pause', headers=auth, json={'paused': True})
    result = client.put('/api/business', headers=auth, json={
        'nome': 'Loja Esperança', 'informacoes': {'horario': '08h–17h'},
    })
    assert result.status_code == 200
    assert result.json()['profile_ready'] is True
    assert bot.db.execute('SELECT phone FROM paused').fetchall() == [('244900000002',)]
    calls = []

    class Client:
        def __init__(self, **kwargs):
            assert not bot.db.in_transaction
            self.messages = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def create(self, **kwargs):
            assert not bot.db.in_transaction
            calls.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type='text', text='Horário: 08h–17h.')])

    monkeypatch.setattr(bot, 'Anthropic', Client)
    bot.responder('244900000001', 'Qual o horário?')
    assert len(calls) == 1
    assert not dashboard()['conversations'][0]['paused']


@pytest.mark.parametrize('payload', [
    {'nome': 'O meu negócio', 'informacoes': {'horario': '08h–17h'}},
    {'nome': 'Loja Esperança', 'informacoes': {}},
    {'nome': 'Loja Esperança', 'informacoes': {'horario': '   '}},
    {'unexpected': 'invalid'},
])
def test_default_empty_or_invalid_saved_profile_is_unready(payload):
    with bot.db:
        bot.db.execute("INSERT INTO business_config(id,payload) VALUES('active',?)", (json.dumps(payload),))
    assert bot.profile_ready() is False


def test_postgres_claim_uses_skip_locked_without_live_connection():
    from database import Database
    from jobqueue import JobQueue
    pg = Database('postgresql://localhost/synthetic')
    try:
        assert JobQueue(pg).claim_sql().endswith('FOR UPDATE OF j SKIP LOCKED')
        assert "INTERVAL '1 day'" in pg.sql("datetime('now','-1 day')")
    finally:
        pg.engine.dispose()


def test_legacy_inbox_migration_never_resends():
    with bot.db:
        bot.db.execute('INSERT INTO inbox(id,payload) VALUES(?,?)', ('legacy', json.dumps(message())))
    assert bot.queue.import_legacy_pending() == 1
    assert bot.queue.claim() is None
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'uncertain'


def test_manual_review_requires_evidence_and_audits_without_sending(monkeypatch):
    from reconcile import review
    bot.queue.enqueue([message()])
    job = bot.queue.claim()
    bot.queue.save_reply(job, {'reply': 'Preparado', 'raw': ''})
    bot.queue.before_send(job)
    bot.queue.fail(job, 'unknown', uncertain=True)
    bot.require_review(job)
    monkeypatch.setattr(bot, 'enviar', lambda *args: pytest.fail('Reconciliação não envia'))
    with pytest.raises(ValueError):
        review(bot, job['id'], 'sent', 'operador', 'Prova validada no fornecedor')
    with pytest.raises(ValueError):
        review(bot, job['id'], 'not-sent', 'operador', '')
    review(bot, job['id'], 'not-sent', 'operador', 'Fornecedor confirmou não aceite')
    assert bot.db.execute('SELECT state FROM jobs').fetchone()[0] == 'pending'
    assert bot.db.execute('SELECT outcome FROM reconciliation_log').fetchone()[0] == 'not-sent'
    assert bot.db.execute('SELECT count(*) FROM paused').fetchone()[0] == 0


def test_worker_cli_drains_synthetic_db(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ, DB_PATH=str(tmp_path / 'worker.db'), DEMO_MODE='true')
    seed = subprocess.run([sys.executable, '-c', "import bot; bot.queue.enqueue([{'id':'child-1','from':'244900000001','type':'text','text':{'body':'Olá'}}])"], env=env, capture_output=True, text=True, timeout=10)
    assert seed.returncode == 0, seed.stderr
    command = [sys.executable, 'worker.py', '--once']
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr

    import sqlite3
    with sqlite3.connect(env['DB_PATH']) as db:
        assert db.execute('SELECT state FROM jobs').fetchone()[0] == 'done'
        assert db.execute('SELECT count(*) FROM msgs').fetchone()[0] == 2
