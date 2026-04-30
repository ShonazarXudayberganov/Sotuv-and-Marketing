# NEXUS AI

> Biznesingizning intellektual markazi.
> O'zbekiston bozori uchun mo'ljallangan AI bilan boshqariladigan multi-tenant SaaS.

---

## Loyiha holati

**Joriy bosqich:** Bosqich 0 — Tayyorgarlik (Foundation) ✅ tugadi
**Keyingi:** Bosqich 1 — SMM MVP

| Sprint | Mazmun | Holat |
|---|---|---|
| 1 | Backend skelet + Auth + multi-tenancy | ✅ |
| 2 | Frontend skelet + auth UI + luxury theme | ✅ |
| 3 | Onboarding wizard, sozlamalar, RBAC, bo'limlar | ✅ |
| 4 | Vazifalar, 2FA, API kalitlar, real-time bildirishnomalar | ✅ |
| 5 | Billing, Invoice PDF, grace period, deploy skeleti | ✅ |

**Test natijasi:** 61 backend + 8 frontend, 86%+ coverage.

---

## Tezkor boshlash (Local development)

### Talablar
- Docker Desktop 4+
- Node.js 20+ va pnpm 10+
- Python 3.11+ va Poetry 2+
- Git

### Ishga tushirish

```bash
# 1. Repo'ni klon qiling
git clone git@github.com:ShonazarXudayberganov/Sotuv-and-Marketing.git
cd Sotuv-and-Marketing

# 2. Environment'ni tayyorlang
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local

# 3. Database va Redis'ni ishga tushiring
cd infra && docker compose up -d postgres redis

# 4. Backend'ni ishga tushiring
cd ../apps/api
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000

# 5. Yangi terminalda frontend'ni ishga tushiring
cd apps/web
pnpm install
pnpm dev
```

Brauzerda oching:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Tasdiqlash

```bash
# Backend
cd apps/api && poetry run pytest                  # 61 tests, 86% coverage
cd apps/api && poetry run ruff check .            # lint
cd apps/api && poetry run mypy app                # types

# Frontend
cd apps/web && pnpm test                          # 8 tests
cd apps/web && pnpm lint && pnpm type-check       # lint + types
cd apps/web && pnpm build                         # production build
```

---

## Loyiha tuzilishi

```
.
├── CLAUDE.md                ← Claude Code yo'riqnomasi (har sessiyada o'qiladi)
├── README.md                ← bu fayl
├── TODO.md                  ← joriy sprint vazifalari + progress
├── apps/
│   ├── api/                 ← FastAPI backend (Python 3.11+)
│   │   ├── app/
│   │   │   ├── core/        (config, security, db, deps, pricing, permissions, tenancy)
│   │   │   ├── api/v1/endpoints/  (auth, billing, departments, tasks, ...)
│   │   │   ├── models/      (SQLAlchemy 2 async)
│   │   │   ├── schemas/     (Pydantic v2)
│   │   │   ├── services/    (auth, billing, audit, twofa, notifications, email, ...)
│   │   │   ├── middleware/  (tenant context, grace period)
│   │   │   └── main.py
│   │   ├── alembic/         (DB migrations)
│   │   └── tests/           (unit + integration)
│   └── web/                 ← Next.js 16 frontend (TypeScript, Tailwind v4)
│       └── src/
│           ├── app/         (App Router: (auth), (app))
│           ├── components/  (ui/, shared/)
│           ├── hooks/       (use-auth, use-permissions, use-notifications)
│           ├── lib/         (api-client, auth-api, tenant-api, sprint4-api, billing-api)
│           └── stores/      (Zustand auth-store)
├── docs/                    ← Hujjatlar (Uzbek)
├── infra/
│   ├── docker-compose.yml         (local dev)
│   ├── docker-compose.prod.yml    (production)
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── nginx.conf
├── prompts/                 ← Claude Code shablonlari
└── .github/workflows/
    ├── ci.yml               (lint + test + build per PR)
    └── deploy.yml           (build → push GHCR → SSH deploy)
```

---

## Texnologiyalar

**Backend:** Python 3.11, FastAPI, SQLAlchemy 2 async, asyncpg, Alembic, Redis, Celery, Pydantic v2, pyotp (2FA), reportlab (PDF), Jinja2 (email)

**Frontend:** Next.js 16 (App Router), TypeScript strict, Tailwind v4, React Query, Zustand, react-hook-form + Zod, axios, sonner, lucide-react

**AI (Bosqich 1+):** Claude Sonnet 4 (asosiy), GPT-4o (backup), Whisper (audio), pgvector (RAG)

**Infra:** Docker, pgvector/postgres:15, redis:7, Nginx, GHCR, Cloudflare (prod), UzCloud (prod)

---

## Production deploy (UzCloud)

### 1. Talab qilinadigan creditallar

GitHub Secrets va GitHub Variables panelida o'rnating:

**Secrets:**
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
- `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`

**Variables:**
- `STAGING_URL` — masalan `https://staging.nexusai.uz`
- `PRODUCTION_URL` — masalan `https://nexusai.uz`
- `NEXT_PUBLIC_API_URL` — frontend build uchun

### 2. Server tayyorlash (har bir muhit uchun)

```bash
# UzCloud VM'da Docker, docker-compose o'rnatilgan bo'lishi kerak
ssh user@server
sudo mkdir -p /opt/nexus
sudo chown $USER /opt/nexus
cd /opt/nexus

# Compose va env fayllarni qo'ying
scp infra/docker-compose.prod.yml user@server:/opt/nexus/docker-compose.yml
scp infra/nginx.conf user@server:/opt/nexus/nginx.conf

# Production env (creditallar)
nano .env.production
# POSTGRES_USER=nexus
# POSTGRES_PASSWORD=<random 32 byte>
# POSTGRES_DB=nexus
# REDIS_PASSWORD=<random 32 byte>
# JWT_SECRET=<openssl rand -hex 32>
# ANTHROPIC_API_KEY=<...>
# OPENAI_API_KEY=<...>
# ESKIZ_EMAIL=<...>
# ESKIZ_PASSWORD=<...>
# SMS_MOCK=false
# CORS_ORIGINS=https://nexusai.uz
# NEXT_PUBLIC_API_URL=https://nexusai.uz

# SSL sertifikatini Let's Encrypt orqali oling (certbot)
sudo certbot certonly --standalone -d nexusai.uz -d www.nexusai.uz
mkdir -p /opt/nexus/certs
sudo cp /etc/letsencrypt/live/nexusai.uz/fullchain.pem /opt/nexus/certs/
sudo cp /etc/letsencrypt/live/nexusai.uz/privkey.pem /opt/nexus/certs/
```

### 3. Deploy

`main` branch'ga push avtomatik staging'ga deploy qiladi. Production'ga deploy uchun:

```
GitHub UI → Actions → Deploy → Run workflow → target=production
```

GitHub environment "production" protection rules orqali manual approve so'raydi.

### 4. Monitoring

- **Sentry:** `SENTRY_DSN` env'ga qo'shing — backend va frontend ikkalasi uchun
- **Cloudflare:** DNS + WAF + CDN. `nexusai.uz` Cloudflare orqali UzCloud IP'ga proxy qiling
- **UptimeRobot** yoki **BetterStack:** `/health` endpoint'ini har 5 daqiqada tekshirsin

---

## Sprint 5 yangiliklari (Bosqich 0 yakuni)

### Billing
- 6 modul × 3 tarif (Start/Pro/Business) = 18 narx
- 3 paket: Marketing Pack (-15%), Sales Pack (-15%), Full Ecosystem (-25%)
- Yillik chegirma: 6 oy −10%, 12 oy −20%
- AI token cap'lar: Start 50k, Pro 200k, Business 1M
- 7 kunlik bepul Pro+Full sinov

### Invoice
- Bank o'tkazma orqali to'lov
- PDF generatsiya (reportlab)
- Email orqali yuborish (mock provider — SMTP wireup credentialsiz)
- Admin tomonidan "to'langan" deb belgilash → subscription muddati avtomatik uzaytiriladi

### Grace period
- 0–7 kun: banner ogohlantirishi
- 7–30 kun: read-only (yangi yozishlar 402)
- 30–90 kun: locked
- 90+ kun: data arxivga (manual ish)

### Production-ready
- `infra/docker-compose.prod.yml` + `nginx.conf` + SSL
- `.github/workflows/deploy.yml` — build → GHCR → SSH deploy
- `staging` va `production` GitHub environments

---

## Bosqich 1 (Keyingi)

Sprint 1.1 — SMM MVP:
- Brendlar (multi-brand)
- Bilimlar bazasi (knowledge_base + pgvector)
- Ijtimoiy akkauntlar (Telegram, Instagram, Facebook, YouTube)
- AI kontent generatsiya (Claude Sonnet 4)
- Postlar (draft → schedule → publish)
- Kontent reja (oylik kalendar)

To'liq plan: [docs/roadmap/phase-1.md](docs/roadmap/phase-1.md)

---

## Hujjatlar

- [docs/00-overview.md](docs/00-overview.md) — Umumiy ko'rinish
- [docs/01-architecture.md](docs/01-architecture.md) — Texnik arxitektura
- [docs/02-conventions.md](docs/02-conventions.md) — Kod konvensiyalari
- [docs/03-design-system.md](docs/03-design-system.md) — UI dizayn tili
- [docs/04-database-schema.md](docs/04-database-schema.md) — DB schema
- [docs/05-api-contracts.md](docs/05-api-contracts.md) — API endpointlar
- [docs/06-ai-strategy.md](docs/06-ai-strategy.md) — AI integratsiya
- [docs/07-security.md](docs/07-security.md) — Xavfsizlik
- [docs/modules/](docs/modules/) — Har modul spec'i
- [docs/roadmap/](docs/roadmap/) — Bosqichma-bosqich reja
- [docs/SPECS.pdf](docs/SPECS.pdf) — To'liq mahsulot spetsifikatsiyasi (80 sahifa)

---

## Claude Code bilan ishlash

Yangi sessiyada:

```
Bu — NEXUS AI loyihasi. Avval CLAUDE.md va TODO.md fayllarni o'qi,
keyin nimaga ishlayotganimizni tushuntir va men nimadan boshlashim
kerakligini ayt.
```

Tafsilotlar: [CLAUDE.md](CLAUDE.md) va [prompts/](prompts/)

---

## Komanda

- Repo: https://github.com/ShonazarXudayberganov/Sotuv-and-Marketing
- Owner: ShonazarXudayberganov
- Email: shonazarx4@gmail.com

## Litsenziya

Maxfiy. Faqat ichki foydalanish uchun.
