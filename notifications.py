"""Notificações persistentes. Sem template aprovado/janela não enviar texto livre."""
import os
import secrets
import time

import httpx


class NotificationService:
    def __init__(self, db):
        self.db = db

    def initialize(self):
        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS notifications(
              id TEXT PRIMARY KEY, source_id TEXT NOT NULL, phone TEXT NOT NULL, kind TEXT NOT NULL,
              owner_phone TEXT, status TEXT NOT NULL DEFAULT 'pending', error TEXT, outgoing_id TEXT,
              lease_owner TEXT, lease_until DOUBLE PRECISION DEFAULT 0, UNIQUE(source_id,kind))''')
            from sqlalchemy import inspect
            columns = {c['name'] for c in inspect(self.db.local.conn).get_columns('notifications')}
            if 'acknowledged_at' not in columns:
                self.db.execute('ALTER TABLE notifications ADD COLUMN acknowledged_at DOUBLE PRECISION')

    def schedule(self, source_id, phone, kind, owner_phone):
        if not owner_phone or not owner_phone.strip():
            return False
        self.db.execute('INSERT OR IGNORE INTO notifications(id,source_id,phone,kind,owner_phone) VALUES(?,?,?,?,?)',
                        (secrets.token_hex(16), source_id, phone, kind, owner_phone))

    def needs_human(self, phone):
        return bool(self.db.execute("SELECT 1 FROM notifications WHERE phone=? AND acknowledged_at IS NULL AND status IN ('failed','pending','sending')", (phone,)).fetchone())

    def list_recent(self):
        return [dict(zip(('id', 'phone', 'kind', 'status', 'error', 'acknowledged_at'), row)) for row in self.db.execute(
            'SELECT id,phone,kind,status,error,acknowledged_at FROM notifications ORDER BY id DESC LIMIT 100')]

    def acknowledge(self, notification_id=None, phone=None):
        clause, value = ('id', notification_id) if notification_id is not None else ('phone', phone)
        return self.db.execute(f'UPDATE notifications SET acknowledged_at=? WHERE {clause}=? AND acknowledged_at IS NULL', (time.time(), value)).rowcount

    def _send(self, notification, owner_phone, demo, send_text):
        if not owner_phone:
            raise ValueError('owner_not_configured')
        template = os.getenv('OWNER_TEMPLATE_NAME', '').strip()
        if template and not demo:
            if self.db.in_transaction:
                raise RuntimeError('Envio dentro de transacção é proibido')
            # Template de alerta sem parâmetros, previamente aprovado; não inclui PII.
            response = httpx.post(
                f"https://graph.facebook.com/{os.getenv('WA_API_VERSION', 'v23.0')}/{os.getenv('WA_PHONE_ID', '')}/messages",
                headers={'Authorization': f"Bearer {os.getenv('WA_TOKEN', '')}"},
                json={'messaging_product': 'whatsapp', 'to': owner_phone, 'type': 'template',
                      'template': {'name': template, 'language': {'code': os.getenv('OWNER_TEMPLATE_LANGUAGE', 'pt_PT')}}},
                timeout=20,
            )
            response.raise_for_status()
            return response.json()['messages'][0]['id']
        if not demo:
            # Só uma mensagem de entrada do próprio dono abre janela; envio ao dono não abre.
            with self.db:
                window = self.db.execute("SELECT 1 FROM msgs WHERE phone=? AND role='user' AND ts>datetime('now','-1 day') LIMIT 1", (owner_phone,)).fetchone()
            if not window:
                raise ValueError('approved_template_required')
        return send_text(owner_phone, 'Há um atendimento que requer atenção. Abra o painel seguro para consultar os detalhes.')

    def process(self, owner_phone, demo, send_text, limit=20):
        for _ in range(limit):
            owner, now = secrets.token_hex(16), time.time()
            with self.db:
                self.db.execute("UPDATE notifications SET status='failed',error='delivery_unknown' WHERE status='sending' AND lease_until<=?", (now,))
                sql = "SELECT id FROM notifications WHERE status='pending' AND acknowledged_at IS NULL ORDER BY id LIMIT 1"
                if self.db.postgres:
                    sql += ' FOR UPDATE SKIP LOCKED'
                row = self.db.execute(sql).fetchone()
                if not row:
                    return
                mid = row[0]
                self.db.execute("UPDATE notifications SET status='sending',lease_owner=?,lease_until=? WHERE id=?", (owner, now + 60, mid))
            # Nenhum lock ou transacção durante Meta.
            try:
                outgoing = self._send(mid, owner_phone, demo, send_text)
                status, error = 'sent', None
            except ValueError as exc:
                outgoing, status = None, 'failed'
                error = str(exc) if str(exc) in ('owner_not_configured', 'approved_template_required') else 'invalid_configuration'
            except Exception:
                outgoing, status, error = None, 'failed', 'provider_failure_or_unknown'
            with self.db:
                self.db.execute('UPDATE notifications SET status=?,error=?,outgoing_id=? WHERE id=? AND lease_owner=?',
                                (status, error, outgoing, mid, owner))
