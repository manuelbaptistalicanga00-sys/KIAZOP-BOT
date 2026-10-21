import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import bot

AUTH = {'Authorization': 'Bearer test-admin'}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    from sqlalchemy import inspect
    monkeypatch.setattr(bot, 'DEMO', True)
    monkeypatch.setattr(bot, 'ADMIN_KEY', 'test-admin')
    with bot.db:
        for table in inspect(bot.db.engine).get_table_names():
            bot.db.execute(f'DELETE FROM {table}')


def test_b4_headers_and_no_cors():
    response = TestClient(bot.app).get('/painel', headers={'Origin': 'https://evil.invalid'})
    assert response.headers.get('x-frame-options') == 'DENY'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert 'unsafe-inline' not in response.headers['content-security-policy']
    assert response.headers['cache-control'] == 'no-store'
    assert 'access-control-allow-origin' not in response.headers


def test_b4_utf8_compare(monkeypatch):
    monkeypatch.setattr(bot, 'ADMIN_KEY', 'segredo-ç')
    bot.auth(SimpleNamespace(headers={'Authorization': 'Bearer segredo-ç'}, client=SimpleNamespace(host='synthetic-ip')))


def test_b4_startup_rejects_short_production_key():
    from security import validate_admin
    with pytest.raises(ValueError, match='ADMIN_KEY'):
        validate_admin(False, 'short')
    validate_admin(True, 'test')
    validate_admin(False, 'x' * 32)


def test_b4_login_ip_limit():
    client = TestClient(bot.app)
    for _ in range(5):
        assert client.get('/api/dashboard', headers={'Authorization': 'Bearer wrong'}).status_code == 401
    response = client.get('/api/dashboard', headers=AUTH)
    assert response.status_code == 429
    assert int(response.headers['retry-after']) > 0


def test_b4_webhook_size_rejected_before_read(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')
    response = TestClient(bot.app).post('/webhook', content=b'{}', headers={'Content-Length': '1000001'})
    assert response.status_code == 413


def test_b4_webhook_rate_before_body(monkeypatch):
    monkeypatch.setattr(bot, 'DEMO', False)
    monkeypatch.setattr(bot, 'APP_SECRET', 'synthetic-secret')
    monkeypatch.setenv('WEBHOOK_RATE_PER_MINUTE', '2')
    client = TestClient(bot.app)
    for _ in range(2):
        assert client.post('/webhook', content=b'{}').status_code == 403
    assert client.post('/webhook', content=b'{}').status_code == 429


def test_b5_message_storage_is_encrypted_and_readable():
    bot.responder('244900000001', 'Texto confidencial sintético')
    with bot.db.engine.connect() as conn:
        raw = conn.exec_driver_sql('SELECT text FROM msgs ORDER BY id LIMIT 1').fetchone()[0]
        inbox = conn.exec_driver_sql('SELECT payload FROM inbox LIMIT 1').fetchone()[0]
    assert 'confidencial' not in raw
    assert 'confidencial' not in inbox
    assert 'confidencial' in bot.historico('244900000001')[0]['content']


def test_b5_reversible_migration_on_synthetic_copy(tmp_path):
    from cryptography.fernet import Fernet
    from privacy import Vault, migrate
    from database import Database
    import sqlite3
    original = tmp_path / 'original.db'
    with sqlite3.connect(original) as conn:
        conn.execute('CREATE TABLE msgs(id INTEGER PRIMARY KEY,text TEXT)')
        conn.execute("INSERT INTO msgs(text) VALUES('Segredo sintético')")
        conn.commit()
        with sqlite3.connect(tmp_path / 'copy.db') as copy:
            conn.backup(copy)
    source = Database(path=str(tmp_path / 'copy.db'))
    vault = Vault([Fernet.generate_key().decode()])
    migrate(source, vault, 'encrypt')
    raw = source.execute('SELECT text FROM msgs').fetchone()[0]
    assert raw.startswith('enc:v1:')
    assert vault.decrypt(raw) == 'Segredo sintético'
    newer = Vault([Fernet.generate_key().decode(), *vault.keys])
    migrate(source, newer, 'rotate')
    assert Vault([newer.keys[0]]).decrypt(source.execute('SELECT text FROM msgs').fetchone()[0]) == 'Segredo sintético'
    migrate(source, newer, 'decrypt')
    assert source.execute('SELECT text FROM msgs').fetchone()[0] == 'Segredo sintético'
    with sqlite3.connect(original) as conn:
        assert conn.execute('SELECT text FROM msgs').fetchone()[0] == 'Segredo sintético'
    source.engine.dispose()


def test_b5_export_delete_and_audit():
    client = TestClient(bot.app)
    bot.responder('244900000001', 'Texto a eliminar')
    response = client.get('/api/privacy/244900000001', headers=AUTH)
    assert response.status_code == 200
    assert response.json()['messages'][0]['text'] == 'Texto a eliminar'
    assert client.delete('/api/privacy/244900000001', headers=AUTH, params={'confirm': 'delete'}).status_code == 200
    assert bot.db.execute('SELECT count(*) FROM msgs').fetchone()[0] == 0
    assert bot.db.execute('SELECT count(*) FROM inbox').fetchone()[0] == 0
    assert bot.db.execute('SELECT count(*) FROM jobs').fetchone()[0] == 0
    assert bot.db.execute('SELECT count(*) FROM privacy_audit').fetchone()[0] == 2


def test_b5_retention_purges_old_data_not_recent():
    bot.responder('244900000001', 'Antigo')
    bot.responder('244900000002', 'Recente')
    bot.db.execute("UPDATE msgs SET ts='2020-01-01 00:00:00' WHERE phone='244900000001'")
    bot.db.execute("UPDATE inbox SET ts='2020-01-01 00:00:00' WHERE id IN (SELECT id FROM jobs WHERE phone='244900000001')")
    bot.db.execute("UPDATE jobs SET created_at=0 WHERE phone='244900000001'")
    response = TestClient(bot.app).post('/api/privacy/purge', headers=AUTH, params={'confirm': 'purge'})
    assert response.status_code == 200
    assert bot.db.execute("SELECT count(*) FROM msgs WHERE phone='244900000001'").fetchone()[0] == 0
    assert bot.db.execute("SELECT count(*) FROM msgs WHERE phone='244900000002'").fetchone()[0] == 2


def test_b5_scheduled_retention():
    bot.responder('244900000001', 'Antigo')
    bot.db.execute("UPDATE msgs SET ts='2020-01-01 00:00:00'")
    bot.db.execute('UPDATE jobs SET created_at=0')
    assert bot.privacy.scheduled() is True
    assert bot.privacy.scheduled() is False
    assert bot.db.execute('SELECT count(*) FROM msgs').fetchone()[0] == 0


def test_b5_access_logs_mask_phone_and_query():
    import logging
    from security import RedactAccess
    record=logging.LogRecord('uvicorn.access',20,'',1,'%s %s %s %s %s',('127.0.0.1','GET','/api/privacy/244900000001?key=secret','1.1',200),None)
    assert RedactAccess().filter(record)
    assert '244900000001' not in record.getMessage()
    assert 'secret' not in record.getMessage()


def test_b5_wrong_key_rolls_back_migration(tmp_path):
    from cryptography.fernet import Fernet, InvalidToken
    from privacy import Vault, migrate
    from database import Database
    db=Database(path=str(tmp_path/'rollback.db'))
    db.execute('CREATE TABLE msgs(id INTEGER PRIMARY KEY,text TEXT)')
    vault=Vault([Fernet.generate_key().decode()])
    encrypted=vault.encrypt('Outro texto')
    db.execute('INSERT INTO msgs(text) VALUES(?)',('Primeiro texto',))
    db.execute('INSERT INTO msgs(text) VALUES(?)',(encrypted,))
    with pytest.raises(InvalidToken):
        migrate(db,Vault([Fernet.generate_key().decode()]),'encrypt')
    assert db.execute('SELECT text FROM msgs ORDER BY id').fetchall()==[('Primeiro texto',),(encrypted,)]
    db.engine.dispose()


def test_b5_delete_active_job_requires_drain():
    bot.queue.enqueue([{'id':'active','from':'244900000001','type':'text','text':{'body':'Olá'}}])
    assert bot.queue.claim()
    response=TestClient(bot.app).delete('/api/privacy/244900000001',headers=AUTH,params={'confirm':'delete'})
    assert response.status_code==409
    assert bot.db.execute('SELECT count(*) FROM jobs').fetchone()[0]==1


def test_b4_non_ascii_signature_is_rejected_not_500(monkeypatch):
    monkeypatch.setattr(bot,'DEMO',False)
    monkeypatch.setattr(bot,'APP_SECRET','synthetic')
    response=TestClient(bot.app).post('/webhook',content=b'{}',headers={b'x-hub-signature-256':b'sha256=\xe7'})
    assert response.status_code==403
