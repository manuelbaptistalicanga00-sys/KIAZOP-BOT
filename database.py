"""Transacções curtas por thread; nenhum advisory lock de sessão/global."""
import os
import threading
from pathlib import Path

from sqlalchemy import create_engine


class Result:
    def __init__(self, rows, rowcount=0):
        self.rows, self.position, self.rowcount = rows, 0, rowcount

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
            self.engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=3,
                                        hide_parameters=True, connect_args={'connect_timeout': 10})
        else:
            if os.getenv('VERCEL'):
                raise RuntimeError('Configure DATABASE_URL na Vercel: SQLite não é persistente em serverless.')
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine('sqlite:///' + str(path), hide_parameters=True,
                                        connect_args={'check_same_thread': False, 'timeout': 10})
        self.local = threading.local()
        self.vault = None

    @property
    def in_transaction(self):
        return getattr(self.local, 'conn', None) is not None

    def sql(self, query):
        if not self.postgres:
            return query
        query = query.replace('INTEGER PRIMARY KEY', 'BIGSERIAL PRIMARY KEY')
        query = query.replace('ts DEFAULT CURRENT_TIMESTAMP', 'ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        query = query.replace("datetime('now','-1 hour')", "(CURRENT_TIMESTAMP - INTERVAL '1 hour')")
        query = query.replace("datetime('now','-1 day')", "(CURRENT_TIMESTAMP - INTERVAL '1 day')")
        if 'INSERT OR IGNORE INTO' in query:
            query = query.replace('INSERT OR IGNORE INTO', 'INSERT INTO') + ' ON CONFLICT DO NOTHING'
        return query.replace('?', '%s')

    def execute(self, query, params=()):
        params = self.vault.parameters(query, params) if self.vault else params
        conn = getattr(self.local, 'conn', None)
        if conn is not None:
            result = conn.exec_driver_sql(self.sql(query), params)
            return Result((self.vault.rows(result) if self.vault else result.fetchall()) if result.returns_rows else [], result.rowcount)
        with self.engine.begin() as conn:
            result = conn.exec_driver_sql(self.sql(query), params)
            return Result((self.vault.rows(result) if self.vault else result.fetchall()) if result.returns_rows else [], result.rowcount)

    def executescript(self, script):
        for query in script.split(';'):
            if query.strip():
                self.execute(query.strip())

    def commit(self):
        # Compatibilidade: a fronteira atómica é o bloco `with db`, nunca este método.
        pass

    def __enter__(self):
        if not getattr(self.local, 'depth', 0):
            self.local.conn = self.engine.connect()
            try:
                if self.postgres:
                    self.local.conn.begin()
                else:
                    # Serializa só claims/escritas CURTAS, inclusive entre processos SQLite.
                    self.local.conn.exec_driver_sql('BEGIN IMMEDIATE')
                self.local.failed = False
            except BaseException:
                self.local.conn.close()
                self.local.conn = None
                raise
        self.local.depth = getattr(self.local, 'depth', 0) + 1
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            self.local.failed = True
        self.local.depth -= 1
        if not self.local.depth:
            try:
                if self.local.failed:
                    self.local.conn.rollback()
                else:
                    self.local.conn.commit()
            finally:
                self.local.conn.close()
                self.local.conn = None
