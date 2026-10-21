"""Processo sempre ligado, separado da API: python worker.py --concurrency 4."""
import argparse
import os
import signal
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--once', action='store_true', help='Drenar jobs disponíveis e sair (manutenção/testes)')
    parser.add_argument('--migrate-legacy', action='store_true', help='Colocar inbox antiga em quarentena para revisão; nunca reenviar')
    args = parser.parse_args()
    if os.getenv('VERCEL'):
        parser.error('O worker requer um serviço sempre ligado, não uma função Vercel.')
    if not 1 <= args.concurrency <= 16:
        parser.error('concurrency deve ser entre 1 e 16')
    import bot

    if args.migrate_legacy:
        count = bot.queue.import_legacy_pending()
        bot.maintenance()
        print(f'{count} entradas antigas colocadas em revisão, sem envio.')
        return
    stop = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    running = set()
    notification_task = None
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool, ThreadPoolExecutor(max_workers=1) as notify_pool:
        while not stop.is_set():
            bot.privacy.scheduled()
            bot.maintenance(send_notifications=False)
            # Alertas lentos à equipa não bloqueiam claims/IA de outras conversas.
            if notification_task is None or notification_task.done():
                if notification_task is not None:
                    try:
                        notification_task.result()
                    except Exception:
                        bot.log.error('Falha a processar notificações; verificar painel')
                notification_task = notify_pool.submit(bot.notifications.process, bot.OWNER_PHONE, bot.DEMO, bot.enviar)
            while len(running) < args.concurrency:
                job = bot.queue.claim()
                if job is None:
                    break
                running.add(pool.submit(bot.process_job, job))
            if running:
                done, running = wait(running, timeout=1, return_when=FIRST_COMPLETED)
                for future in done:
                    try:
                        future.result()
                    except Exception:
                        bot.log.error('Falha no worker; lease permite recuperação segura')
            elif args.once:
                break
            else:
                stop.wait(1)
        # SIGTERM pára novos claims e deixa terminar os jobs em curso.
    bot.maintenance()


if __name__ == '__main__':
    main()
