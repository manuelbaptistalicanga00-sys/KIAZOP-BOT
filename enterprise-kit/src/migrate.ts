import { Client } from 'pg';
import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
const url = process.env.DIRECT_URL;
if (!url) throw new Error('DIRECT_URL obrigatória para migrações. Não usar a role da aplicação.');
const client = new Client({ connectionString: url, connectionTimeoutMillis: 10000 });
await client.connect();
try {
  await client.query('BEGIN');
  await client.query('SELECT pg_advisory_xact_lock(90372001)'); // Lock transaccional só nas migrações.
  await client.query('CREATE SCHEMA IF NOT EXISTS bo_meta');
  await client.query('CREATE TABLE IF NOT EXISTS bo_meta.migrations(name text primary key, checksum text not null, applied_at timestamptz default now())');
  const folder = new URL('../migrations/', import.meta.url);
  for (const name of (await readdir(folder)).filter(f => f.endsWith('.sql')).sort()) {
    const content = await readFile(new URL(name, folder), 'utf8');
    const checksum = createHash('sha256').update(content).digest('hex');
    const prior = await client.query('SELECT checksum FROM bo_meta.migrations WHERE name=$1', [name]);
    if (prior.rowCount) {
      if (prior.rows[0].checksum !== checksum) throw new Error('Migração já aplicada foi alterada: ' + name);
      continue;
    }
    await client.query(content);
    await client.query('INSERT INTO bo_meta.migrations(name,checksum) VALUES($1,$2)', [name, checksum]);
  }
  await client.query('COMMIT');
  console.log('Migrações concluídas.');
} catch (error) { await client.query('ROLLBACK'); throw error; }
finally { await client.end(); }
