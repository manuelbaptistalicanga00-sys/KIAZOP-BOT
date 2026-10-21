"""Persistência SQLite local ou PostgreSQL gerido, com pool e exclusão entre instâncias."""
import os
import threading
from pathlib import Path

from sqlalchemy import create_engine


class Result:
    def __init__(self, rows):
        self.rows = rows
        self.position = 0

    def fetchall(self):
        rows = self.rows[self.position:]
        self.position = len(self.rows)
        return rows

    def fetchone(self):
        if self.position >= len(self.rows):
            return None
        row = self.rows[self.position]
        self.position += 1
        return row

    def __iter__(self):
        return iter(self.fetchall())


class Database:
    def __init__(self, url=None, path='bot.db'):
        self.postgres = bool(url)
        if url:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql+psycopg://', 1)
            elif url.startswith('postgresql://'):
                url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
            if not url.startswith('postgresql+psycopg://'):
                raise ValueError('DATABASE_URL deve ser uma ligação PostgreSQL')
            self.engine = create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=1, connect_args={'connect_timeout': 10})
        else:
            if os.getenv('VERCEL'):
                raise RuntimeError('Configure DATABASE_URL na Vercel: SQLite não é persistente em serverless.')
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine('sqlite:///' + str(path), connect_args={'check_same_thread': False, 'timeout': 10})
        self.local = threading.local()
        self.mutex = threading.RLock()

    def sql(self, query):
        if not self.postgres:
            return query
        query = query.replace('INTEGER PRIMARY KEY', 'BIGSERIAL PRIMARY KEY')
        query = query.replace('ts DEFAULT CURRENT_TIMESTAMP', 'ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        query = query.replace("datetime('now','-1 hour')", "(CURRENT_TIMESTAMP - INTERVAL '1 hour')")
        if 'INSERT OR IGNORE INTO' in query:
            query = query.replace('INSERT OR IGNORE INTO', 'INSERT INTO') + ' ON CONFLICT DO NOTHING'
        return query.replace('?', '%s')

    def execute(self, query, params=()):
        conn = getattr(self.local, 'conn', None)
        if conn is not None:
            result = conn.exec_driver_sql(self.sql(query), params)
            return Result(result.fetchall() if result.returns_rows else [])
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            result = conn.exec_driver_sql(self.sql(query), params)
            return Result(result.fetchall() if result.returns_rows else [])

    def executescript(self, script):
        for query in script.split(';'):
            if query.strip():
                self.execute(query.strip())

    def commit(self):
        # As operações são autocommit; não há transações abertas durante chamadas externas.
        pass

    def __enter__(self):
        self.mutex.acquire()
        try:
            if not getattr(self.local, 'depth', 0):
                self.local.conn = self.engine.connect().execution_options(isolation_level='AUTOCOMMIT')
                if self.postgres:
                    # Lock de sessão: requer ligação direta ou pool em modo sessão.
                    self.local.conn.exec_driver_sql('SELECT pg_advisory_lock(74190321)')
            self.local.depth = getattr(self.local, 'depth', 0) + 1
            return self
        except Exception:
            if getattr(self.local, 'conn', None) is not None:
                self.local.conn.close()
                self.local.conn = None
            self.mutex.release()
            raise

    def __exit__(self, *args):
        self.local.depth -= 1
        try:
            if not self.local.depth:
                try:
                    if self.postgres:
                        self.local.conn.exec_driver_sql('SELECT pg_advisory_unlock(74190321)')
                finally:
                    self.local.conn.close()
                    self.local.conn = None
        finally:
            self.mutex.release()
