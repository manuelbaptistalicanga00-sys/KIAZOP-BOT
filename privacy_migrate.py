"""Offline: parar API/worker, fazer backup e testar primeiro numa cópia sintética."""
import argparse
import os

from database import Database
from privacy import Vault, migrate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sqlite-copy', required=True, help='Caminho da cópia SQLite offline')
    parser.add_argument('--mode', choices=['encrypt', 'rotate', 'decrypt'], required=True)
    parser.add_argument('--confirm-offline-copy', action='store_true')
    args = parser.parse_args()
    if not args.confirm_offline_copy:
        parser.error('Exige --confirm-offline-copy')
    vault = Vault([k.strip() for k in os.environ.get('MESSAGE_ENCRYPTION_KEYS', '').split(',') if k.strip()])
    db = Database(path=args.sqlite_copy)
    try:
        migrate(db, vault, args.mode)
        print('Migração offline concluída; validar a cópia antes de promover.')
    finally:
        db.engine.dispose()


if __name__ == '__main__':
    main()
