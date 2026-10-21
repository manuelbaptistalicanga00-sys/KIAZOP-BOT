"""O processo de testes nunca carrega URLs/chaves de produção nem abre sockets."""
import os
import tempfile

import pytest
from cryptography.fernet import Fernet
os.environ["MESSAGE_ENCRYPTION_KEYS"] = Fernet.generate_key().decode()

for key in ('DATABASE_URL', 'DIRECT_URL', 'WA_TOKEN', 'WA_PHONE_ID', 'VERIFY_TOKEN',
            'APP_SECRET', 'OWNER_PHONE', 'ANTHROPIC_API_KEY', 'OWNER_TEMPLATE_NAME'):
    os.environ[key] = ''
os.environ.pop('VERCEL', None)
os.environ['DEMO_MODE'] = 'true'
os.environ['ADMIN_KEY'] = 'test-admin'
os.environ['DB_PATH'] = tempfile.mktemp(prefix='pilot-tests-', suffix='.db')


@pytest.fixture(autouse=True)
def no_external_connections(monkeypatch):
    import socket

    def deny(*args, **kwargs):
        raise AssertionError('Ligações de rede proibidas nos testes sintéticos')

    monkeypatch.setattr(socket.socket, 'connect', deny)
