import pytest

from database import Database


def test_sqlite_persistence_and_nested_lock(tmp_path):
    path = str(tmp_path / 'data.db')
    db = Database(path=path)
    with db:
        db.execute('CREATE TABLE test(id INTEGER PRIMARY KEY, value TEXT)')
        with db:
            db.execute('INSERT INTO test(value) VALUES(?)', ('persistido',))
    other = Database(path=path)
    assert other.execute('SELECT value FROM test').fetchone()[0] == 'persistido'
    db.engine.dispose()
    other.engine.dispose()


def test_postgres_sql_translation():
    # Apenas compilação/adaptação: não abre ligação nem exige credenciais.
    db = Database('postgresql://localhost/kiazop')
    assert 'BIGSERIAL PRIMARY KEY' in db.sql('id INTEGER PRIMARY KEY')
    assert 'ts TIMESTAMP' in db.sql('ts DEFAULT CURRENT_TIMESTAMP')
    assert db.sql('INSERT OR IGNORE INTO seen(id) VALUES(?)') == 'INSERT INTO seen(id) VALUES(%s) ON CONFLICT DO NOTHING'
    assert "INTERVAL '1 hour'" in db.sql("ts>datetime('now','-1 hour')")
    db.engine.dispose()


def test_vercel_requires_persistent_database(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    with pytest.raises(RuntimeError, match='DATABASE_URL'):
        Database()


def test_reject_unknown_database_protocol():
    with pytest.raises(ValueError, match='PostgreSQL'):
        Database('mysql://localhost/test')
