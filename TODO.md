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

- [x] **F1.** Next.js 16 init (TypeScript, Tailwind v4, App Router, src/) ✅ 2026-04-29
- [x] **F2.** Loyiha tuzilishi (app, components/{ui,shared,auth}, lib, hooks, stores) ✅ 2026-04-29
- [x] **F3.** Luxury theme (gold/charcoal/cream) + custom UI primitives (Button, Input, Card, FormField, Label) ✅ 2026-04-29
- [x] **F4.** Asosiy layout — Sidebar (modul ro'yxati skeleti) + Header + ProtectedRoute HOC ✅ 2026-04-29
- [x] **F5.** Auth sahifalari: /, /login, /register, /verify-phone (Suspense bilan), /forgot-password ✅ 2026-04-29
- [x] **F6.** API client (axios + JWT interceptor + 401→refresh→retry, Zustand persist store, React Query) ✅ 2026-04-29

### DevOps (infra/)

- [x] **D1.** docker-compose.yml (postgres pgvector, redis, api, pgadmin) ✅ 2026-04-29
- [x] **D2.** Dockerfile.api + Dockerfile.web (multi-stage, standalone Next.js) ✅ 2026-04-29
- [x] **D3.** .env.example (root + apps/web/.env.example) ✅ 2026-04-29
- [x] **D4.** Pre-commit hooks (ruff, prettier, conventional commits) ✅ 2026-04-29
- [x] **D5.** GitHub Actions CI: api job + web job (lint, type-check, test, build) ✅ 2026-04-29

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

**Backend:** ✅ B1-B6
**DevOps:** ✅ D1, D3, D4, D5 (D2 Dockerfile.api)
**Smoke test:** docker compose, alembic upgrade, uvicorn, /health 200, /auth/register 201
**Test natijasi:** 26 passed, 82.57% coverage, ruff toza, mypy toza

## 📈 Sprint 1.1 progress (2026-04-30) — Bosqich 1 boshlandi

**Backend:** Brand + BrandMembership + TenantIntegration modellari, har tenant schema'ga DDL avtomatik bootstrap, Fernet (AES) bilan shifrlangan creditallar saqlash, 9 ta provider katalogi (anthropic/openai/telegram/meta/youtube/google_oauth/eskiz/sendgrid), `smm.read|write|publish` + `integrations.write` permissions, brands CRUD + set-default endpoint, integrations connect/disconnect endpoint, audit log integratsiyasi. **8 ta yangi test (brands lifecycle + integrations) yashil.**

**Frontend:** Types + `smm-api` + `integrations-api` clientlar, `/smm` dashboard sahifasi (brendlar listi, ulanishlar holati, yo'l xaritasi), `/smm/brands` to-liq CRUD UI (rang tanlash, til, ovoz va uslub, asosiy brend belgisi), `/settings/integrations` provayder kartochkalari + connect modal (eye/eye-off password toggle, masked qiymatlar, kategoriya bo'yicha guruhlash). Sidebar'da SMM va Integratsiyalar yoqilgan. **22 sahifa pre-rendered.**

**Arxitektura qarori:** Foydalanuvchi tokenlari `/settings/integrations` orqali UI'dan kiritiladi. Tizim mock providerlar bilan to'liq ishlay oladi — real API kalitlar Sprint davomida bosqichma-bosqich ulanadi. Tashqi xizmat creditallari hech qachon `.env`ga yozilmaydi (multi-tenant SaaS standart).

---

## 🎉 Bosqich 0 yakunlandi (2026-04-30)

Sprint 1–5 tugadi. Tizim production'ga deploy qilishga tayyor (server creditallar so'ng).

**Yakuniy son raqamlar:**
- Backend: 61 testlar (unit + integration), 86.34% coverage, ruff + mypy strict toza
- Frontend: 8 unit testlar, 20 sahifa pre-rendered, lint/type-check/build toza
- DB: 14 jadval (public + tenant template), schema-per-tenant DDL bootstrap
- Endpointlar: 9 router (auth, tenant, users, roles, departments, onboarding, tasks, 2fa, api-keys, notifications, billing)
- 5 standart rol + 40+ permissions
- WebSocket bildirishnomalar, JWT + 2FA, API kalit tizimi
- Billing: 18 narx + 4 paket, PDF Invoice, grace period state machine

**Kelgusi (Bosqich 1):** SMM MVP — brendlar, knowledge_base (pgvector), ijtimoiy akkauntlar, AI kontent generatsiya

---

## 📈 Sprint 5 progress (2026-04-30)

**Backend:** Plan/Subscription/Invoice/AiUsage modellari + DDL har tenant schema'da; pricing modul (6 modul × 3 tarif × paketlar × yillik chegirma); billing_service (start_trial, change_subscription, mark_paid) + grace period state machine (active/banner/read_only/locked); reportlab orqali PDF Invoice generatsiya; Jinja2 + mock email provider; full billing endpoints (catalog, status, quote, subscribe, invoices, pdf, mark-paid). 61 tests passed (21 yangi: 5 pricing, 5 grace state, 8 billing integration), 86.34% coverage.

**Frontend:** `/settings/billing` to'liq sahifa — joriy tarif kartochkasi + paket/modul/tarif/davr tanlovi + jonli quote (chegirma + AI cap) + invoice tarixi (PDF download + mark-paid), trial start tugmasi. `<GraceBanner>` komponenti app layout'ga qo'shildi — 4 holat (active yashirin, banner sariq ogohlantirish, read_only kuchaytirilgan, locked qizil bloklash) bilan to'lovga yo'naltiruvchi CTA. 20 sahifa pre-rendered.

**DevOps:** `infra/docker-compose.prod.yml` (postgres, redis password-protected, api+web GHCR'dan, nginx); `infra/nginx.conf` (TLS 1.2/1.3, HSTS, WebSocket upgrade, /api proxy); `.github/workflows/deploy.yml` (build → GHCR push → SSH staging/production rollout, manual production approval).

**Hujjatlar:** README to'liq qayta yozildi — quick start, project structure, tech stack, **production deploy guide** (UzCloud + Cloudflare + Sentry + Let's Encrypt), Sprint 5 yangiliklari, Bosqich 1 keyingi qadamlar.

**Note:** Real SMTP/SendGrid, OAuth (Google + Telegram) Bosqich 1 ga ko'chirildi — kerakli credentials kelganda yoqamiz.

---

## 📈 Sprint 4 progress (2026-04-29)

**Backend:** Tasks model + DDL (status, priority, assignee, due dates, polymorphic related_to), CRUD endpoints with status/assignee filters, auto-notification on assign. **2FA** (TOTP via pyotp) — setup → QR data URL → backup codes → verify-and-enable → disable. **API keys** — generate `nxa_…` token, hash store, scopes, rate limit, revoke. **Notifications** — DB persist + in-process pub/sub broker + WebSocket `/api/v1/notifications/ws?token=...` + REST list/mark-all-read. **40 tests passed, 85.05% coverage.**

**Frontend:** `/tasks` Kanban (5 status columns) + List view with create form, status dropdown per card, delete on hover. `<Header>` notification bell with unread badge + dropdown + mark-all-read. WebSocket toast on incoming notifications (auto-reconnect). `/settings/security` — full 2FA setup flow with QR display + backup codes. `/settings/api-keys` — create/list/revoke with one-time plaintext display + clipboard copy. **20 routes pre-rendered, lint + type-check + build green.**

**Note:** Email Jinja2 templates va OAuth (Google + Telegram) Sprint 5 ga ko'chirildi — credentials kelganda yoqamiz.

---

## 📈 Sprint 3 progress (2026-04-29)

**Backend:** Tenant-scoped models (Department, Role, UserMembership, Notification, AuditLog, ApiKey), schema-per-tenant DDL bootstrap on register, 5 standard roles seeded, Owner membership auto-attached, RBAC permission registry (40+ permissions), `require_permission` FastAPI dep, endpoints for `/tenant`, `/users`, `/roles`, `/departments`, `/onboarding`, audit log writer. **34 tests passed, 87.05% coverage.**

**Frontend:** Onboarding wizard (7 qadam: welcome → company → departments → users → modules → plan → done), Settings shell with 10 sub-pages (`/settings/profile`, `/settings/company`, `/settings/departments`, `/settings/users`, plus 6 placeholders), `<Can permission>` component with `usePermissions` hook (React Query backed), full department CRUD UI (list, create, delete), tenant company name/industry edit. **18 sahifa pre-rendered, lint + type-check + 8 tests yashil.**

**Note:** OAuth (Google + Telegram) `/auth/oauth/*` endpointlari Sprint 4 ga ko'chirildi — credentials kelganda yoqamiz.

---

## 📈 Sprint 2 progress (2026-04-29)

**Frontend:** ✅ F1-F6 — Next.js 16, Tailwind v4, luxury theme, auth flow, layout, API client
**DevOps:** ✅ Dockerfile.web (standalone), web service in compose, frontend CI job

**Build natijasi:**
- `pnpm lint` → ✓
- `pnpm type-check` → ✓
- `pnpm test` → 8 passed (utils)
- `pnpm build` → ✓ 9 sahifa pre-rendered (`/`, `/login`, `/register`, `/verify-phone`, `/forgot-password`, `/dashboard`)
- `pnpm format:check` → ✓

**Sahifalar:**
- `/` — landing (NEXUS AI brending, CTA tugmalar)
- `/login` — email yoki telefon + parol
- `/register` — kompaniya nomi, soha, telefon (+998), email, parol, shartnoma
- `/verify-phone` — 6 raqamli SMS kod, 5 daqiqa taymer
- `/forgot-password` — placeholder Sprint 3 uchun
- `/dashboard` — protected, ProtectedRoute HOC bilan

---

**Oxirgi yangilanish:** 2026-04-29
