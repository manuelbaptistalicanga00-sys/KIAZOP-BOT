import postgres from 'postgres';
import { drizzle } from 'drizzle-orm/postgres-js';
import { sql } from 'drizzle-orm';
import { ActorSchema, type Actor } from './contracts.js';

export function connectApplication(url: string) {
  // Este módulo NÃO lê DIRECT_URL e não usa locks de sessão.
  const client = postgres(url, { max: 3, prepare: false, connect_timeout: 10 });
  return { db: drizzle(client), close: () => client.end() };
}
export type AppDatabase = ReturnType<typeof connectApplication>['db'];
export async function withTenant<T>(db: AppDatabase, untrustedActor: Actor,
  fn: (tx: Parameters<Parameters<AppDatabase['transaction']>[0]>[0]) => Promise<T>) {
  const actor = ActorSchema.parse(untrustedActor);
  return db.transaction(async tx => {
    // Contexto LOCAL à transação: seguro com PgBouncer em transaction mode.
    await tx.execute(sql`select set_config('app.tenant_id', ${actor.tenantId}, true)`);
    await tx.execute(sql`select set_config('app.user_id', ${actor.userId}, true)`);
    return fn(tx);
  });
}
