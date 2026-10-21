"""Limites partilhados por DB, sem confiar em X-Forwarded-For do cliente."""
import hashlib
import hmac
import json
import logging
import time

from fastapi import HTTPException


def validate_admin(demo, key):
    if not demo and (not key.strip() or len(key) < 32):
        raise ValueError('ADMIN_KEY deve ter pelo menos 32 caracteres em produção')


class Gate:
    def __init__(self, db, secret):
        self.db, self.secret = db, secret.encode()
        db.execute('CREATE TABLE IF NOT EXISTS rate_limits(id TEXT PRIMARY KEY,times TEXT NOT NULL)')

    def key(self, kind, ip):
        return hmac.new(self.secret, f'{kind}:{ip}'.encode(), hashlib.sha256).hexdigest()

    def times(self, key, window):
        self.db.execute("INSERT OR IGNORE INTO rate_limits(id,times) VALUES(?,'[]')", (key,))
        sql = 'SELECT times FROM rate_limits WHERE id=?' + (' FOR UPDATE' if self.db.postgres else '')
        return [t for t in json.loads(self.db.execute(sql, (key,)).fetchone()[0]) if t > time.time() - window]

    def save(self, key, times):
        self.db.execute('UPDATE rate_limits SET times=? WHERE id=?', (json.dumps(times), key))

    def hit(self, kind, ip, limit, window):
        key = self.key(kind, ip)
        with self.db:
            times = self.times(key, window)
            blocked = len(times) >= limit
            if not blocked:
                times.append(time.time())
            self.save(key, times)
        if blocked:
            raise HTTPException(429, 'Limite temporário', headers={'Retry-After': str(max(1, int(times[0] + window - time.time()) + 1))})

    def authenticate(self, ip, token, expected):
        valid = bool(expected) and hmac.compare_digest(token.encode('utf-8'), expected.encode('utf-8'))
        if valid:
            return  # Uma chave válida nunca é bloqueada nem altera contagem de falhas.
        key = self.key('login', ip)
        with self.db:
            times = self.times(key, 600)
            blocked = len(times) >= 5
            if not blocked:
                self.save(key, times + [time.time()])
        if blocked:
            raise HTTPException(429, 'Aguarde antes de tentar novamente', headers={'Retry-After': str(max(2, int(times[0] + 600 - time.time()) + 1))})
        if not valid:
            raise HTTPException(401, 'Autenticação necessária')


class RedactAccess(logging.Filter):
    def filter(self, record):
        import re
        def mask(value):
            if not isinstance(value, str):
                return value
            if value.startswith('/'):
                value = value.split('?', 1)[0]
            return re.sub(r'(?<!\w)\d{6,20}(?!\w)', '[number]', value)
        if isinstance(record.args, tuple):
            record.args = tuple(mask(arg) for arg in record.args)
        record.msg = mask(record.msg)
        return True
