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

- [x] **B1.** Poetry init va asosiy paketlar ✅ 2026-04-29
- [x] **B2.** Loyiha tuzilishi ✅ 2026-04-29
- [x] **B3.** Database ulanish (async SQLAlchemy + Alembic) ✅ 2026-04-29
- [x] **B4.** Multi-tenancy middleware (ASGI) ✅ 2026-04-29
- [x] **B5.** Auth tizimi (register, verify-phone, login, refresh, logout) ✅ 2026-04-29
- [x] **B6.** Test infra — 26 testlar yashil, 82.57% coverage ✅ 2026-04-29

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

- [x] **D1.** docker-compose.yml (postgres pgvector, redis, api, pgadmin) ✅ 2026-04-29
- [x] **D2.** Dockerfile.api (multi-stage) ✅ 2026-04-29 — Dockerfile.web Sprint 2 da
- [x] **D3.** .env.example ✅ 2026-04-29
- [x] **D4.** Pre-commit hooks (ruff, conventional commits) ✅ 2026-04-29 — eslint Sprint 2 da
- [x] **D5.** GitHub Actions CI (lint, mypy, test, conventional commits) ✅ 2026-04-29

### Hujjatlar (docs/)

- [ ] **H1.** README.md to'ldirish (haqiqiy commands) — Sprint 2 da
- [ ] **H2.** CLAUDE.md ni proyekt holatiga moslashtirish — Sprint 2 da
- [ ] **H3.** Birinchi ADR yozish: 0001-monorepo-structure.md — Sprint 2 da

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

## 📈 Sprint 1 progress (2026-04-29)

**Backend:** ✅ B1-B6 tugadi
**DevOps:** ✅ D1, D3, D4, D5 tugadi (D2: Dockerfile.web Sprint 2 da)
**Hujjatlar:** ⏳ H1-H3 Sprint 2 da

**Smoke test:**
- `docker compose up -d postgres redis` → ✓
- `alembic upgrade head` → ✓
- `uvicorn app.main:app` → ✓
- `GET /health` → `{"status":"ok","db":"ok"}` ✓
- `POST /api/v1/auth/register` → 201 + verification_id ✓

**Test natijasi:** 26 passed, 82.57% coverage, ruff toza, mypy toza

---

**Oxirgi yangilanish:** 2026-04-29
