"""Validação local não comprova existência/acesso remoto ao modelo."""
import re


def validate_model(model):
    if not re.fullmatch(r'claude-[a-z0-9]+(?:-[a-z0-9]+)*', model):
        raise ValueError('MODEL inválido: identificador Claude sem espaços obrigatório')


def classify(exc):
    from budget import BudgetExceeded
    if isinstance(exc, BudgetExceeded):
        return 'budget', False
    import anthropic
    import httpx
    if isinstance(exc, (httpx.TimeoutException, anthropic.APITimeoutError)):
        return 'timeout', True
    if isinstance(exc, (httpx.NetworkError, anthropic.APIConnectionError)):
        return 'connection', True
    status = getattr(exc, 'status_code', None) or getattr(getattr(exc, 'response', None), 'status_code', None)
    body = getattr(exc, 'body', None)
    error = body.get('error', {}) if isinstance(body, dict) else {}
    code = error.get('type', '') if isinstance(error, dict) else ''
    if code in ('credit_balance_too_low', 'billing_error'):
        return 'quota', False
    if status and status >= 500:
        return 'unavailable', True
    return {401: ('authentication', False), 403: ('permission', False), 404: ('model', False),
            429: ('rate_limit', True), 400: ('invalid_request', False)}.get(status, ('unknown', False))


def retry_call(operation, sleep=None):
    import time
    sleep = sleep or time.sleep
    for attempt in range(3):
        try:
            return operation()
        except Exception as exc:
            if not classify(exc)[1] or attempt == 2:
                raise
            sleep(min(2, 0.5 * (2 ** attempt)))
