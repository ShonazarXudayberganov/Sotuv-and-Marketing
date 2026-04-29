# NEXUS AI

> Biznesingizning intellektual markazi.
> O'zbekiston bozori uchun mo'ljallangan AI bilan boshqariladigan SaaS ekotizimi.

[![Build Status](#)](#)
[![Coverage](#)](#)
[![License](#)](#)

---

## Loyiha haqida

NEXUS AI — bu o'rta biznes (10-50 xodim) uchun mo'ljallangan multi-tenant SaaS
platforma. CRM, SMM, Reklama, Inbox, Hisobotlar va Integratsiyalar — bitta tizimda.

**To'liq spetsifikatsiya:** [docs/SPECS.pdf](docs/SPECS.pdf)

## Tezkor boshlash (Local development)

### Talablar

- Docker Desktop 4+
- Node.js 20+
- Python 3.11+
- Git

### O'rnatish

```bash
# 1. Repo'ni klon qiling
git clone https://github.com/<org>/nexus-ai.git
cd nexus-ai

# 2. Environment'ni tayyorlang
cp .env.example .env
# .env faylida API kalitlarni to'ldiring (Anthropic, OpenAI, Meta, ...)

# 3. Servislarni ishga tushiring
docker-compose up -d

# 4. Database migratsiyalarni bajaring
cd apps/api
poetry install
poetry run alembic upgrade head

# 5. Frontend'ni ishga tushiring
cd ../web
npm install
npm run dev

# 6. Brauzerda oching
# http://localhost:3000
```

### Birinchi foydalanuvchi yaratish

```bash
cd apps/api
poetry run python scripts/create_admin.py
```

## Loyiha tuzilishi

```
nexus-ai/
├── apps/
│   ├── api/          # Backend (FastAPI)
│   ├── web/          # Frontend (Next.js)
│   └── widget/       # Sayt widget (alohida server)
├── packages/
│   ├── shared-types/ # API/UI o'rtasidagi tiplar
│   └── ui/           # Umumiy komponentlar
├── docs/             # Hujjatlar (markdown)
├── infra/            # Docker, Kubernetes
└── scripts/          # Dev skriptlar
```

## Texnologiyalar

**Backend:** Python 3.11, FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy
**Frontend:** Next.js 14, TypeScript, TailwindCSS, shadcn/ui
**AI:** Claude, GPT-4o, Whisper
**Infra:** Docker, UzCloud (production)

## Hujjatlar

- [docs/00-overview.md](docs/00-overview.md) — Umumiy ko'rinish
- [docs/01-architecture.md](docs/01-architecture.md) — Texnik arxitektura
- [docs/02-conventions.md](docs/02-conventions.md) — Kod konvensiyalari
- [docs/03-design-system.md](docs/03-design-system.md) — UI dizayn tili
- [docs/modules/](docs/modules/) — Har modul spec'i
- [docs/roadmap/](docs/roadmap/) — Bosqichma-bosqich reja

## Claude Code bilan ishlash

Bu loyiha Claude Code (Opus 4.7) bilan ishlash uchun moslashtirilgan.

```bash
cd nexus-ai
claude
```

Birinchi sessiya:
```
CLAUDE.md va TODO.md fayllarni o'qi, hozirgi holatni tushuntir va
nimadan boshlash kerakligini ayt.
```

Tafsilotlar: [CLAUDE.md](CLAUDE.md) va [prompts/](prompts/)

## Litsenziya

Maxfiy. Faqat ichki foydalanish uchun.

## Komanda

- Owner: [ismingiz]
- Tech Lead: [TBD]
- Email: [email]
