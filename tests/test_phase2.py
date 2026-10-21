import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import bot

AUTH = {'Authorization': 'Bearer test-admin'}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    from sqlalchemy import inspect
    monkeypatch.setattr(bot, 'DEMO', True)
    monkeypatch.setattr(bot, 'ADMIN_KEY', 'test-admin')
    with bot.db:
        for table in inspect(bot.db.engine).get_table_names():
            bot.db.execute(f'DELETE FROM {table}')


def test_env_no_duplicates():
    names = [line.split('=', 1)[0] for line in Path('.env.example').read_text().splitlines() if line and not line.startswith('#')]
    assert len(names) == len(set(names))


def test_model_startup_validation():
    from ai_service import validate_model
    for model in ('', 'wrong-model', 'claude x', 'claude-sonnet\n'):
        with pytest.raises(ValueError, match='MODEL'):
            validate_model(model)
    validate_model('claude-sonnet-4-5-20250929')


def test_diagnostic_authenticated_and_no_key(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', '')
    client = TestClient(bot.app)
    assert client.post('/api/diagnostics/ai').status_code == 401
    response = client.post('/api/diagnostics/ai', headers=AUTH)
    assert response.status_code == 200
    assert response.json()['category'] == 'configuration'
    assert response.json()['verified'] is False


@pytest.mark.parametrize('status,category,retry', [(401,'authentication',False),(403,'permission',False),(404,'model',False),(429,'rate_limit',True),(500,'unavailable',True),(400,'invalid_request',False)])
def test_ai_failure_classes(status, category, retry):
    import httpx
    from ai_service import classify
    response = httpx.Response(status, request=httpx.Request('POST','https://synthetic.invalid'))
    exc = httpx.HTTPStatusError('secret must not be logged', request=response.request, response=response)
    assert classify(exc) == (category, retry)


def test_ai_timeout_class():
    import httpx
    from ai_service import classify
    assert classify(httpx.ReadTimeout('synthetic')) == ('timeout', True)


def test_ai_retries_only_transient():
    import httpx
    from ai_service import retry_call
    calls = []
    def transient():
        calls.append(1)
        if len(calls)<3:
            raise httpx.ReadTimeout('synthetic')
        return 'ok'
    assert retry_call(transient, sleep=lambda _: None) == 'ok'
    assert len(calls) == 3
    calls.clear()
    def fatal():
        calls.append(1)
        response=httpx.Response(401,request=httpx.Request('POST','https://synthetic.invalid'))
        raise httpx.HTTPStatusError('private',request=response.request,response=response)
    with pytest.raises(httpx.HTTPStatusError):
        retry_call(fatal, sleep=lambda _:None)
    assert len(calls)==1


@pytest.mark.parametrize('raw', [
    'Pedido [HUMANO] texto depois', 'Pedido [HUMANO][HUMANO]',
    'Pedido [SOLICITACAO]{"tipo":"encomenda","nome":"Ana","descricao":"Camisa","extra":"bad"}',
    'Pedido [AGENDAMENTO]{"nome":2,"servico":"Corte","data_hora":"Amanhã"}',
    'Pedido [SOLICITACAO]{"tipo":"encomenda","nome":"Ana","nome":"Outra","descricao":"Camisa"}',
    'Pedido [OUTRA_TAG] privado',
])
def test_strict_tags_reject_invalid(raw):
    from actions import parse_response
    result = parse_response(raw, {'agendamentos':True,'reservas':True,'encomendas':True,'orcamentos':True})
    assert result.get('action') is None
    assert result['human'] is True
    assert '[' not in result['reply']
    assert 'privado' not in result['reply']


def test_strict_tags_valid_and_disabled():
    from actions import parse_response
    raw='A equipa confirmará. [SOLICITACAO]{"tipo":"reserva","nome":"Ana","descricao":"Mesa","preferencia":"Amanhã"}'
    assert parse_response(raw, {'reservas':True})['action']['data']['tipo']=='reserva'
    assert parse_response(raw, {'reservas':False}).get('action') is None
    assert parse_response('Vou encaminhar. [HUMANO]', {})['human'] is True


def test_budget_warns_blocks_and_survives_new_instance():
    from budget import Budget, BudgetExceeded
    events=[]
    budget=Budget(bot.db, lambda code:events.append(code), limit_micro=100)
    token=budget.reserve(80)
    budget.settle(token,80)
    assert 'ai_budget_80' in events
    with pytest.raises(BudgetExceeded):
        budget.reserve(21)
    assert 'ai_budget_100' in events
    other=Budget(bot.db,lambda _:None,limit_micro=100)
    with pytest.raises(BudgetExceeded):
        other.reserve(21)


def test_budget_atomic_concurrent_reservations():
    from budget import Budget, BudgetExceeded
    from concurrent.futures import ThreadPoolExecutor
    budget=Budget(bot.db,lambda _:None,limit_micro=100)
    def reserve(_):
        try:
            budget.reserve(60)
            return True
        except BudgetExceeded:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(reserve,range(2)))==1


def test_dashboard_pagination_is_bounded_and_disjoint():
    for i in range(5):
        bot.responder(f'24490000000{i}', 'Olá')
    client=TestClient(bot.app)
    one=client.get('/api/dashboard?page=1&page_size=2',headers=AUTH).json()
    two=client.get('/api/dashboard?page=2&page_size=2',headers=AUTH).json()
    assert len(one['conversations'])==2
    assert {c['phone'] for c in one['conversations']}.isdisjoint({c['phone'] for c in two['conversations']})
    assert one['pagination']['conversations']['total']==5
    assert client.get('/api/dashboard?page=0',headers=AUTH).status_code==422
    assert client.get('/api/dashboard?page_size=1000',headers=AUTH).status_code==422


def test_thread_pagination():
    for i in range(3):
        bot.responder('244900000001', f'Mensagem {i}')
    client=TestClient(bot.app)
    one=client.get('/api/conversations/244900000001/messages?page_size=2',headers=AUTH)
    assert one.status_code==200
    assert one.json()['total']==6
    assert len(one.json()['messages'])==2


def test_model_diagnostic_uses_metadata_not_generation(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    class Client:
        def __init__(self,**kwargs):
            self.models=self
        def __enter__(self):
            return self
        def __exit__(self,*args):
            pass
        def retrieve(self,model):
            assert not bot.db.in_transaction
            calls.append(model)
            return SimpleNamespace(id=model)
    monkeypatch.setenv('ANTHROPIC_API_KEY','synthetic-only')
    monkeypatch.setattr(bot,'Anthropic',Client)
    response=TestClient(bot.app).post('/api/diagnostics/ai',headers=AUTH)
    assert response.json()['verified'] is True
    assert calls==[bot.MODEL]


def test_actual_import_rejects_invalid_model_and_key(tmp_path):
    import subprocess
    import sys
    env=dict(os.environ,DEMO_MODE='false',ADMIN_KEY='short',MODEL=bot.MODEL,DB_PATH=str(tmp_path/'unused.db'))
    result=subprocess.run([sys.executable,'-c','import bot'],env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode!=0
    assert 'ADMIN_KEY deve' in result.stderr
    env.update(ADMIN_KEY='x'*32,MODEL='not-a-model')
    result=subprocess.run([sys.executable,'-c','import bot'],env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode!=0
    assert 'MODEL inválido' in result.stderr
    assert not (tmp_path/'unused.db').exists()
