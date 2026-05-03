# TODO — Joriy Holat Va Ish Rejasi

> Har sessiyada shu fayl real holatga moslab yangilanadi.
> Eski sprint loglar arxiv sifatida git tarixida qoladi; bu fayl esa hozirgi ishni boshqaradi.

---

## Joriy Holat

**Sana:** 2026-05-03  
**Asosiy bosqich:** Bosqich 1 — SMM MVP hardening (Foundation 100% yopildi)  
**Amaldagi kod holati:** Foundation barcha qarzlari yopilgan; SMM ancha oldinga ketgan; CRM/Inbox/Ads/Reports/Marketplace prototiplari mavjud.  
**Joriy maqsad:** SMM MVP'ni production-ready holatga keltirish va real provider integratsiyalari (IG/FB/Eskiz/SMTP).

### Oxirgi Tekshiruv

- Backend testlar: `192 passed` (10 yangi Foundation-close test qo‘shildi).
- Frontend type-check, lint, build: o‘tgan.
- Foundation yakuniy yopilish bosqichida qo‘shilgan: audit GET, notification preferences, user sessions table + login/refresh/logout wiring, real Eskiz SMS adapter, real SMTP email adapter, Google + Telegram OAuth (env-driven mock fallback).
- UI to‘liq yopilgan: Settings/users (invite/edit/delete + roles CRUD), Settings/audit (jadval), Settings/notifications (kanal × kategoriya matritsa + indamas vaqt), Settings/security (faol sessiyalar list/revoke), Login (Google + Telegram tugmalar mock-prompt rejimida).

---

## Tugagan Yoki Ishlaydigan Qismlar

### Foundation

- [x] FastAPI backend skeleti, async SQLAlchemy, Alembic public schema.
- [x] Schema-per-tenant bootstrap va tenant DDL.
- [x] Auth: register, phone verify, login, refresh, logout.
- [x] JWT tenant context middleware.
- [x] RBAC permission registry va 5 standart rol.
- [x] Departments, tasks, notifications, 2FA, API keys.
- [x] Billing catalog, subscription, invoice, PDF, grace state.
- [x] Docker, production compose, nginx, GitHub Actions deploy skeleti.

### SMM

- [x] Brand CRUD va default brand.
- [x] Tenant integrations credentials encryption.
- [x] Knowledge base text/file ingest, chunking, pgvector search.
- [x] AI content draft generation, token usage tracking, RAG prompt context.
- [x] Telegram, Meta, YouTube social account link/test/read flows.
- [x] Posts: draft/schedule/publish-now/retry/cancel.
- [x] SMM analytics overview/timeseries/top posts/insights.
- [x] Web UI: `/smm`, `/smm/brands`, `/smm/knowledge-base`, `/smm/ai-studio`, `/smm/social`, `/smm/posts`, `/smm/calendar`, `/smm/analytics`.

### CRM / Inbox / Ads / Reports / Marketplace Prototiplari

- [x] CRM contacts, activities, AI score, deals, pipeline/stages, forecast.
- [x] Inbox conversations, messages, manual ingest, draft reply, auto-reply config.
- [x] Ads accounts/campaigns/metrics with mock sync and draft creation.
- [x] Reports overview, funnel, cohorts, saved reports, CSV export.
- [x] Marketplace catalog, inbound/outbound webhooks, HMAC, delivery log, mock sync.

---

## Hozir Yopilayotgan Ishlar

- [x] Backend ruff lint xatolarini yopish.
- [x] Backend ruff format qarzini yopish.
- [x] Frontend prettier format qarzini yopish.
- [x] Grace period dependency routerlarga ulash.
- [x] Grace period tuzatishidan keyin full backend testlarni qayta yuritish.
- [x] Frontend lint/type/test/buildni qayta yuritish.
- [x] README va roadmap fayllarini real holatga moslash.

---

## Boshlanmagan Yoki Tugallanmagan Muhim Qismlar

### Foundation Qarzlari (yopilgan)

- [x] Forgot password/reset password backend va UI oqimi.
- [x] Google OAuth va Telegram OAuth auth oqimlari (env-driven mock fallback bilan).
- [x] Real Eskiz SMS provider (token cache + 401 retry; SMS_MOCK=false bilan yoqiladi).
- [x] Real SMTP provider (asyncio.to_thread bilan smtplib; EMAIL_MOCK=false bilan yoqiladi).
- [x] Users invite/update/delete (backend + Settings/users invite modal + edit dialog + delete).
- [x] Custom role create/update/delete (backend + permission matritsa UI; system rollar himoyalangan).
- [x] Audit log UI (filtrlar bilan jadval + audit GET endpoint).
- [x] Notification settings UI (channel × category matritsa + indamas vaqt + Telegram chat ID).
- [x] Active sessions UI va session revoke (login refresh-token jti bilan persisting; logout va per-session DELETE).
- [x] Grace period UX banner (active/banner/read_only/locked) layoutga ulangan.

### SMM MVP Qarzlari

- [ ] Brand yaratish 5-step wizard.
- [ ] Knowledge Base 8 bo‘limli strukturaga keltirish.
- [ ] Knowledge Base import usullari: website parse, Instagram import, AI chat.
- [ ] AI Studio: 3 variant generatsiya, tezkor tahrir, AI chat.
- [ ] Hashtag generator.
- [ ] Reels/Story script generator.
- [ ] AI 30 kunlik kontent reja.
- [ ] Approval workflow.
- [ ] Brand assets CRUD/upload.
- [ ] IG/FB publishingni real credential/OAuth bilan production holatga keltirish.
- [ ] SMM analyticsga real platform metrics ingestion.

### CRM / Inbox Qarzlari

- [ ] CRM products catalog va SMM bilan sync.
- [ ] CRM automation builder.
- [ ] OnlinePBX integration.
- [ ] AmoCRM real import wizard.
- [ ] Inbox real webhook ingestion for Meta/Telegram/SMS.
- [ ] Site widget alohida server.
- [ ] Inbox SLA monitoring, handover, internal notes, templates.

### Ads / Reports / Marketplace Qarzlari

- [ ] Ads real Meta/Google account sync.
- [ ] Ads smart wizard 8 qadam.
- [ ] Campaign launch/pause/resume real platform calls.
- [ ] Lead forms, audiences, landing builder.
- [ ] Reports anomaly detector, AI Sherik, OKR, forecasting, scheduled reports.
- [ ] Public REST/GraphQL developer portal.
- [ ] Backup/restore, white-label, custom domain/email.
- [ ] 1C/Click/Payme/Uzum real connectorlar.

---

## Ishlash Tartibi

1. Avval CI tozaligi: lint, format, type-check, test, build.
2. Keyin hujjatlarni real kodga moslab borish.
3. Har katta tuzatishga kamida bitta test yoki mavjud test yangilanishi.
4. Reja bo‘yicha tugamagan ishni `TODO.md`da checkbox bilan yangilash.
5. Mock/prototype bo‘lgan joylar hujjatda aniq belgilansin.

---

## Keyingi Eng To‘g‘ri Ketma-ketlik

1. SMM MVP qarzlari: brand 5-step wizard + structured knowledge base + AI Studio 3-variant.
2. Real platform integratsiyalari: IG/FB OAuth bilan haqiqiy publishing, real platform metrics ingestion.
3. CRM/Inbox prototiplarini product scope bo‘yicha ajratish va automation builder.
4. Production deploy: UzCloud + Cloudflare + Sentry + smoke/load test.

> Bosqich 0 (Foundation) endi 100% yopildi. Keyingi sessiyalar Bosqich 1 ga to‘liq fokus.
