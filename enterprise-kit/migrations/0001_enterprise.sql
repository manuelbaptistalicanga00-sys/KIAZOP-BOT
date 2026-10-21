-- Nova base/branch APENAS. Não migra automaticamente o esquema legado bot.py.
-- Executar como owner de migrações; aplicação liga com uma role membro de bot_app,
-- sem ownership, sem superuser, sem BYPASSRLS. Não conceder bot_app a utilizadores finais.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='bot_app') THEN
    CREATE ROLE bot_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
  END IF;
END $$;
CREATE SCHEMA IF NOT EXISTS bo;
REVOKE ALL ON SCHEMA bo FROM PUBLIC;
GRANT USAGE ON SCHEMA bo TO bot_app;

CREATE TABLE bo.tenants (
 tenant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL,
 auth_org_id text NOT NULL UNIQUE, status text NOT NULL DEFAULT 'trial',
 timezone text NOT NULL DEFAULT 'Africa/Luanda', currency char(3) NOT NULL DEFAULT 'USD',
 retention_days integer NOT NULL DEFAULT 90 CHECK(retention_days BETWEEN 1 AND 3650),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bo.users (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 auth_subject text NOT NULL, email text NOT NULL,
 role text NOT NULL CHECK(role IN ('owner','admin','manager','agent','analyst')),
 active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,auth_subject)
);
CREATE TABLE bo.whatsapp_connections (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 provider text NOT NULL CHECK(provider IN ('meta','qr')), external_asset_id text NOT NULL,
 waba_id text, encrypted_token text, status text NOT NULL DEFAULT 'disconnected',
 risk_accepted_at timestamptz, last_event_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(provider,external_asset_id),
 CHECK(provider <> 'qr' OR risk_accepted_at IS NOT NULL)
);
CREATE TABLE bo.contacts (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 phone_e164 text NOT NULL, display_name text, consent_basis text, consent_recorded_at timestamptz,
 opted_out_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,phone_e164)
);
CREATE TABLE bo.conversations (
 tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), contact_id uuid NOT NULL,
 connection_id uuid NOT NULL, assigned_user_id uuid,
 status text NOT NULL DEFAULT 'open', bot_paused boolean NOT NULL DEFAULT false,
 last_inbound_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,contact_id) REFERENCES bo.contacts(tenant_id,id),
 FOREIGN KEY(tenant_id,connection_id) REFERENCES bo.whatsapp_connections(tenant_id,id),
 FOREIGN KEY(tenant_id,assigned_user_id) REFERENCES bo.users(tenant_id,id)
);
CREATE TABLE bo.messages (
 tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL,
 provider text NOT NULL, external_id text NOT NULL,
 direction text NOT NULL CHECK(direction IN ('inbound','outbound')), body_ciphertext text,
 status text NOT NULL DEFAULT 'received', source text NOT NULL DEFAULT 'live',
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,provider,external_id),
 FOREIGN KEY(tenant_id,conversation_id) REFERENCES bo.conversations(tenant_id,id)
);
CREATE INDEX messages_tenant_conversation_time ON bo.messages(tenant_id,conversation_id,created_at);
CREATE TABLE bo.leads (
 tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), contact_id uuid NOT NULL,
 stage text NOT NULL DEFAULT 'new', source text NOT NULL DEFAULT 'whatsapp',
 estimated_value numeric(14,2) CHECK(estimated_value >= 0), currency char(3) NOT NULL DEFAULT 'USD',
 confirmed_revenue numeric(14,2) NOT NULL DEFAULT 0 CHECK(confirmed_revenue >= 0),
 confirmed_at timestamptz, attribution_method text, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,contact_id) REFERENCES bo.contacts(tenant_id,id)
);
CREATE TABLE bo.appointments (
 tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), contact_id uuid NOT NULL,
 external_calendar_id text, starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL,
 status text NOT NULL DEFAULT 'requested', details jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(), CHECK(ends_at > starts_at),
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,contact_id) REFERENCES bo.contacts(tenant_id,id)
);
CREATE TABLE bo.templates (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 sector text NOT NULL, name text NOT NULL, content jsonb NOT NULL,
 revision integer NOT NULL DEFAULT 1, approved_by uuid, approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,name,revision),
 FOREIGN KEY(tenant_id,approved_by) REFERENCES bo.users(tenant_id,id)
);
CREATE TABLE bo.audit_logs (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 actor_user_id uuid, action text NOT NULL, request_id uuid NOT NULL,
 safe_metadata jsonb NOT NULL DEFAULT '{}', occurred_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,actor_user_id) REFERENCES bo.users(tenant_id,id)
);
CREATE TABLE bo.billing (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 provider text NOT NULL, external_subscription_id text NOT NULL,
 plan text NOT NULL, status text NOT NULL, period_end timestamptz,
 ai_replies_used integer NOT NULL DEFAULT 0 CHECK(ai_replies_used >= 0),
 PRIMARY KEY(tenant_id,id), UNIQUE(provider,external_subscription_id)
);
CREATE TABLE bo.onboarding_attempts (
 tenant_id uuid NOT NULL, id uuid NOT NULL DEFAULT gen_random_uuid(), user_id uuid NOT NULL,
 nonce_hash text NOT NULL, provider text NOT NULL, status text NOT NULL DEFAULT 'pending',
 verified_flow text, expires_at timestamptz NOT NULL, consumed_at timestamptz,
 PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,user_id) REFERENCES bo.users(tenant_id,id)
);
CREATE TABLE bo.inbox_events (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 provider text NOT NULL, event_id text NOT NULL, payload_ciphertext text NOT NULL,
 status text NOT NULL DEFAULT 'pending', created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,provider,event_id)
);
CREATE TABLE bo.outbox_jobs (
 tenant_id uuid NOT NULL REFERENCES bo.tenants(tenant_id), id uuid NOT NULL DEFAULT gen_random_uuid(),
 idempotency_key text NOT NULL, kind text NOT NULL, payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending', attempts integer NOT NULL DEFAULT 0,
 available_at timestamptz NOT NULL DEFAULT now(), lease_until timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,idempotency_key)
);
CREATE INDEX outbox_pending ON bo.outbox_jobs(tenant_id,status,available_at);

DO $$ DECLARE t text;
BEGIN
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='bo' LOOP
  EXECUTE format('ALTER TABLE bo.%I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE bo.%I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_isolation ON bo.%I TO bot_app USING (tenant_id = nullif(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id = nullif(current_setting(''app.tenant_id'',true),'''')::uuid)',t);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON bo.%I TO bot_app',t);
 END LOOP;
END $$;
REVOKE UPDATE, DELETE ON bo.audit_logs FROM bot_app;
-- Retenção de auditoria executada por uma role operacional separada e auditada.
-- RLS protege tenant; RBAC por acção também tem de ser verificado no servidor.
