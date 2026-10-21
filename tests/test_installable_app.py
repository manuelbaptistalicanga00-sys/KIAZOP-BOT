"""Instalação web sem cache persistente de conversas ou credenciais."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

import bot


def test_manifest_and_icons_are_public_and_same_origin():
    client = TestClient(bot.app)
    response = client.get('/static/manifest.webmanifest')
    assert response.status_code == 200
    manifest = response.json()
    assert manifest['start_url'] == '/painel'
    assert manifest['scope'] == '/'
    assert manifest['display'] == 'standalone'
    assert manifest['id'] == '/painel'
    assert {icon['sizes'] for icon in manifest['icons']} >= {'192x192', '512x512'}
    for icon in manifest['icons']:
        assert icon['src'].startswith('/static/')
        image = client.get(icon['src'])
        assert image.status_code == 200
        assert image.content.startswith(b'\x89PNG\r\n\x1a\n')


def test_installation_assets_do_not_cache_private_data():
    client = TestClient(bot.app)
    response = client.get('/service-worker.js')
    assert response.status_code == 200
    assert 'javascript' in response.headers['content-type']
    assert response.headers['cache-control'] == 'no-store'
    assert 'caches.open' not in response.text
    assert 'respondWith' not in response.text
    assert client.get('/api/dashboard').status_code == 401
    html = client.get('/painel').text
    assert 'rel="manifest"' in html
    assert 'rel="apple-touch-icon"' in html
    js = Path('static/app.js').read_text()
    assert "register('/service-worker.js')" in js


def test_manifest_contains_no_credentials():
    path = Path('static/manifest.webmanifest')
    assert path.exists()
    manifest = json.loads(path.read_text())
    assert '?' not in manifest['start_url']
    assert manifest['name'] == 'KIAZOP — Central de operações'
