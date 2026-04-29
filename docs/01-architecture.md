# 01 — Texnik arxitektura

> Tizim qanday qurilgan: stack, qatlamlar, ma'lumot oqimi, masshtablanish.

---

## Arxitektura tamoyillari

### 1. Modulyarlik
Har modul mustaqil sotiladi va deploy qilinadi. Mikroservis emas (boshlang'ich
murakkablik kerak emas), lekin **domain-driven monolit** — modullar orasida aniq
chegaralar.

```
app/modules/
├── crm/          # CRM modul
├── smm/          # SMM modul
├── ads/          # Reklama
├── inbox/        # Inbox
├── reports/      # Hisobotlar
└── integrations/ # Integratsiyalar
```

Har modul o'zining: models/, schemas/, services/, api/, tests/ ga ega.

### 2. Multi-tenancy
Bitta inframuzilma, ko'p mijozlar (kompaniyalar). Schema-per-tenant strategiyasi.

### 3. API-first
Barcha funksiyalar avval API sifatida quriladi. Frontend va Telegram bot shu
API'larni iste'mol qiladi.

### 4. AI-native
AI qo'shimcha emas, balki tizim yadrosi. Har modulda AI markaziy o'rinda.

### 5. Event-driven
Tizim ichidagi o'zgarishlar event'lar orqali tarqatiladi (webhook'lar, anomaliya
detektor, modullar orasidagi bog'lanishlar).

### 6. Local-first ma'lumotlar
Mijoz ma'lumotlari O'zbekiston serverlarida saqlanadi (qonun talabi). Faqat AI
uchun anonimlashtirilgan so'rovlar tashqi servislarga ketadi.

---

## Yuqori darajadagi diagramma

```
┌─────────────────────────────────────────────────────────────┐
│                      MIJOZ QURILMALARI                       │
│   Browser (Next.js)  ·  Telegram WebApp  ·  Sayt widget     │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS / WSS
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare / CDN / WAF                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                       Nginx (reverse proxy)                  │
└──────┬──────────────────────────────┬──────────────────────┘
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────────────────────┐
│  Next.js     │              │  FastAPI (Python)            │
│  (frontend)  │              │  ├─ /api/v1/* (REST)         │
│              │              │  ├─ /graphql                 │
│              │              │  └─ /ws/* (WebSocket)        │
└──────────────┘              └──┬──────────┬─────────┬─────┘
                                 │          │         │
                                 ▼          ▼         ▼
                         ┌──────────┐ ┌────────┐ ┌─────────┐
                         │PostgreSQL│ │ Redis  │ │ Celery  │
                         │+pgvector │ │ cache  │ │ workers │
                         └──────────┘ │ +queue │ └────┬────┘
                                      └────────┘      │
                                                      ▼
                                              ┌──────────────┐
                                              │ Tashqi API'lar│
                                              │ Claude, GPT,  │
                                              │ Meta, Google, │
                                              │ Eskiz, ...    │
                                              └──────────────┘
```

---

## Backend arxitekturasi (FastAPI)

### Layer struktura

```
Request → Middleware → Router → Service → Repository → Database
                          ↓
                    Pydantic schema validation
```

### Layer'lar

| Layer | Vazifa | Misol |
|---|---|---|
| **API (router)** | HTTP endpoint, request/response | `app/modules/crm/api/contacts.py` |
| **Schema (Pydantic)** | Validatsiya, serializatsiya | `app/modules/crm/schemas/contact.py` |
| **Service** | Business logic | `app/modules/crm/services/contact_service.py` |
| **Repository** | Database operatsiyalari | `app/modules/crm/repositories/contact_repository.py` |
| **Model (SQLAlchemy)** | DB jadval struktura | `app/modules/crm/models/contact.py` |

**Qoida:** API va Service layerlar bir-biridan bilmaydi. Service Repository orqali
DB bilan ishlaydi. Bu testlash va o'zgartirish uchun yaxshi.

### Async/sync

- **Endpoint'lar — async** (async def). FastAPI async-friendly.
- **DB sessiyalar — async** (asyncpg + SQLAlchemy 2 async).
- **Background tasklar — Celery** (sync, ammo workerlar parallel).
- **AI chaqiruvlar — async** (httpx async client).

### Konfiguratsiya

`app/core/config.py` — Pydantic Settings, .env'dan o'qiydi.

```python
class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    JWT_SECRET: SecretStr
    ANTHROPIC_API_KEY: SecretStr
    OPENAI_API_KEY: SecretStr
    # ...
```

---

## Frontend arxitekturasi (Next.js)

### Routing strategiyasi

App Router (Next.js 14+):

```
src/app/
├── (auth)/
│   ├── login/page.tsx
│   └── register/page.tsx
├── (app)/                  # Protected routes
│   ├── layout.tsx          # Sidebar + Header
│   ├── dashboard/page.tsx
│   ├── crm/
│   │   ├── page.tsx        # /crm
│   │   ├── contacts/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   └── deals/page.tsx
│   ├── smm/...
│   └── settings/...
└── api/                    # Next.js API routes (faqat BFF)
```

### Component architecture

```
src/components/
├── ui/                     # shadcn/ui primitivlari (button, input, card)
├── shared/                 # Loyiha bo'yicha umumiy (Sidebar, Header, ...)
├── crm/                    # CRM-spetsifik
├── smm/                    # SMM-spetsifik
└── ...
```

### State management

| Holat turi | Vosita | Misol |
|---|---|---|
| Server state | React Query | Mijozlar ro'yxati |
| Client state (global) | Zustand | Joriy brend, theme |
| URL state | Next.js searchParams | Filterlar, page |
| Form state | react-hook-form + Zod | Mijoz tahrirlash forma |

### Dizayn tizimi

Detallar: [03-design-system.md](03-design-system.md)

Asosiy: shadcn/ui + Tailwind CSS + custom luxury theme (oltin + ko'mir + krem
palette + Cormorant/Inter + Playfair sarlavhalar).

---

## Ma'lumotlar bazasi (PostgreSQL)

### Multi-tenancy: Schema-per-tenant

Har yangi kompaniya yaratilganda yangi schema avtomatik generatsiya qilinadi:

```sql
-- Kompaniya yaratish
CREATE SCHEMA tenant_akme_salon;
SET search_path TO tenant_akme_salon;

-- Bu schema'da hamma jadvallar yaratiladi
CREATE TABLE contacts (...);
CREATE TABLE deals (...);
-- ...
```

Application layer middleware'da:

```python
async def tenant_middleware(request, call_next):
    tenant = extract_tenant_from_jwt(request)
    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {tenant.schema_name}"))
    response = await call_next(request)
    return response
```

### Public schema (umumiy)

Faqat shared resurslar:

- `tenants` — kompaniyalar ro'yxati
- `users` — foydalanuvchilar (cross-tenant qidiruv uchun)
- `plans` — tarif rejalari
- `integrations_catalog` — integratsiyalar marketplace

### Tenant schema (har kompaniya uchun)

To'liq spec: [04-database-schema.md](04-database-schema.md)

Yuqori daraja:
- **Tizim asosi:** departments, roles, user_roles, notifications, tasks, audit_log
- **CRM:** contacts, deals, pipelines, products, activities, automations
- **SMM:** brands, knowledge_base, social_accounts, posts, content_plans
- **Reklama:** campaigns, ad_sets, ads, audiences, lead_forms, leads
- **Inbox:** conversations, messages, templates
- **Hisobotlar:** anomalies, goals, scheduled_reports
- **Integratsiyalar:** integrations, sync_jobs, webhooks, api_keys

### pgvector kengaytmasi

AI embedding'lari uchun:

```sql
CREATE EXTENSION vector;

-- Bilimlar bazasi RAG uchun
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    brand_id INT,
    section INT,
    content TEXT,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    ...
);

CREATE INDEX ON knowledge_base USING hnsw (embedding vector_cosine_ops);
```

### Migratsiyalar (Alembic)

- Har feature alohida migration
- Migration naming: `YYYY_MM_DD_HHMM_<short_description>.py`
- Multi-tenant migrations: shared (public schema) va per-tenant (har schema)
- Rollback har doim sinab ko'rilgan bo'lishi kerak

---

## AI infratuzilmasi

To'liq strategiya: [06-ai-strategy.md](06-ai-strategy.md)

Asosiy:

| Vazifa | Asosiy model | Backup |
|---|---|---|
| Kontent yaratish | Claude Sonnet 4 | GPT-4o |
| Sentiment (har xabar) | Claude Haiku 4.5 | GPT-4o-mini |
| AI Sherik | Claude Opus 4.7 | — |
| Embedding | OpenAI text-embedding-3 | — |
| Audio | Whisper API | — |
| Image gen | GPT image | DALL-E 3 |

### RAG (Retrieval-Augmented Generation)

```
User savol → Embed (OpenAI) → pgvector KNN search → Top-5 kontekst →
LLM (Claude) → javob
```

### Token boshqaruvi

- Har tenant uchun **oylik cap** (Start: 50k, Pro: 200k, Business: 1M)
- Cache 24 soat (bir xil so'rovlar)
- Streaming UI uchun
- Background AI (anomaliya monitor) — kunda 1 marta

---

## Caching strategiyasi (Redis)

| Cache turi | TTL | Misol |
|---|---|---|
| API response cache | 5-60 daq | GET /reports/dashboard |
| AI response cache | 24 soat | Bir xil promptga javob |
| Session | 30 kun | JWT refresh |
| Rate limit | 1 daq window | Per IP, per tenant |
| Pub/Sub | — | Real-time inbox xabarlari |

---

## Background tasks (Celery)

Celery workerlar quyidagilarni bajaradi:

- AI generatsiya (uzun, 10-30 sek)
- Sync ishlari (1C, AmoCRM)
- Email/SMS yuborish
- Anomaliya monitor (kunlik)
- Hisobot generatsiya (PDF, Excel)
- Webhook delivery (retry bilan)
- Cleanup (eski log, expired backup)

```
Beat scheduler → Celery queue → Workers → Result backend (Redis)
```

---

## Real-time (WebSocket)

FastAPI WebSocket — Inbox uchun. Asosiy.

```
Mijoz brauzeri ←─ WSS ─→ FastAPI WS endpoint ←─ Redis pub/sub
                                                      ↑
                          Boshqa servis (xabar olganda) publish qiladi
```

Sayt widget esa **alohida server** (sizning tanlovingiz) — Mavqei 100+ saytdagi
trafikni alohida WebSocket pool bilan boshqaradi.

---

## Xavfsizlik qatlamlari

To'liq spec: [07-security.md](07-security.md)

1. **Network:** TLS 1.3, Cloudflare, DDoS, WAF
2. **Auth:** JWT (access+refresh), OAuth, 2FA, bcrypt 12
3. **Authz:** RBAC (5 standart rol + custom)
4. **Data:** Encryption at rest (AES-256), encrypted secrets
5. **Audit:** har muhim harakat log, 90 kun
6. **Compliance:** O'zbekiston PD qonuni, GDPR-ready

---

## Deployment va infra

### Local development

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: nexus_dev
  redis:
    image: redis:7-alpine
  api:
    build: ./apps/api
    depends_on: [postgres, redis]
  web:
    build: ./apps/web
    depends_on: [api]
```

### Production (UzCloud)

- Kubernetes cluster (3+ node)
- Managed PostgreSQL (high availability)
- Managed Redis
- Object storage (rasm, fayl)
- CDN (rasm yetkazib berish)
- Backup avtomatik (har kun 02:00)

### CI/CD pipeline

```
PR → Lint + Test → Build → Deploy to staging → E2E test → 
  → Manual approve → Deploy to production
```

---

## Masshtablanish strategiyasi

**Boshlang'ich (50-500 mijoz):**
- Single PostgreSQL instance (read replica keyin)
- Backend horizontal scaling (Kubernetes pods)
- Redis cluster (3 node)

**O'rta (500-5000 mijoz):**
- PostgreSQL — primary + 2 read replicas
- Yirik tenant'lar uchun alohida database
- ClickHouse — analytics uchun (Reports modul)

**Yirik (5000+):**
- Sharding (tenant_id bo'yicha)
- Mikroservis migratsiya (avval Inbox real-time)
- CDN — har region uchun

---

## Tahlil va monitoring

- **Sentry** — error tracking
- **Grafana + Prometheus** — performance metrics
- **PostgreSQL slow query log**
- **AI cost dashboard** — har tenant per-day token sarfi
- **Custom alerts:** SLA buzilish, AI cap yetishi, error rate spike

---

## Tegishli hujjatlar

- [02-conventions.md](02-conventions.md) — Kod konvensiyalari
- [04-database-schema.md](04-database-schema.md) — DB schema to'liq
- [05-api-contracts.md](05-api-contracts.md) — API endpoints
- [06-ai-strategy.md](06-ai-strategy.md) — AI integratsiya
- [07-security.md](07-security.md) — Xavfsizlik
- [adrs/](adrs/) — Arxitekturaviy qarorlar
