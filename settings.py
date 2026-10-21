"""Validação offline antes de abrir a DB; nunca inclui valores secretos no erro."""
from ai_service import validate_model
from security import validate_admin
from privacy import Vault


def validate_startup(demo, config):
    if demo:
        validate_model(config.get('MODEL') or 'claude-sonnet-4-5-20250929')
        return
    errors = []
    if not config.get('DATABASE_URL', '').strip() and config.get('ALLOW_SQLITE', '').lower() != 'true':
        errors.append('DATABASE_URL obrigatória em produção; ALLOW_SQLITE=true apenas para teste local')
    for key in ('MESSAGE_ENCRYPTION_KEYS', 'APP_SECRET', 'VERIFY_TOKEN', 'WA_TOKEN', 'WA_PHONE_ID', 'ANTHROPIC_API_KEY', 'MODEL'):
        if not config.get(key, '').strip():
            errors.append(f'{key} obrigatório em produção')
    try:
        validate_admin(False, config.get('ADMIN_KEY', ''))
    except ValueError as exc:
        errors.append(str(exc))
    model = config.get('MODEL', '')
    if model:
        try:
            validate_model(model)
        except ValueError as exc:
            errors.append(str(exc))
    keys = config.get('MESSAGE_ENCRYPTION_KEYS', '')
    if keys:
        try:
            Vault([k.strip() for k in keys.split(',') if k.strip()])
        except Exception:
            errors.append('MESSAGE_ENCRYPTION_KEYS inválidas: configure chaves Fernet válidas')
    url = config.get('DATABASE_URL', '')
    if url and not url.startswith(('postgres://', 'postgresql://', 'postgresql+psycopg://')):
        errors.append('DATABASE_URL inválida: exige PostgreSQL')
    if errors:
        raise ValueError('Configuração de arranque inválida: ' + '; '.join(errors))
