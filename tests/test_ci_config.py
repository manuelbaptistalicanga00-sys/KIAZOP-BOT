"""Contrato de execução dos testes num checkout sem instalação do projecto."""
import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_resolves_root_modules_without_external_pythonpath():
    config = configparser.ConfigParser()
    config.read(ROOT / 'pytest.ini')
    assert config.has_section('pytest'), 'Configurar pytest para um checkout limpo'
    assert config['pytest']['pythonpath'].split() == ['.']


def test_ci_uses_the_selected_python_interpreter():
    workflow = (ROOT / '.github/workflows/python-app.yml').read_text()
    assert '- run: python -m pytest -q' in workflow
