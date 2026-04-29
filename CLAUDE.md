# NEXUS AI — Claude Code uchun yo'riqnoma

> **Diqqat:** Bu fayl har Claude Code sessiyasi boshida birinchi navbatda o'qiladi.
> Loyihaning umumiy konteksti, qoidalari va konvensiyalari shu yerda.
> Agar shubha bo'lsa — bu yerga qayting.

---

## 🎯 Loyiha haqida (1 paragraf)

**NEXUS AI** — O'zbekiston bozori uchun mo'ljallangan multi-tenant SaaS platforma.
6 ta modul bir tizimda: **CRM, SMM, Reklama, Inbox, Hisobotlar, Integratsiyalar**.
Asosiy farqlovchi — **AI hamma joyda**: kontent yaratish, mijoz scoring, reklama
optimizatsiyasi, sentiment tahlili, biznes maslahat. To'liq spetsifikatsiya
`docs/SPECS.pdf` faylida (80 sahifa).

---

## 🏗 Texnologiyalar

**Backend:**
- Python 3.11+
- FastAPI (async, OpenAPI auto-docs)
- PostgreSQL 15+ (with pgvector)
- Redis 7+
- Celery (background tasks)
- SQLAlchemy 2 + Alembic
- Pydantic v2

**Frontend:**
- Next.js 14+ (App Router)
- TypeScript (strict mode)
- TailwindCSS + shadcn/ui (luxury theme)
- React Query (TanStack)
- Zustand (client state)
- react-hook-form + Zod

**AI:**
- Claude (asosiy — kontent, suhbat, kompleks reasoning)
- GPT-4o (backup + image generation)
- OpenAI Whisper (audio transkripsiya)
- OpenAI Embeddings (RAG)

**Infra:**
- Docker + Docker Compose (local dev)
- UzCloud (production — qonun talabi)
- GitHub Actions (CI/CD)
- Sentry (error tracking)

---

## 📂 Fayl tuzilishi

```
nexus-ai/
├── CLAUDE.md                  ← Bu fayl (har sessiyada o'qiladi)
├── README.md                  ← Boshlash bo'yicha qo'llanma
├── TODO.md                    ← Joriy sprint vazifalari
├── docs/
│   ├── SPECS.pdf              ← To'liq spetsifikatsiya (referens)
│   ├── 00-overview.md         ← Umumiy ko'rinish
│   ├── 01-architecture.md     ← Texnik arxitektura
│   ├── 02-conventions.md      ← Kod standartlari
│   ├── 03-design-system.md    ← UI/UX dizayn tili
│   ├── 04-database-schema.md  ← Ma'lumotlar bazasi
│   ├── 05-api-contracts.md    ← API kontraktlari
│   ├── 06-ai-strategy.md      ← AI integratsiya
│   ├── 07-security.md         ← Xavfsizlik
│   ├── modules/
│   │   ├── 00-foundation.md   ← Auth, RBAC, settings
│   │   ├── 01-crm.md
│   │   ├── 02-smm.md          ← Bosqich 1 — birinchi modul
│   │   ├── 03-ads.md
│   │   ├── 04-inbox.md
│   │   ├── 05-reports.md
│   │   └── 06-integrations.md
│   ├── roadmap/
│   │   ├── phase-0.md         ← Tayyorgarlik (joriy)
│   │   ├── phase-1.md         ← SMM MVP
│   │   ├── phase-2.md         ← CRM + Inbox
│   │   ├── phase-3.md         ← Reklama + Hisobotlar
│   │   └── phase-4.md         ← Integratsiyalar
│   ├── adrs/                  ← Architecture Decision Records
│   │   ├── 0001-monorepo-structure.md
│   │   ├── 0002-multi-tenancy-strategy.md
│   │   └── ...
│   └── glossary.md
├── prompts/                   ← Claude Code uchun tayyor promptlar
│   ├── starter.md             ← Birinchi sessiya
│   ├── new-feature.md         ← Yangi xususiyat qo'shish
│   ├── debug.md               ← Bug topish
│   └── review.md              ← Code review
├── apps/
│   ├── api/                   ← Backend (FastAPI)
│   ├── web/                   ← Frontend (Next.js)
│   └── widget/                ← Sayt widget (alohida server)
├── packages/
│   ├── shared-types/          ← Backend ↔ Frontend umumiy tiplar
│   └── ui/                    ← Umumiy UI komponentlar (kerak bo'lsa)
├── infra/
│   ├── docker-compose.yml     ← Local dev
│   ├── Dockerfile.api
│   └── Dockerfile.web
└── scripts/                   ← Dev skriptlar
```

---

## 📋 Loyihaning hozirgi holati

**Joriy bosqich:** Bosqich 0 — Tayyorgarlik

- [ ] Bosqich 0 — Tayyorgarlik (1-2 oy) ← **HOZIR**
- [ ] Bosqich 1 — MVP: SMM moduli (3-4 oy)
- [ ] Bosqich 2 — CRM + Inbox (3-4 oy)
- [ ] Bosqich 3 — Reklama + Hisobotlar (3-4 oy)
- [ ] Bosqich 4 — Integratsiyalar va kengaytirish (3-6 oy)

**Joriy sprint vazifalari:** `TODO.md` faylida.

---

## 📐 Asosiy konvensiyalar

### Til siyosati

| Joy | Til |
|---|---|
| UI matn | O'zbek lotin (asosiy), rus (qo'shimcha) |
| Kod identifierlar | English (camelCase / snake_case) |
| Kod commentlar | English |
| Hujjatlar (docs/) | O'zbek |
| Commit messages | English (conventional commits) |
| Database fields | English (snake_case) |
| API endpoints | English (kebab-case) |

### Commit konvensiyasi

[Conventional Commits](https://www.conventionalcommits.org/) standarti:

```
<type>(<scope>): <description>

[body]

[footer]
```

Type'lar: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.

Misol:
```
feat(crm): add AI scoring to contact card

- Calculate score on contact creation
- Update score hourly via Celery task
- Display badge on contact list

Closes #42
```

### Branch strategiyasi

- `main` — production-ready
- `develop` — joriy ishlanma
- `feature/<scope>-<description>` — yangi xususiyat
- `fix/<scope>-<description>` — bug fix
- `docs/<scope>` — hujjat o'zgarishi

### PR qoidalari

1. **Bitta xususiyat — bitta PR.** 500+ qator o'zgarish bo'lsa — bo'lib yubor.
2. **Test majburiy.** Yangi kod uchun unit + integration test.
3. **Hujjatni yangilash.** README, CLAUDE.md, modul spec — kerakli joyni yangila.
4. **Inson review qiladi.** Kritik joylarda (auth, billing, RBAC) — Tech Lead majburiy.

---

## 🔒 Multi-tenancy qoidalari

**Bu eng kritik bo'lim. Yodda tut!**

- Strategiya: **Schema-per-tenant** (PostgreSQL).
- Har request boshida `tenant_id` middleware'da ekstrakt qilinadi.
- DB so'rovlari **doim** joriy tenant schema'sida bajariladi.
- **Hech qachon** boshqa tenant ma'lumotini ko'rib bo'lmaydi.
- Shared resurslar (users, plans, integrations_catalog) faqat `public` schema'da.

Har yangi xususiyatda **avval shu savolni ber:**
> "Bu kod tenant kontekstini to'g'ri qabul qiladimi? Cross-tenant leak bormi?"

---

## 🤖 AI integratsiya qoidalari

1. **Multi-provider:** Claude asosiy → ishlamasa GPT-4o backup.
2. **Token cap:** har tenant uchun oylik limit. **Hech qachon limitsiz** AI chaqiruvi qilma.
3. **Cache-first:** bir xil so'rovlar 24 soat cache.
4. **Streaming UI:** uzun javoblar stream bo'lsin (UX yaxshilanadi).
5. **Confidence threshold:** Inbox auto-respond uchun 90%+ confidence.
6. **RAG:** mijoz ma'lumotlari pgvector'da, har AI chaqiruvida kontekst sifatida.
7. **Promptlar:** alohida fayllarda saqla (`apps/api/app/ai/prompts/*.txt`), kod ichida emas.

---

## ⚠ Inson nazorati shart bo'lgan joylar

Bu sohalarda Claude Code **avtonom emas** — har doim inson tasdiqlaydi:

- 💰 **Billing va to'lov logikasi** — pul bilan bog'liq har qator tekshiriladi
- 🔐 **Auth, encryption, RBAC** — xato qimmat va xavfli
- 🏢 **Multi-tenancy chegaralash** — bir tenant boshqasini ko'rmasligi shart
- 🤖 **AI prompt'lar** — mahsulot sifatini belgilaydi
- 🚀 **Production deploy** — har release inson tasdiqlaydi
- 🗑 **Mijoz ma'lumotlari o'chirish** — qaytarib bo'lmaydi
- 📡 **Tashqi API integratsiya** — Meta/Google reklama (real pul)

---

## 📖 Sessiya boshida nimani o'qish kerak

**Har doim:**
1. `CLAUDE.md` (bu fayl)
2. `TODO.md` — joriy vazifalar

**Vazifaga qarab:**
3. `docs/00-overview.md` — agar umumiy kontekst kerak bo'lsa
4. `docs/modules/<modul>.md` — konkret modul ustida ishlayotgan bo'lsang
5. `docs/04-database-schema.md` — DB o'zgarishlari uchun
6. `docs/05-api-contracts.md` — API qo'shyotgan bo'lsang
7. `docs/03-design-system.md` — UI ishlayotgan bo'lsang

**Yangi muammolar:**
8. `docs/adrs/` — yangi arxitekturaviy qaror qabul qilishdan oldin

---

## 🔄 Ish ketma-ketligi (har xususiyat uchun)

```
1. Spec o'qish              (docs/modules/...)
2. ADR yozish (kerak bo'lsa) (docs/adrs/...)
3. Test yozish (TDD)         (tests/...)
4. Implementatsiya
5. Test ishlatish
6. Hujjatni yangilash        (CLAUDE.md, modul spec)
7. Commit (conventional)
8. PR + review
9. TODO.md ni yangila
```

---

## 🚦 Boshlash bo'yicha tavsiyalar

**Yangi sessiyada birinchi xabar misoli:**

```
Bu — NEXUS AI loyihasi. Avval CLAUDE.md va TODO.md fayllarni o'qi,
keyin nimaga ishlayotganimizni tushuntir va men nimadan boshlashim
kerakligini ayt.
```

**Yangi xususiyat qo'shish uchun:**

```
prompts/new-feature.md shablonini o'qib, undagi savollarga javob beraman.
Keyin spec yozamiz va kod yozishni boshlaymiz.
```

**Bug topish uchun:**

```
prompts/debug.md shablonida muammo tasvirlangan. O'qi va tahlil qil.
```

---

## 🆘 Yordam

- Loyiha boshlig'i: [ismingiz]
- Tech Lead: [Tech Lead]
- To'liq spec: `docs/SPECS.pdf`
- Lug'at: `docs/glossary.md`
- Roadmap: `docs/roadmap/`

---

**So'nggi yangilanish:** 2026-04-29
**Versiya:** 1.0
