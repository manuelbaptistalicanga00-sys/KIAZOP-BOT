"""Inbox durável, lease por conversa e quarentena de resultados de envio incertos."""
import json
import secrets
import time
from contextlib import contextmanager
from threading import Event, Thread


class LeaseLost(RuntimeError):
    pass


class JobQueue:
    def __init__(self, db, lease_seconds=300, clock=time.time):
        self.db, self.lease_seconds, self.clock = db, lease_seconds, clock

    def initialize(self):
        with self.db:
            self.db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs(
              id TEXT PRIMARY KEY, phone TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
              created_at DOUBLE PRECISION NOT NULL, next_attempt DOUBLE PRECISION DEFAULT 0,
              lease_owner TEXT, lease_until DOUBLE PRECISION DEFAULT 0, attempts INTEGER DEFAULT 0,
              reply TEXT, result TEXT, outgoing_id TEXT, error TEXT);
            CREATE INDEX IF NOT EXISTS jobs_claim ON jobs(state,next_attempt,created_at);
            CREATE TABLE IF NOT EXISTS conversation_leases(
              phone TEXT PRIMARY KEY, owner TEXT NOT NULL, expires_at DOUBLE PRECISION NOT NULL);
            CREATE TABLE IF NOT EXISTS ingested(id TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS delivery_receipts(
              event_key TEXT PRIMARY KEY, job_id TEXT NOT NULL, outgoing_id TEXT NOT NULL,
              phone TEXT NOT NULL, status TEXT NOT NULL);
            ''')

    def enqueue(self, messages):
        with self.db:
            for msg in messages:
                mid = msg['id']
                if self.db.execute('SELECT 1 FROM seen WHERE id=?', (mid,)).fetchone():
                    continue
                self.db.execute('INSERT OR IGNORE INTO inbox(id,payload) VALUES(?,?)', (mid, json.dumps(msg)))
                self.db.execute('INSERT OR IGNORE INTO jobs(id,phone,created_at) VALUES(?,?,?)',
                                (mid, msg['from'], self.clock()))

    def import_legacy_pending(self):
        # Só no comando explícito de migração; envios antigos sem prova vão para quarentena.
        with self.db:
            rows = self.db.execute("SELECT id,payload FROM inbox WHERE status IN ('pending','failed') AND id NOT IN (SELECT id FROM jobs)").fetchall()
            for mid, payload in rows:
                msg = json.loads(payload)
                self.db.execute("INSERT INTO jobs(id,phone,state,created_at,error) VALUES(?,?,'uncertain',?,'legacy_requires_review')",
                                (mid, msg['from'], self.clock()))
        return len(rows)

    def _get(self, mid, for_update=False):
        suffix = " FOR UPDATE" if for_update and self.db.postgres else ""
        row = self.db.execute('SELECT id,phone,state,lease_owner,reply,result,outgoing_id,attempts FROM jobs WHERE id=?' + suffix, (mid,)).fetchone()
        return dict(zip(('id', 'phone', 'state', 'owner', 'reply', 'result', 'outgoing_id', 'attempts'), row)) if row else None

    def owned(self, job):
        row = self.db.execute('SELECT 1 FROM jobs WHERE id=? AND lease_owner=? AND lease_until>?',
                              (job['id'], job['owner'], self.clock())).fetchone()
        if not row:
            raise LeaseLost('Lease expirada; não executar efeitos externos')

    def claim_sql(self):
        sql = """SELECT j.id FROM jobs j
          WHERE ((j.state IN ('pending','failed') AND j.next_attempt<=? AND j.attempts<3)
                 OR (j.state IN ('processing','prepared') AND j.lease_until<=?))
          AND NOT EXISTS(SELECT 1 FROM conversation_leases l WHERE l.phone=j.phone AND l.expires_at>?)
          AND NOT EXISTS(SELECT 1 FROM jobs prior WHERE prior.phone=j.phone AND (prior.created_at<j.created_at OR (prior.created_at=j.created_at AND prior.id<j.id))
                         AND prior.state NOT IN ('done','cancelled'))
          ORDER BY j.created_at,j.id LIMIT 1"""
        return sql + (' FOR UPDATE OF j SKIP LOCKED' if self.db.postgres else '')

    def claim(self):
        now, owner = self.clock(), secrets.token_hex(16)
        with self.db:
            # Um worker pode ter enviado e morrido antes do commit: NUNCA reenviar automaticamente.
            self.db.execute("UPDATE jobs SET state='uncertain',error='send_outcome_unknown' WHERE state='sending' AND lease_until<=?", (now,))
            row = self.db.execute(self.claim_sql(), (now, now, now)).fetchone()
            if not row:
                return None
            job = self._get(row[0])
            lease = self.db.execute('''INSERT INTO conversation_leases(phone,owner,expires_at) VALUES(?,?,?)
              ON CONFLICT(phone) DO UPDATE SET owner=excluded.owner,expires_at=excluded.expires_at
              WHERE conversation_leases.expires_at<=? RETURNING phone''',
                                    (job['phone'], owner, now + self.lease_seconds, now)).fetchone()
            if not lease:
                return None
            self.db.execute("UPDATE jobs SET state='processing',lease_owner=?,lease_until=?,attempts=attempts+1 WHERE id=?",
                            (owner, now + self.lease_seconds, job['id']))
            self.db.execute("UPDATE inbox SET status='processing' WHERE id=?", (job['id'],))
            return self._get(job['id'])

    @contextmanager
    def heartbeat(self, job):
        stop = Event()

        def renew():
            while not stop.wait(max(0.05, self.lease_seconds / 3)):
                try:
                    with self.db:
                        self.owned(job)
                        until = self.clock() + self.lease_seconds
                        self.db.execute('UPDATE jobs SET lease_until=? WHERE id=? AND lease_owner=?', (until, job['id'], job['owner']))
                        self.db.execute('UPDATE conversation_leases SET expires_at=? WHERE phone=? AND owner=?', (until, job['phone'], job['owner']))
                except Exception:
                    return  # Efeito seguinte volta a verificar lease; sem envio cego.

        thread = Thread(target=renew, daemon=True)
        thread.start()
        try:
            yield
        finally:
            stop.set()
            thread.join(timeout=2)

    def save_reply(self, job, result):
        with self.db:
            self.owned(job)
            self.db.execute("UPDATE jobs SET state='prepared',reply=?,result=? WHERE id=? AND lease_owner=?",
                            (result.get('reply'), json.dumps(result), job['id'], job['owner']))
        job.update(reply=result.get('reply'), result=json.dumps(result))

    def before_send(self, job):
        with self.db:
            self.owned(job)
            # Pausa manual posterior à geração ganha: não enviar uma resposta já preparada.
            if self.db.execute('SELECT 1 FROM paused WHERE phone=?', (job['phone'],)).fetchone():
                return False
            self.db.execute("UPDATE jobs SET state='sending' WHERE id=? AND lease_owner=?", (job['id'], job['owner']))
        return True

    def finish(self, job, finalize, outgoing_id=None, from_receipt=False):
        with self.db:
            current = self._get(job['id'], for_update=True)
            if not current or current['state'] == 'done':
                return
            if not from_receipt:
                self.owned(job)
            finalize(current)
            self.db.execute("UPDATE jobs SET state='done',outgoing_id=?,error=NULL,lease_until=0 WHERE id=?", (outgoing_id, job['id']))
            self.db.execute("UPDATE inbox SET status='done',error=NULL WHERE id=?", (job['id'],))
            self.db.execute('INSERT OR IGNORE INTO seen(id) VALUES(?)', (job['id'],))
            self.db.execute('DELETE FROM conversation_leases WHERE phone=? AND owner=?', (current['phone'], current['owner']))

    def fail(self, job, error, uncertain=False):
        with self.db:
            current = self._get(job['id'], for_update=True)
            if not current or current['state'] == 'done':
                return
            self.owned(job)
            state = 'uncertain' if uncertain else 'failed'
            self.db.execute('UPDATE jobs SET state=?,error=?,next_attempt=?,lease_until=0 WHERE id=? AND lease_owner=?',
                            (state, error, self.clock() + 30, job['id'], job['owner']))
            self.db.execute("UPDATE inbox SET status='failed',error=? WHERE id=?", (error, job['id']))
            self.db.execute('DELETE FROM conversation_leases WHERE phone=? AND owner=?', (job['phone'], job['owner']))

    def receipts(self, statuses):
        with self.db:
            for status in statuses:
                mid = status.get('biz_opaque_callback_data')
                if isinstance(mid, str) and mid.startswith('job:'):
                    job = self._get(mid[4:])
                else:
                    row = self.db.execute('SELECT id FROM jobs WHERE outgoing_id=?', (status.get('id'),)).fetchone()
                    job = self._get(row[0]) if row else None
                if not job or status.get('recipient_id') != job['phone']:
                    continue
                outgoing_id, state = status.get('id'), status.get('status')
                if isinstance(outgoing_id, str) and state in ('sent', 'delivered', 'read', 'failed'):
                    self.db.execute('INSERT OR IGNORE INTO delivery_receipts(event_key,job_id,outgoing_id,phone,status) VALUES(?,?,?,?,?)',
                                    (outgoing_id + ':' + state, job['id'], outgoing_id, job['phone'], state))

    def reconcile(self, finalize):
        with self.db:
            rows = self.db.execute("SELECT j.id,r.outgoing_id FROM jobs j JOIN delivery_receipts r ON r.job_id=j.id WHERE j.state IN ('sending','uncertain') AND r.status IN ('sent','delivered','read')").fetchall()
            for mid, outgoing_id in rows:
                self.finish(self._get(mid), finalize, outgoing_id, from_receipt=True)
        return len(rows)
