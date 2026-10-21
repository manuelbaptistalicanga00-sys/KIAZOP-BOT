import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';

test('Postgres WASM: RLS, FORCE, contexto, FK composta e auditoria append-only', async () => {
  const db = new PGlite();
  try {
    await db.exec(await readFile(new URL('../migrations/0001_enterprise.sql', import.meta.url), 'utf8'));
    const a = '11111111-1111-4111-8111-111111111111', b = '22222222-2222-4222-8222-222222222222';
    const cb = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
    await db.query('INSERT INTO bo.tenants(tenant_id,name,auth_org_id) VALUES($1,$2,$3),($4,$5,$6)', [a,'Empresa A','org_a',b,'Empresa B','org_b']);
    await db.query('INSERT INTO bo.contacts(tenant_id,id,phone_e164) VALUES($1,$2,$3)', [b,cb,'+244900000002']);
    const secured = await db.query<{ tablename: string }>("SELECT tablename FROM pg_tables WHERE schemaname='bo'");
    assert.equal(secured.rows.length, 14);
    const flags = await db.query<{ secured: boolean }>("SELECT bool_and(relrowsecurity AND relforcerowsecurity) AS secured FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='bo' AND c.relkind='r'");
    assert.equal(flags.rows[0].secured, true);
    await db.exec('BEGIN; SET LOCAL ROLE bot_app;');
    assert.equal((await db.query('SELECT * FROM bo.tenants')).rows.length, 0);
    await db.query("SELECT set_config('app.tenant_id',$1,true)", [a]);
    assert.equal((await db.query('SELECT * FROM bo.tenants')).rows.length, 1);
    assert.equal((await db.query('SELECT * FROM bo.contacts')).rows.length, 0);
    await assert.rejects(() => db.query('INSERT INTO bo.contacts(tenant_id,phone_e164) VALUES($1,$2)', [b,'+244900000003']), /row-level security/);
    await db.exec('ROLLBACK; BEGIN; SET LOCAL ROLE bot_app;');
    await db.query("SELECT set_config('app.tenant_id',$1,true)", [a]);
    await assert.rejects(() => db.query('INSERT INTO bo.leads(tenant_id,contact_id) VALUES($1,$2)', [a,cb]), /foreign key/);
    await db.exec('ROLLBACK; BEGIN; SET LOCAL ROLE bot_app;');
    await db.query("SELECT set_config('app.tenant_id',$1,true)", [a]);
    await db.query('INSERT INTO bo.audit_logs(tenant_id,action,request_id) VALUES($1,$2,$3)', [a,'test.action','33333333-3333-4333-8333-333333333333']);
    await assert.rejects(() => db.query('DELETE FROM bo.audit_logs'), /permission denied/);
    await db.exec('ROLLBACK;');
  } finally { await db.close(); }
});
