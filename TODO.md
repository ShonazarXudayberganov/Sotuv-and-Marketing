# TODO — Joriy sprint vazifalari

> Bu fayl har Claude Code sessiyasida o'qiladi.
> Joriy bosqich va sprint vazifalari shu yerda.
> Ishlash davomida yangilab boring.

---

## 📍 Joriy holat

**Bosqich:** 0 — Tayyorgarlik (Foundation)
**Sprint:** 1 — Repository setup va texnik fundament
**Sprint davri:** 2 hafta
**Boshlangan:** 2026-04-29

---

## ✅ Sprint 1 vazifalari

### Backend (apps/api/)

- [ ] **B1.** Poetry init va asosiy paketlar
  - FastAPI, uvicorn, Pydantic v2
  - SQLAlchemy 2, Alembic, asyncpg
  - Redis, Celery
  - pytest, pytest-asyncio, httpx
  - ruff, mypy

- [ ] **B2.** Loyiha tuzilishi
  ```
  apps/api/
  ├── app/
  │   ├── core/        # config, security, db
  │   ├── api/         # endpoints
  │   ├── models/      # SQLAlchemy models
  │   ├── schemas/     # Pydantic schemas
  │   ├── services/    # business logic
  │   ├── ai/          # AI integrations
  │   └── main.py
  ├── tests/
  ├── alembic/
  └── pyproject.toml
  ```

- [ ] **B3.** Database ulanish
  - Async SQLAlchemy session
  - Alembic migratsiyalar setup
  - Health check endpoint

- [ ] **B4.** Multi-tenancy middleware
  - Tenant_id ekstrakt qilish (JWT'dan)
  - Schema almashtirish (PostgreSQL `SET search_path`)
  - Tenant yo'q bo'lsa — 404

- [ ] **B5.** Auth tizimi
  - User va Tenant modellar
  - JWT token (access + refresh)
  - Password hashing (bcrypt)
  - `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`

- [ ] **B6.** Test infra
  - pytest fixtures (test db, test client)
  - Birinchi auth testlari

### Frontend (apps/web/)

- [ ] **F1.** Next.js initialize
  ```bash
  npx create-next-app@latest --typescript --tailwind --app --src-dir
  ```

- [ ] **F2.** Loyiha tuzilishi
  ```
  apps/web/
  ├── src/
  │   ├── app/         # Next.js App Router
  │   ├── components/  # UI komponentlar
  │   ├── lib/         # utils, api client
  │   ├── hooks/       # custom hooks
  │   └── styles/      # global CSS
  ├── public/
  └── package.json
  ```

- [ ] **F3.** shadcn/ui o'rnatish
  - `npx shadcn-ui@latest init`
  - Luxury theme override (oltin + ko'mir + krem)

- [ ] **F4.** Asosiy layout
  - Sidebar component (kontent yo'q, faqat skeleton)
  - Header component
  - Main layout wrapper

- [ ] **F5.** Auth sahifalari
  - `/login` page
  - `/register` page
  - Auth context (React Query + Zustand)
  - Protected route HOC

- [ ] **F6.** API client
  - axios yoki fetch wrapper
  - Auth interceptor (JWT)
  - Error handler

### DevOps (infra/)

- [ ] **D1.** docker-compose.yml
  - PostgreSQL 15
  - Redis 7
  - Backend service
  - Frontend service
  - pgAdmin (dev)

- [ ] **D2.** Dockerfile.api va Dockerfile.web

- [ ] **D3.** .env.example
  - Barcha kerakli env variables (kalitlarsiz)

- [ ] **D4.** Pre-commit hooks
  - ruff (Python)
  - eslint, prettier (TypeScript)
  - Conventional commits validatsiya

- [ ] **D5.** GitHub Actions CI
  - Lint on PR
  - Test on PR
  - Build check

### Hujjatlar (docs/)

- [ ] **H1.** README.md to'ldirish (haqiqiy commands)
- [ ] **H2.** CLAUDE.md ni proyekt holatiga moslashtirish
- [ ] **H3.** Birinchi ADR yozish: 0001-monorepo-structure.md

---

## 🎯 Sprint 1 muvaffaqiyat mezonlari

Sprint 1 tugashi uchun quyidagilar ishlashi kerak:

1. ✅ `docker-compose up` — barcha servislar yuqotmasdan ishga tushadi
2. ✅ `POST /auth/register` — yangi kompaniya + Owner yaratiladi (yangi schema bilan)
3. ✅ `POST /auth/login` — JWT token qaytaradi
4. ✅ Frontend'da Login va Register sahifalari ishlaydi
5. ✅ Login bo'lgandan keyin protected sahifaga (dashboard placeholder) o'tadi
6. ✅ Sidebar va Header ko'rinadi (kontent yo'q)
7. ✅ Lint va testlar yashil
8. ✅ GitHub Actions CI yashil
9. ✅ README'da yozilgan boshlash instruksiyasi haqiqatan ishlaydi

---

## 📅 Keyingi sprint (preview)

**Sprint 2 (Bosqich 0 davomi):**
- Onboarding wizard (7 qadam)
- Sozlamalar sahifasi (Profil, Kompaniya)
- Bo'limlar va Xodimlar
- Rollar va imtiyozlar (RBAC)
- Bildirishnomalar tizimi (asosiy)
- Email + SMS shablon tizimi

**Sprint 3-4 (Bosqich 0 → Bosqich 1 o'tish):**
- Billing va Tarif tizimi
- AI integratsiya skeleti (Anthropic + OpenAI client)
- Brendlar (multi-brand) — SMM uchun tayyorgarlik

---

## ⚠ Eslatmalar

- Har vazifa **bir alohida PR**.
- Test yozmasangiz — vazifa tugamagan.
- Vazifa tugaganda: ✅ qo'ying va sana yozing (`B1 ✅ 2026-05-02`).
- Yangi vazifa kelsa — pastga qo'shing va ssalq qiling.
- Sprint oxirida: retrospektiv va keyingi sprint plan.

---

**Oxirgi yangilanish:** 2026-04-29
