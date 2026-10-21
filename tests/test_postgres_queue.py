"""PostgreSQL real local/descartável; não Neon, não credenciais reais."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from database import Database
from jobqueue import JobQueue, LeaseLost


@pytest.fixture
def pg(tmp_path):
    pgserver = pytest.importorskip('pgserver')
    server = pgserver.get_server(tmp_path / 'postgres', cleanup_mode='delete')
    db = Database(server.get_uri())
    db.executescript('''
      CREATE TABLE inbox(id TEXT PRIMARY KEY,payload TEXT,status TEXT DEFAULT 'pending',error TEXT);
      CREATE TABLE seen(id TEXT PRIMARY KEY);
      CREATE TABLE paused(phone TEXT PRIMARY KEY);
    ''')
    queue = JobQueue(db)
    queue.initialize()
    try:
        yield db, queue
    finally:
        db.engine.dispose()
        server.cleanup()


def msg(mid, phone='244900000001'):
    return {'id':mid,'from':phone,'type':'text','text':{'body':'Sintético'}}


def test_postgres_atomic_claims_and_duplicates(pg):
    db, q = pg
    q.enqueue([msg('a'),msg('a'),msg('b'),msg('c','244900000002')])
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=list(pool.map(lambda _:q.claim(),range(2)))
    assert all(jobs)
    assert len({job['phone'] for job in jobs})==2
    assert db.execute('SELECT count(*) FROM jobs').fetchone()[0]==3
    assert q.claim() is None


def test_postgres_fencing_gap_and_receipt(pg):
    db,q=pg
    q.enqueue([msg('a')])
    old=q.claim()
    q.save_reply(old,{'reply':'Preparado'})
    with db:
        db.execute('UPDATE jobs SET lease_until=0')
        db.execute('UPDATE conversation_leases SET expires_at=0')
    job=q.claim()
    with pytest.raises(LeaseLost):
        q.before_send(old)
    assert q.before_send(job)
    db.execute('UPDATE jobs SET lease_until=0')
    assert q.claim() is None
    assert db.execute('SELECT state FROM jobs').fetchone()[0]=='uncertain'
    q.receipts([{'id':'sent-synthetic','status':'sent','recipient_id':job['phone'],'biz_opaque_callback_data':'job:a'}])
    finalized=[]
    q.reconcile(lambda current:finalized.append(json.loads(current['result'])))
    q.reconcile(lambda _:pytest.fail('Não finalizar duas vezes'))
    assert finalized==[{'reply':'Preparado'}]
    assert db.execute('SELECT state FROM jobs').fetchone()[0]=='done'


def test_postgres_ciphertext_and_reversible_migration(pg):
    from cryptography.fernet import Fernet
    from privacy import Vault, migrate
    db,q=pg
    vault=Vault([Fernet.generate_key().decode()])
    db.vault=vault
    q.enqueue([msg('encrypted')])
    job=q.claim()
    q.save_reply(job,{'reply':'Conteúdo sintético'})
    with db.engine.connect() as conn:
        raw=conn.exec_driver_sql("SELECT reply FROM jobs WHERE id='encrypted'").fetchone()[0]
    assert raw.startswith('enc:v1:')
    assert q._get('encrypted')['reply']=='Conteúdo sintético'
    migrate(db,vault,'decrypt')
    db.vault=None
    assert q._get('encrypted')['reply']=='Conteúdo sintético'
    migrate(db,vault,'encrypt')
    db.vault=vault
    assert q._get('encrypted')['reply']=='Conteúdo sintético'
