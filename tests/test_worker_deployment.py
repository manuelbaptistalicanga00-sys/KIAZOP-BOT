"""Contratos offline do worker; nunca inicia serviços nem usa segredos reais."""
import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docker_context_excludes_all_environment_secret_files():
    patterns = (ROOT / '.dockerignore').read_text().splitlines()
    for name in ('.env', '.env.worker', '.env.production', '.env.local'):
        assert any(fnmatch.fnmatch(name, pattern) for pattern in patterns), name


def test_worker_compose_requires_database_and_has_no_public_port():
    path = ROOT / 'compose.worker.yaml'
    assert path.exists(), 'Falta configuração do worker separado'
    config = path.read_text()
    assert 'python worker.py --concurrency 4' in config
    assert '${DATABASE_URL:?' in config
    assert 'restart: unless-stopped' in config
    assert 'ports:' not in config
    assert 'init: true' in config
