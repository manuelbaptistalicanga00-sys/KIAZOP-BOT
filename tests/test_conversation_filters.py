"""Pesquisa/filtros globais compatíveis com Cloud API, só dados sintéticos."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

import bot

AUTH = {'Authorization': 'Bearer test-admin'}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(bot, 'ADMIN_KEY', 'test-admin')
    with bot.db:
        for table in inspect(bot.db.engine).get_table_names():
            bot.db.execute(f'DELETE FROM {table}')
        for i in range(31):
            bot.db.execute('INSERT INTO msgs(phone,role,text) VALUES(?,?,?)', (f'24490000{i:04d}', 'user', 'Teste local'))
        bot.db.execute('INSERT INTO paused(phone) VALUES(?)', ('244900000000',))
        bot.db.execute("INSERT INTO notifications(id,source_id,phone,kind,status) VALUES(?,?,?,?,?)", ('filter-test', 'local', '244900000001', 'handoff', 'failed'))


def get(**params):
    return TestClient(bot.app).get('/api/dashboard', params=params, headers=AUTH)


def test_search_reaches_conversations_outside_first_page():
    result = get(phone_query='+244 900000000').json()
    assert [c['phone'] for c in result['conversations']] == ['244900000000']
    assert result['pagination']['conversations']['total'] == 1
    assert result['stats']['clients'] == 31  # métricas globais não são adulteradas


def test_human_filter_includes_paused_and_unacknowledged_notifications():
    result = get(conversation_state='human', page_size=1).json()
    assert result['pagination']['conversations']['total'] == 2
    second = get(conversation_state='human', page_size=1, page=2).json()
    assert {result['conversations'][0]['phone'], second['conversations'][0]['phone']} == {'244900000000', '244900000001'}
    assert all(c['needs_human'] for c in result['conversations'] + second['conversations'])


def test_assistant_filter_excludes_human_and_ack_changes_filter():
    result = get(conversation_state='assistant').json()
    assert result['pagination']['conversations']['total'] == 29
    assert all(not c['needs_human'] for c in result['conversations'])
    with bot.db:
        bot.db.execute("UPDATE notifications SET acknowledged_at=1 WHERE id='filter-test'")
    assert get(conversation_state='human').json()['pagination']['conversations']['total'] == 1


def test_search_and_state_combine_without_exposing_other_conversations():
    result = get(phone_query='999999', conversation_state='human').json()
    assert result['conversations'] == []
    assert result['pagination']['conversations']['total'] == 0


@pytest.mark.parametrize('params', [{'phone_query':'%'}, {'phone_query':"' OR 1=1 --"}, {'phone_query':'1'*31}, {'conversation_state':'unknown'}])
def test_invalid_filters_are_rejected(params):
    assert get(**params).status_code == 422


def test_filtered_dashboard_still_requires_authentication():
    assert TestClient(bot.app).get('/api/dashboard?phone_query=244').status_code == 401


def test_filters_preserve_laboratory_conversation():
    with bot.db:
        bot.db.execute('INSERT INTO msgs(phone,role,text) VALUES(?,?,?)', ('244900000001', 'assistant', 'Demonstração sintética'))
    result = get(phone_query='999999').json()
    assert result['conversations'] == []
    assert result['demo_conversation']['phone'] == '244900000001'
    assert result['demo_conversation']['messages'][-1]['text'] == 'Demonstração sintética'


def test_premium_filter_controls_and_server_side_query():
    from pathlib import Path
    html = Path('static/index.html').read_text()
    js = Path('static/app.js').read_text()
    assert 'id="conversation-filter-form"' in html
    assert 'id="conversation-state"' in html
    assert 'phone_query:conversationQuery' in js
    assert 'conversation_state:conversationState' in js
    assert 'data.demo_conversation' in js
    assert "data.conversations.filter(c=>c.phone.includes" not in js
