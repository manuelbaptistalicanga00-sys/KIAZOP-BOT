"""Orçamento local estimado em micro-USD; não substitui factura/limite do fornecedor."""
import os
import secrets
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
from zoneinfo import ZoneInfo


class BudgetExceeded(RuntimeError):
    pass


def money(value):
    result = Decimal(value)
    if not result.is_finite() or result <= 0:
        raise ValueError('Limites/preços de IA devem ser positivos e finitos')
    return result


class Budget:
    def __init__(self, db, warn, limit_micro=None):
        self.db, self.warn = db, warn
        self.limit = limit_micro if limit_micro is not None else int(money(os.getenv('AI_DAILY_BUDGET_USD', '5')) * 1_000_000)
        self.input_price = money(os.getenv('AI_INPUT_USD_PER_MILLION', '3'))
        self.output_price = money(os.getenv('AI_OUTPUT_USD_PER_MILLION', '15'))
        db.execute('CREATE TABLE IF NOT EXISTS ai_budget(day TEXT PRIMARY KEY,spent BIGINT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS ai_reservations(id TEXT PRIMARY KEY,day TEXT,cost BIGINT,state TEXT)')

    def day(self):
        return datetime.now(ZoneInfo('Africa/Luanda')).date().isoformat()

    def lock_day(self, day):
        self.db.execute('INSERT OR IGNORE INTO ai_budget(day,spent) VALUES(?,0)', (day,))
        sql = 'SELECT spent FROM ai_budget WHERE day=?' + (' FOR UPDATE' if self.db.postgres else '')
        return self.db.execute(sql, (day,)).fetchone()[0]

    def cost(self, input_tokens, output_tokens):
        return int((Decimal(input_tokens) * self.input_price + Decimal(output_tokens) * self.output_price).to_integral_value(rounding=ROUND_CEILING))

    def reserve(self, cost):
        day, token = self.day(), secrets.token_hex(16)
        with self.db:
            spent = self.lock_day(day)
            blocked = spent + cost > self.limit
            if blocked:
                self.warn('ai_budget_100')
            else:
                self.db.execute('UPDATE ai_budget SET spent=spent+? WHERE day=?', (cost, day))
                self.db.execute("INSERT INTO ai_reservations(id,day,cost,state) VALUES(?,?,?,'reserved')", (token, day, cost))
                if spent + cost >= self.limit * 0.8:
                    self.warn('ai_budget_80')
        if blocked:
            raise BudgetExceeded('Orçamento diário insuficiente para nova chamada')
        return token

    def settle(self, token, actual_cost):
        with self.db:
            sql = 'SELECT day,cost,state FROM ai_reservations WHERE id=?' + (' FOR UPDATE' if self.db.postgres else '')
            row = self.db.execute(sql, (token,)).fetchone()
            if not row or row[2] != 'reserved':
                return
            day, reserved, _ = row
            spent = self.lock_day(day) - reserved + max(0, actual_cost)
            self.db.execute('UPDATE ai_budget SET spent=? WHERE day=?', (spent, day))
            self.db.execute("UPDATE ai_reservations SET state='settled',cost=? WHERE id=?", (actual_cost, token))
            if spent >= self.limit * 0.8:
                self.warn('ai_budget_100' if spent >= self.limit else 'ai_budget_80')

    def status(self):
        row = self.db.execute('SELECT spent FROM ai_budget WHERE day=?', (self.day(),)).fetchone()
        return {'day': self.day(), 'spent_micro_usd': row[0] if row else 0, 'limit_micro_usd': self.limit, 'estimated': True}

    def call(self, estimated_cost, operation):
        """Uma reserva por tentativa; só libertar quando não houve aceitação."""
        import httpx
        token = self.reserve(estimated_cost)
        try:
            response = operation()
        except Exception as exc:
            from ai_service import classify
            category, _ = classify(exc)
            status = getattr(exc, 'status_code', None) or getattr(getattr(exc, 'response', None), 'status_code', None)
            cause = exc
            connection_not_opened = False
            for _ in range(8):
                if isinstance(cause, httpx.ConnectError):
                    connection_not_opened = True
                    break
                cause = getattr(cause, '__cause__', None)
                if cause is None:
                    break
            if category != 'timeout' and ((status is not None and 400 <= status < 500 and status != 408) or connection_not_opened):
                self.settle(token, 0)
            # Timeouts, 5xx ou ligação interrompida após possível aceitação conservam reserva.
            raise
        usage = getattr(response, 'usage', None)
        if usage is not None:
            self.settle(token, self.cost(usage.input_tokens, usage.output_tokens))
        return response
