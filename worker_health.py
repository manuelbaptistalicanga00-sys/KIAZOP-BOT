"""Batimento independente de IA/manutenção e idade de jobs por resolver."""
import time
import uuid
from contextlib import contextmanager
from threading import Event, Thread


class WorkerHealth:
    def __init__(self, db):
        self.db = db
        db.execute('CREATE TABLE IF NOT EXISTS worker_heartbeats(id TEXT PRIMARY KEY,last_seen DOUBLE PRECISION NOT NULL)')

    def beat(self, worker_id):
        self.db.execute('INSERT INTO worker_heartbeats(id,last_seen) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen', (worker_id,time.time()))

    def status(self):
        now=time.time()
        last=self.db.execute('SELECT max(last_seen) FROM worker_heartbeats').fetchone()[0]
        oldest=self.db.execute("SELECT min(created_at) FROM jobs WHERE state NOT IN ('done','cancelled')").fetchone()[0]
        age=max(0,now-last) if last is not None else None
        pending=max(0,now-oldest) if oldest is not None else None
        alive=age is not None and age<=60
        return {'worker_alive':alive,'worker_heartbeat_age_seconds':round(age,1) if age is not None else None,
                'oldest_pending_age_seconds':round(pending,1) if pending is not None else None,
                'operations_alert':not alive or (pending is not None and pending>300)}

    @contextmanager
    def running(self, log):
        worker_id=uuid.uuid4().hex
        stop=Event()
        self.beat(worker_id)
        def heartbeat():
            while not stop.wait(15):
                try:
                    self.beat(worker_id)
                except Exception:
                    log.error('Não foi possível gravar batimento do worker')
        thread=Thread(target=heartbeat,daemon=True)
        thread.start()
        try:
            yield
        finally:
            stop.set()
            thread.join(timeout=12)
            self.db.execute('DELETE FROM worker_heartbeats WHERE id=?',(worker_id,))
