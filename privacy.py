"""Cifragem de conteúdo, migração reversível e ciclo de vida. Sem alegação legal."""
import json
import re
import time
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy import inspect

PROTECTED = {
    'msgs': ('text',), 'inbox': ('payload',), 'jobs': ('reply', 'result'),
    'business_config': ('payload',), 'bookings': ('nome', 'servico', 'data_hora'),
    'requests': ('nome', 'descricao', 'preferencia'),
    'reconciliation_log': ('operator', 'evidence'),
}


class Vault:
    def __init__(self, keys, allow_legacy=True):
        self.keys, self.allow_legacy = keys, allow_legacy
        if not keys:
            raise ValueError('MESSAGE_ENCRYPTION_KEYS obrigatório; não gerar chave efémera')
        self.fernet = MultiFernet([Fernet(key.encode()) for key in keys])

    def encrypt(self, value):
        if value is None:
            return None
        return 'enc:v1:' + self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, value):
        if value is None:
            return None
        if not value.startswith('enc:v1:'):
            if not self.allow_legacy:
                raise ValueError('Dados antigos exigem migração antes da activação')
            return value
        return self.fernet.decrypt(value[7:].encode()).decode()

    def parameters(self, query, params):
        # SQL interno parametrizado, nunca SQL fornecido pelo utilizador.
        insert = re.search(r'INSERT(?: OR IGNORE)? INTO (\w+)\s*\(([^)]+)\)\s*VALUES\(([^)]+)\)', query, re.I)
        values = list(params)
        if insert and insert[1].lower() in PROTECTED:
            index = 0
            for col, expr in zip(insert[2].split(','), insert[3].split(',')):
                if expr.strip() == '?':
                    if col.strip().lower() in PROTECTED[insert[1].lower()]:
                        values[index] = self.encrypt(values[index])
                    index += 1
        update = re.search(r'UPDATE (\w+) SET (.+?)(?: WHERE |$)', query, re.I)
        if update and update[1].lower() in PROTECTED:
            index = 0
            for expr in update[2].split(','):
                col, _, rhs = expr.partition('=')
                if rhs.strip() == '?':
                    if col.strip().lower() in PROTECTED[update[1].lower()]:
                        values[index] = self.encrypt(values[index])
                    index += 1
        return tuple(values)

    def rows(self, result):
        if not result.returns_rows:
            return []
        names = list(result.keys())
        protected = {c for fields in PROTECTED.values() for c in fields}
        return [tuple(self.decrypt(v) if name in protected and isinstance(v, str) else v for name, v in zip(names, row)) for row in result.fetchall()]


def migrate(db, vault, mode):
    if mode not in ('encrypt', 'decrypt', 'rotate'):
        raise ValueError('Modo inválido')
    tables = set(inspect(db.engine).get_table_names())
    # Uma transacção: erro de chave/corrupção faz rollback de TODA a transformação.
    with db.engine.begin() as conn:
        for table, fields in PROTECTED.items():
            if table not in tables:
                continue
            columns = {c['name'] for c in inspect(db.engine).get_columns(table)}
            for col in set(fields) & columns:
                last = None
                while True:
                    query = f'SELECT id,{col} FROM {table}' + (' WHERE id>?' if last is not None else '') + ' ORDER BY id LIMIT 200'
                    rows = conn.exec_driver_sql(db.sql(query), (last,) if last is not None else ()).fetchall()
                    if not rows:
                        break
                    for mid, value in rows:
                        if value is not None:
                            plain = vault.decrypt(value)
                            transformed = plain if mode == 'decrypt' else vault.encrypt(plain)
                            conn.exec_driver_sql(db.sql(f'UPDATE {table} SET {col}=? WHERE id=?'), (transformed, mid))
                    last = rows[-1][0]


class Privacy:
    def __init__(self, db, fingerprint):
        self.db, self.fingerprint = db, fingerprint
        db.execute('CREATE TABLE IF NOT EXISTS maintenance_state(id TEXT PRIMARY KEY,last_run DOUBLE PRECISION)')
        db.execute('CREATE TABLE IF NOT EXISTS privacy_audit(id INTEGER PRIMARY KEY,action TEXT,subject_hash TEXT,ts DEFAULT CURRENT_TIMESTAMP)')

    def audit(self, action, phone='*'):
        self.db.execute('INSERT INTO privacy_audit(action,subject_hash) VALUES(?,?)', (action, self.fingerprint('privacy', phone)))

    def export(self, phone):
        with self.db:
            data = {}
            for name, table in [('messages', 'msgs'), ('jobs', 'jobs'), ('requests', 'requests'), ('bookings', 'bookings'), ('notifications', 'notifications')]:
                rows = self.db.execute(f'SELECT * FROM {table} WHERE phone=?', (phone,)).fetchall()
                cols = [c['name'] for c in inspect(self.db.engine).get_columns(table)]
                data[name] = [dict(zip(cols, row)) for row in rows]
            ids = [job['id'] for job in data['jobs']]
            data['inbox'] = [dict(id=mid, payload=self.db.execute('SELECT payload FROM inbox WHERE id=?', (mid,)).fetchone()[0]) for mid in ids]
            self.audit('export', phone)
            return data

    def ensure_idle(self, phone=None):
        if self.db.postgres:
            self.db.execute('LOCK TABLE jobs,notifications IN SHARE ROW EXCLUSIVE MODE')
        notify_sql = "SELECT 1 FROM notifications WHERE status='sending' AND lease_until>?"
        notify_params = (time.time(),)
        if phone:
            notify_sql += ' AND phone=?'
            notify_params += (phone,)
        if self.db.execute(notify_sql, notify_params).fetchone():
            from fastapi import HTTPException
            raise HTTPException(409, 'Drene notificações antes de eliminar dados')
        sql = "SELECT 1 FROM jobs WHERE state IN ('processing','prepared','sending') AND lease_until>?"
        params = (time.time(),)
        if phone:
            sql += ' AND phone=?'
            params += (phone,)
        if self.db.execute(sql, params).fetchone():
            from fastapi import HTTPException
            raise HTTPException(409, 'Pare/drene o worker antes de eliminar dados activos')

    def delete_jobs(self, ids):
        for mid in ids:
            for table, col in [('delivery_receipts', 'job_id'), ('reconciliation_log', 'job_id'), ('ingested', 'id'), ('inbox', 'id'), ('seen', 'id'), ('jobs', 'id')]:
                self.db.execute(f'DELETE FROM {table} WHERE {col}=?', (mid,))

    def delete(self, phone):
        with self.db:
            self.ensure_idle(phone)
            ids = [r[0] for r in self.db.execute('SELECT id FROM jobs WHERE phone=?', (phone,))]
            self.delete_jobs(ids)
            # Inbox anterior à fila também contém dados; ler pelo adaptador (descifra).
            for mid, payload in self.db.execute('SELECT id,payload FROM inbox').fetchall():
                if json.loads(payload).get('from') == phone:
                    self.delete_jobs([mid])
            for table in ('msgs', 'bookings', 'requests', 'notifications', 'paused', 'handoff_reasons', 'conversation_leases', 'alerts'):
                self.db.execute(f'DELETE FROM {table} WHERE phone=?', (phone,))
            self.audit('delete', phone)

    def purge(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
        with self.db:
            self.ensure_idle()
            ids = [r[0] for r in self.db.execute('SELECT id FROM jobs WHERE created_at<?', (time.time() - 90 * 86400,))]
            self.delete_jobs(ids)
            for mid, in self.db.execute('SELECT id FROM inbox WHERE ts<?', (cutoff,)).fetchall():
                self.delete_jobs([mid])
            for table in ('msgs', 'bookings', 'requests'):
                self.db.execute(f'DELETE FROM {table} WHERE ts<?', (cutoff,))
            # Notificações sem job já expurgado não precisam de guardar o número.
            self.db.execute('DELETE FROM notifications WHERE source_id NOT IN (SELECT id FROM jobs)')
            self.db.execute("DELETE FROM alerts WHERE phone<>'*' AND phone NOT IN (SELECT phone FROM jobs)")
            for table in ('paused', 'handoff_reasons', 'conversation_leases'):
                self.db.execute(f'DELETE FROM {table} WHERE phone NOT IN (SELECT phone FROM msgs) AND phone NOT IN (SELECT phone FROM jobs)')
            self.db.execute('DELETE FROM privacy_audit WHERE ts<?', (cutoff,))
            for key, timestamps in self.db.execute('SELECT id,times FROM rate_limits').fetchall():
                if not any(t > time.time() - 600 for t in json.loads(timestamps)):
                    self.db.execute('DELETE FROM rate_limits WHERE id=?', (key,))
            self.audit('purge_90_days')

    def scheduled(self):
        from fastapi import HTTPException
        try:
            with self.db:
                self.db.execute("INSERT OR IGNORE INTO maintenance_state(id,last_run) VALUES('retention',0)")
                query = "SELECT last_run FROM maintenance_state WHERE id='retention'" + (' FOR UPDATE' if self.db.postgres else '')
                last = self.db.execute(query).fetchone()[0]
                if last > time.time() - 86400:
                    return False
                self.purge()
                self.db.execute("UPDATE maintenance_state SET last_run=? WHERE id='retention'", (time.time(),))
            return True
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            return False  # Trabalhadores activos: tentar no ciclo seguinte, nunca cortar envio.
