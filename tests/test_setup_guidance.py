"""A preparação deve explicar os estados sem fabricar um perfil/heartbeat."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_setup_guidance_preserves_operational_alerts():
    html = Path('static/index.html').read_text()
    js = Path('static/app.js').read_text()
    assert 'id="setup-status"' in html
    assert 'function renderSetup()' in js
    assert 'Login confirmado nesta sessão' in js
    assert 'worker sem batimento' in js
    assert 'Guarde os dados reais do negócio' in js


def test_setup_states_in_javascript():
    if not shutil.which('node'):
        pytest.skip('Node necessário para o contrato de apresentação')
    result = subprocess.run(['node', 'scripts/check-setup-guidance.cjs'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_configuration_prompt_uses_saved_readiness_not_catalogue_alone():
    js = Path('static/app.js').read_text()
    assert "if(!data.profile_ready){const b=el('button','Configurar o meu negócio'" in js
