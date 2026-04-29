# 04 — Ma'lumotlar bazasi schema

> PostgreSQL 15+ va pgvector. Schema-per-tenant.
> Har modul uchun jadval va ustunlar.

---

## Strategiya

### Public schema

Faqat shared (cross-tenant) ma'lumotlar:

```sql
-- Tenants (kompaniyalar)
CREATE TABLE public.tenants (
  id SERIAL PRIMARY KEY,
  schema_name VARCHAR(63) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  industry VARCHAR(50),
  plan_id INT REFERENCES plans(id),
  status VARCHAR(20) DEFAULT 'active',  -- active, trial, suspended, archived
  trial_ends_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (cross-tenant qidiruv uchun)
CREATE TABLE public.users (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id) NOT NULL,
  email VARCHAR(200) UNIQUE NOT NULL,
  phone VARCHAR(20) UNIQUE NOT NULL,
  password_hash VARCHAR(60) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  is_owner BOOLEAN DEFAULT FALSE,
  email_verified_at TIMESTAMPTZ,
  phone_verified_at TIMESTAMPTZ,
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plans
CREATE TABLE public.plans (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,  -- 'start', 'pro', 'business', 'enterprise'
  name VARCHAR(100),
  monthly_price_uzs INT,
  yearly_price_uzs INT,
  ai_tokens_monthly INT,
  features JSONB,
  is_active BOOLEAN DEFAULT TRUE
);

-- Plan items (per-modul narxlar)
CREATE TABLE public.plan_items (
  id SERIAL PRIMARY KEY,
  plan_id INT REFERENCES plans(id),
  module VARCHAR(50),  -- 'crm', 'smm', 'ads', 'inbox', 'reports', 'integrations'
  monthly_price_uzs INT,
  features JSONB
);

-- Invoices
CREATE TABLE public.invoices (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  invoice_number VARCHAR(50) UNIQUE,
  amount_uzs INT,
  status VARCHAR(20),  -- 'pending', 'paid', 'overdue', 'cancelled'
  due_date DATE,
  paid_at TIMESTAMPTZ,
  payment_method VARCHAR(20),  -- 'bank', 'cash', 'click', 'payme', 'uzum'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Integration catalog (marketplace)
CREATE TABLE public.integrations_catalog (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE,
  name VARCHAR(100),
  category VARCHAR(50),
  logo_url VARCHAR(500),
  description TEXT,
  is_featured BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  config_schema JSONB
);
```

### Tenant schema (har kompaniya uchun)

Yaratiladi: `tenant_<schema_name>` (masalan `tenant_akme_salon`).

Migration har yangi tenant'da bajariladi.

---

## Foundation jadvallari (har tenant)

```sql
-- Departments (tree)
CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  parent_id INT REFERENCES departments(id),
  name VARCHAR(200),
  head_user_id INT,
  position INT,  -- ko'rsatish tartibi
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Roles
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE,  -- 'owner', 'admin', 'manager', 'operator', 'viewer', custom
  name VARCHAR(100),
  permissions JSONB,  -- { "contacts": "edit", "deals": "view", ... }
  is_system BOOLEAN DEFAULT FALSE  -- standart 5 ta uchun TRUE
);

-- User-role-department
CREATE TABLE user_roles (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES public.users(id),
  role_id INT REFERENCES roles(id),
  department_id INT REFERENCES departments(id),
  scope VARCHAR(20),  -- 'all', 'department', 'own'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notifications
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  type VARCHAR(50),
  title VARCHAR(200),
  body TEXT,
  link VARCHAR(500),
  is_read BOOLEAN DEFAULT FALSE,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  read_at TIMESTAMPTZ
);

-- Tasks (umumiy)
CREATE TABLE tasks (
  id SERIAL PRIMARY KEY,
  title VARCHAR(300),
  description TEXT,
  status VARCHAR(20),  -- 'new', 'in_progress', 'review', 'done', 'cancelled'
  priority VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
  assignee_id INT,
  creator_id INT,
  related_type VARCHAR(50),  -- 'contact', 'deal', 'post', 'campaign', 'message'
  related_id INT,
  starts_at TIMESTAMPTZ,
  due_at TIMESTAMPTZ,
  estimated_hours NUMERIC(5,1),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task subtasks
CREATE TABLE task_subtasks (
  id SERIAL PRIMARY KEY,
  task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
  title VARCHAR(300),
  is_done BOOLEAN DEFAULT FALSE,
  position INT
);

-- Audit log
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id INT,
  action VARCHAR(100),  -- 'contact.created', 'deal.stage_changed', ...
  resource_type VARCHAR(50),
  resource_id INT,
  changes JSONB,  -- before/after diff
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Verification codes (SMS, email)
CREATE TABLE verification_codes (
  id SERIAL PRIMARY KEY,
  user_id INT,
  type VARCHAR(20),  -- 'phone', 'email', 'password_reset', '2fa'
  code VARCHAR(10),
  expires_at TIMESTAMPTZ,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API keys
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  key_hash VARCHAR(64),  -- SHA256 of key
  key_preview VARCHAR(8),  -- first 8 chars for UI
  permissions JSONB,
  rate_limit INT,
  ip_whitelist INET[],
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  created_by INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  revoked_at TIMESTAMPTZ
);
```

---

## CRM modul jadvallari

```sql
-- Contacts
CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  type VARCHAR(20),  -- 'individual', 'company'
  name VARCHAR(300),
  phone VARCHAR(20) UNIQUE,
  email VARCHAR(200),
  ai_score INT DEFAULT 0,  -- 0-100
  ai_score_explanation TEXT,
  ai_score_updated_at TIMESTAMPTZ,
  source VARCHAR(50),  -- 'website', 'instagram', 'referral', ...
  status VARCHAR(20),  -- 'new', 'active', 'inactive', 'blocked'
  department_id INT REFERENCES departments(id),
  assignee_id INT,
  custom_fields JSONB,
  notes TEXT,
  birthday DATE,
  social_links JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contacts_phone ON contacts(phone);
CREATE INDEX idx_contacts_assignee ON contacts(assignee_id);
CREATE INDEX idx_contacts_ai_score ON contacts(ai_score DESC);

-- Pipelines
CREATE TABLE pipelines (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  is_default BOOLEAN DEFAULT FALSE,
  position INT
);

-- Deal stages
CREATE TABLE deal_stages (
  id SERIAL PRIMARY KEY,
  pipeline_id INT REFERENCES pipelines(id) ON DELETE CASCADE,
  name VARCHAR(100),
  default_probability INT,  -- 0-100
  color VARCHAR(7),
  position INT,
  is_won BOOLEAN DEFAULT FALSE,
  is_lost BOOLEAN DEFAULT FALSE
);

-- Deals
CREATE TABLE deals (
  id SERIAL PRIMARY KEY,
  pipeline_id INT REFERENCES pipelines(id),
  stage_id INT REFERENCES deal_stages(id),
  contact_id INT REFERENCES contacts(id),
  title VARCHAR(300),
  amount_uzs BIGINT,
  probability INT,  -- 0-100
  ai_win_probability INT,  -- AI bashorati
  expected_close_date DATE,
  closed_at TIMESTAMPTZ,
  closed_status VARCHAR(20),  -- 'won', 'lost'
  closed_reason TEXT,
  source VARCHAR(50),
  utm_source VARCHAR(100),
  utm_campaign VARCHAR(100),
  assignee_id INT,
  custom_fields JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Products
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  category VARCHAR(100),
  name VARCHAR(300),
  description TEXT,
  price_uzs BIGINT,
  cost_uzs BIGINT,
  unit VARCHAR(20),
  sku VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  custom_fields JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deal products
CREATE TABLE deal_products (
  id SERIAL PRIMARY KEY,
  deal_id INT REFERENCES deals(id) ON DELETE CASCADE,
  product_id INT REFERENCES products(id),
  quantity NUMERIC(10,2),
  price_uzs BIGINT,
  discount_percent NUMERIC(5,2)
);

-- Activities (timeline)
CREATE TABLE activities (
  id SERIAL PRIMARY KEY,
  contact_id INT REFERENCES contacts(id),
  deal_id INT REFERENCES deals(id),
  type VARCHAR(20),  -- 'call', 'email', 'message', 'meeting', 'note'
  direction VARCHAR(10),  -- 'inbound', 'outbound'
  user_id INT,
  subject VARCHAR(300),
  content TEXT,
  duration_seconds INT,
  attachments JSONB,
  metadata JSONB,
  occurred_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Score history
CREATE TABLE contact_score_history (
  id BIGSERIAL PRIMARY KEY,
  contact_id INT REFERENCES contacts(id),
  score INT,
  factors JSONB,
  calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Automations
CREATE TABLE automations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  trigger_type VARCHAR(50),
  trigger_config JSONB,
  conditions JSONB,
  actions JSONB,  -- ordered list
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE automation_runs (
  id BIGSERIAL PRIMARY KEY,
  automation_id INT REFERENCES automations(id),
  trigger_data JSONB,
  status VARCHAR(20),  -- 'success', 'failed', 'skipped'
  error TEXT,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## SMM modul jadvallari

```sql
-- Brands
CREATE TABLE brands (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  industry VARCHAR(100),
  description TEXT,
  logo_url VARCHAR(500),
  brand_colors JSONB,
  brand_voice JSONB,
  target_audience JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge base (with pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_base (
  id SERIAL PRIMARY KEY,
  brand_id INT REFERENCES brands(id) ON DELETE CASCADE,
  section INT,  -- 1..8
  content TEXT,
  metadata JSONB,
  embedding vector(1536),  -- OpenAI text-embedding-3-small
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON knowledge_base USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_brand_section ON knowledge_base(brand_id, section);

-- Social accounts
CREATE TABLE social_accounts (
  id SERIAL PRIMARY KEY,
  brand_id INT REFERENCES brands(id) ON DELETE CASCADE,
  platform VARCHAR(20),  -- 'instagram', 'facebook', 'telegram', 'youtube'
  account_id VARCHAR(200),
  account_name VARCHAR(200),
  access_token_encrypted TEXT,  -- AES-256 encrypted
  refresh_token_encrypted TEXT,
  expires_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  last_sync_at TIMESTAMPTZ
);

-- Posts
CREATE TABLE posts (
  id SERIAL PRIMARY KEY,
  brand_id INT REFERENCES brands(id),
  type VARCHAR(20),  -- 'post', 'reels', 'story', 'video', 'short'
  status VARCHAR(20),  -- 'draft', 'scheduled', 'pending_approval', 'approved', 'published', 'failed'
  title VARCHAR(300),
  content TEXT,
  hashtags TEXT[],
  media JSONB,  -- [{ "type": "image", "url": "..." }]
  platforms TEXT[],  -- ['instagram', 'telegram']
  scheduled_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  publish_mode VARCHAR(20),  -- 'auto', 'manual'
  created_by INT,
  approved_by INT,
  approved_at TIMESTAMPTZ,
  metadata JSONB,  -- ai_prompts, ai_model_used, ...
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Post variants (3 ta variant)
CREATE TABLE post_variants (
  id SERIAL PRIMARY KEY,
  post_id INT REFERENCES posts(id) ON DELETE CASCADE,
  variant_letter VARCHAR(1),  -- 'A', 'B', 'C'
  content TEXT,
  hashtags TEXT[],
  is_selected BOOLEAN DEFAULT FALSE
);

-- Post metrics
CREATE TABLE post_metrics (
  id SERIAL PRIMARY KEY,
  post_id INT REFERENCES posts(id),
  platform VARCHAR(20),
  reach INT,
  impressions INT,
  likes INT,
  comments INT,
  shares INT,
  saves INT,
  clicks INT,
  engagement_rate NUMERIC(5,2),
  fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content plans
CREATE TABLE content_plans (
  id SERIAL PRIMARY KEY,
  brand_id INT REFERENCES brands(id),
  name VARCHAR(200),
  starts_at DATE,
  ends_at DATE,
  goals JSONB,
  topics JSONB,
  format_distribution JSONB,
  status VARCHAR(20),  -- 'draft', 'active', 'completed'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Brand assets
CREATE TABLE brand_assets (
  id SERIAL PRIMARY KEY,
  brand_id INT REFERENCES brands(id) ON DELETE CASCADE,
  type VARCHAR(20),  -- 'logo', 'image', 'video', 'template', 'font'
  name VARCHAR(200),
  file_url VARCHAR(500),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Reklama modul jadvallari

```sql
-- Campaigns
CREATE TABLE campaigns (
  id SERIAL PRIMARY KEY,
  platform VARCHAR(20),  -- 'meta', 'google', 'telegram'
  external_id VARCHAR(100),
  name VARCHAR(300),
  objective VARCHAR(50),
  status VARCHAR(20),
  daily_budget_uzs BIGINT,
  total_budget_uzs BIGINT,
  starts_at TIMESTAMPTZ,
  ends_at TIMESTAMPTZ,
  ai_optimization_mode VARCHAR(20),  -- 'off', 'recommendations', 'auto', 'full_ai'
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ad sets
CREATE TABLE ad_sets (
  id SERIAL PRIMARY KEY,
  campaign_id INT REFERENCES campaigns(id) ON DELETE CASCADE,
  external_id VARCHAR(100),
  name VARCHAR(300),
  audience_id INT,
  budget_uzs BIGINT,
  bid_strategy VARCHAR(50),
  status VARCHAR(20)
);

-- Ads
CREATE TABLE ads (
  id SERIAL PRIMARY KEY,
  ad_set_id INT REFERENCES ad_sets(id) ON DELETE CASCADE,
  external_id VARCHAR(100),
  creative_id INT,
  copy_text TEXT,
  cta VARCHAR(50),
  destination_url VARCHAR(500),
  status VARCHAR(20),
  metrics JSONB,  -- impressions, clicks, ctr, cpl, ...
  metrics_updated_at TIMESTAMPTZ
);

-- Audiences
CREATE TABLE audiences (
  id SERIAL PRIMARY KEY,
  type VARCHAR(20),  -- 'saved', 'lookalike', 'custom', 'ai_optimized'
  name VARCHAR(200),
  config JSONB,  -- platform-specific
  size_estimate INT,
  external_ids JSONB,  -- per-platform IDs
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead forms
CREATE TABLE lead_forms (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  fields JSONB,
  design JSONB,
  spam_filter_enabled BOOLEAN DEFAULT TRUE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leads
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  form_id INT REFERENCES lead_forms(id),
  campaign_id INT REFERENCES campaigns(id),
  contact_id INT REFERENCES contacts(id),  -- linked CRM contact
  data JSONB,
  is_spam BOOLEAN DEFAULT FALSE,
  status VARCHAR(20),  -- 'new', 'qualified', 'converted', 'rejected'
  utm_source VARCHAR(100),
  utm_campaign VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Landing pages
CREATE TABLE landing_pages (
  id SERIAL PRIMARY KEY,
  template_id INT,
  name VARCHAR(200),
  slug VARCHAR(100) UNIQUE,
  content JSONB,
  meta JSONB,  -- SEO
  is_published BOOLEAN DEFAULT FALSE,
  views INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Inbox modul jadvallari

```sql
-- Conversations
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  channel VARCHAR(20),  -- 'instagram', 'facebook', 'telegram', 'site_widget', 'sms', 'whatsapp'
  external_id VARCHAR(200),  -- platform-specific
  contact_id INT REFERENCES contacts(id),
  status VARCHAR(20),  -- 'open', 'pending', 'closed', 'spam'
  priority VARCHAR(20),  -- 'low', 'normal', 'high', 'urgent'
  assignee_id INT,
  sentiment VARCHAR(20),  -- 'positive', 'neutral', 'negative', 'urgent'
  sentiment_score INT,  -- 0-100
  last_message_at TIMESTAMPTZ,
  sla_due_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_status ON conversations(status, last_message_at DESC);

-- Messages
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id INT REFERENCES conversations(id) ON DELETE CASCADE,
  external_id VARCHAR(200),
  direction VARCHAR(10),  -- 'inbound', 'outbound'
  sender_type VARCHAR(20),  -- 'contact', 'user', 'ai_auto', 'system'
  sender_id INT,
  content TEXT,
  attachments JSONB,
  is_read BOOLEAN DEFAULT FALSE,
  ai_metadata JSONB,  -- sentiment, confidence, suggested_response
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Templates
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200),
  hashtag VARCHAR(50),
  language VARCHAR(10),
  content TEXT,
  variables JSONB,
  category VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Hisobotlar modul jadvallari

```sql
-- Anomalies
CREATE TABLE anomalies (
  id SERIAL PRIMARY KEY,
  type VARCHAR(50),
  severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
  metric VARCHAR(100),
  expected_value NUMERIC,
  actual_value NUMERIC,
  deviation NUMERIC,
  ai_explanation TEXT,
  ai_recommendation TEXT,
  is_acknowledged BOOLEAN DEFAULT FALSE,
  detected_at TIMESTAMPTZ DEFAULT NOW()
);

-- Goals (OKR)
CREATE TABLE goals (
  id SERIAL PRIMARY KEY,
  parent_id INT REFERENCES goals(id),  -- daraja: company > department > user
  level VARCHAR(20),  -- 'company', 'department', 'user'
  owner_id INT,
  title VARCHAR(300),
  description TEXT,
  period_type VARCHAR(20),  -- 'quarter', 'year'
  starts_at DATE,
  ends_at DATE,
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE key_results (
  id SERIAL PRIMARY KEY,
  goal_id INT REFERENCES goals(id) ON DELETE CASCADE,
  title VARCHAR(300),
  metric VARCHAR(100),
  target_value NUMERIC,
  current_value NUMERIC,
  position INT
);

-- Scheduled reports
CREATE TABLE scheduled_reports (
  id SERIAL PRIMARY KEY,
  template_code VARCHAR(50),
  recipients JSONB,  -- emails, telegram_ids
  schedule VARCHAR(50),  -- cron expression
  format VARCHAR(20),  -- 'pdf', 'excel'
  config JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  last_sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI buddy conversations
CREATE TABLE ai_buddy_conversations (
  id SERIAL PRIMARY KEY,
  user_id INT,
  title VARCHAR(300),
  messages JSONB,
  tokens_used INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Integratsiya modul jadvallari

```sql
-- Active integrations
CREATE TABLE integrations (
  id SERIAL PRIMARY KEY,
  catalog_id INT,  -- references public.integrations_catalog
  config JSONB,
  credentials_encrypted TEXT,  -- AES-256
  status VARCHAR(20),  -- 'active', 'paused', 'error'
  last_sync_at TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sync jobs
CREATE TABLE sync_jobs (
  id BIGSERIAL PRIMARY KEY,
  integration_id INT REFERENCES integrations(id),
  type VARCHAR(50),  -- 'full', 'incremental'
  status VARCHAR(20),  -- 'running', 'success', 'failed'
  records_processed INT,
  errors JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Webhooks
CREATE TABLE webhooks (
  id SERIAL PRIMARY KEY,
  url VARCHAR(500),
  events TEXT[],  -- subscribed events
  secret_encrypted TEXT,  -- HMAC secret
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE webhook_deliveries (
  id BIGSERIAL PRIMARY KEY,
  webhook_id INT REFERENCES webhooks(id),
  event VARCHAR(100),
  payload JSONB,
  status_code INT,
  response_body TEXT,
  attempt INT DEFAULT 1,
  delivered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backups
CREATE TABLE backups (
  id SERIAL PRIMARY KEY,
  type VARCHAR(20),  -- 'auto', 'manual'
  storage_type VARCHAR(20),  -- 'server', 's3', 'gdrive', 'dropbox'
  size_bytes BIGINT,
  encryption_key_hint VARCHAR(100),
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Migration strategiyasi (Alembic)

### Multi-tenant migration

```python
# alembic/env.py
def run_migrations_online():
    # 1. Public schema migration
    run_public_migrations()
    
    # 2. Per-tenant schema migrations
    tenants = get_all_tenants()
    for tenant in tenants:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {tenant.schema_name}"))
            run_tenant_migrations(conn)
```

### Naming

`alembic/versions/2026_05_01_1430_add_ai_score_to_contacts.py`

### Rollback

Har migration `downgrade()` funksiyasi bilan, sinab ko'rilgan.

---

## Indexes umumiy ko'rinish

```sql
-- Contacts (CRM tez qidiruv)
CREATE INDEX idx_contacts_phone ON contacts(phone);
CREATE INDEX idx_contacts_assignee ON contacts(assignee_id);
CREATE INDEX idx_contacts_ai_score ON contacts(ai_score DESC);
CREATE INDEX idx_contacts_status ON contacts(status);

-- Deals
CREATE INDEX idx_deals_pipeline_stage ON deals(pipeline_id, stage_id);
CREATE INDEX idx_deals_assignee ON deals(assignee_id);
CREATE INDEX idx_deals_close_date ON deals(expected_close_date);

-- Activities
CREATE INDEX idx_activities_contact ON activities(contact_id, occurred_at DESC);
CREATE INDEX idx_activities_deal ON activities(deal_id, occurred_at DESC);

-- Posts
CREATE INDEX idx_posts_brand_status ON posts(brand_id, status);
CREATE INDEX idx_posts_scheduled ON posts(scheduled_at) WHERE status = 'scheduled';

-- Messages
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);

-- Audit log
CREATE INDEX idx_audit_user_created ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);

-- Knowledge base (vector search)
CREATE INDEX ON knowledge_base USING hnsw (embedding vector_cosine_ops);
```

---

## Tegishli fayllar

- [01-architecture.md](01-architecture.md) — Multi-tenancy detali
- [02-conventions.md](02-conventions.md) — DB naming
- [adrs/0002-multi-tenancy-strategy.md](adrs/0002-multi-tenancy-strategy.md)
