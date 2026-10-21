"""Reconciliação local e explícita; nunca escolher not-sent sem prova externa."""
import argparse


def review(bot, mid, outcome, operator, evidence, outgoing_id=None):
    if outcome not in ('sent', 'not-sent') or not operator.strip() or len(evidence.strip()) < 12:
        raise ValueError('Operador e resumo de evidência obrigatórios (sem dados sensíveis).')
    if outcome == 'sent' and not outgoing_id:
        raise ValueError('Identificador de saída obrigatório para envio confirmado.')
    with bot.db:
        # Mesma ordem de locking do claim/finish, evitando alterações concorrentes.
        sql = 'SELECT state FROM jobs WHERE id=?'
        if bot.db.postgres:
            sql += ' FOR UPDATE'
        row = bot.db.execute(sql, (mid,)).fetchone()
        if not row or row[0] != 'uncertain':
            raise ValueError('Só envios incertos podem ser reconciliados por este comando.')
        job = bot.queue._get(mid)
        bot.db.execute('INSERT INTO reconciliation_log(job_id,outcome,operator,evidence) VALUES(?,?,?,?)',
                       (mid, outcome, operator.strip()[:160], evidence.strip()[:1200]))
        if outcome == 'sent':
            bot.queue.finish(job, bot.finalize_job, outgoing_id, from_receipt=True)
        else:
            # Prova de não envio: reutilizar resposta persistida, sem chamar IA novamente.
            bot.db.execute("UPDATE jobs SET state='pending',next_attempt=0,attempts=0,lease_until=0 WHERE id=?", (mid,))
            bot.db.execute("UPDATE inbox SET status='pending',error=NULL WHERE id=?", (mid,))
            bot.db.execute('DELETE FROM conversation_leases WHERE phone=? AND owner=?', (job['phone'], job['owner']))
        bot.db.execute("DELETE FROM paused WHERE phone=? AND phone IN (SELECT phone FROM handoff_reasons WHERE reason='delivery_unknown')", (job['phone'],))
        bot.db.execute("DELETE FROM handoff_reasons WHERE phone=? AND reason='delivery_unknown'", (job['phone'],))
        bot.db.execute("UPDATE alerts SET resolved=1 WHERE phone=? AND code='delivery_unknown'", (job['phone'],))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job_id')
    parser.add_argument('--outcome', required=True, choices=['sent', 'not-sent'])
    parser.add_argument('--outgoing-id')
    parser.add_argument('--operator', required=True)
    parser.add_argument('--evidence', required=True, help='Resumo da prova, sem PII, chaves ou tokens')
    parser.add_argument('--confirm-reviewed', action='store_true')
    args = parser.parse_args()
    if not args.confirm_reviewed:
        parser.error('Exige --confirm-reviewed após revisão no fornecedor/equipa.')
    import bot
    try:
        review(bot, args.job_id, args.outcome, args.operator, args.evidence, args.outgoing_id)
    except ValueError as exc:
        parser.error(str(exc))
    print('Reconciliação registada. Nenhum envio executado por este comando.')


if __name__ == '__main__':
    main()
