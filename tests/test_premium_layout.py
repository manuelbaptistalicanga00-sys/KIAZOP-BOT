"""Contrato visual: layout novo sem remover os controlos funcionais."""
from html.parser import HTMLParser
from pathlib import Path


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.attributes.append((tag, attrs))
        if attrs.get('id'):
            assert attrs['id'] not in self.ids, 'ID duplicado'
            self.ids.add(attrs['id'])


def test_executive_layout_and_preserved_controls():
    page = Page()
    page.feed(Path('static/index.html').read_text())
    assert any(tag == 'body' and attrs.get('data-design') == 'executive' for tag, attrs in page.attributes)
    assert {'login','login-form','key','workspace','business-form','metrics','thread','demo-form','safety-alerts','worker-status','notification-panel','budget-status'} <= page.ids
    assert any(tag == 'nav' and attrs.get('aria-label') == 'Navegação principal' for tag, attrs in page.attributes)


def test_typography_is_self_hosted_and_motion_accessible():
    css = Path('static/style.css').read_text()
    assert '@font-face' in css and '/static/fonts/' in css
    assert 'prefers-reduced-motion' in css
    assert Path('static/fonts/manrope-latin-variable.woff2').exists()


def test_login_and_overview_have_distinct_editorial_layouts():
    html = Path('static/index.html').read_text()
    assert 'login-editorial' in html
    assert 'command-visual' in html
    assert 'Todas as solicitações dependem de confirmação' in html
