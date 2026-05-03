# TODO — Joriy Holat Va Ish Rejasi

> Har sessiyada shu fayl real holatga moslab yangilanadi.
> Eski sprint loglar arxiv sifatida git tarixida qoladi; bu fayl esa hozirgi ishni boshqaradi.

---

## Joriy Holat

**Sana:** 2026-05-03  
**Asosiy bosqich:** Bosqich 1 — SMM MVP hardening  
**Amaldagi kod holati:** Foundation tugagan, SMM ancha oldinga ketgan, CRM/Inbox/Ads/Reports/Marketplace prototiplari ham boshlangan.  
**Joriy maqsad:** mavjud funksiyalarni CI-toza, hujjatga mos va real ishlaydigan MVP oqimiga keltirish.

### Oxirgi Tekshiruv

- Backend testlar: `202 passed`, coverage `83.55%`.
- Frontend testlar: `8 passed`.
- Frontend type-check/lint/build: o‘tgan.
- 2026-05-03 da format/lint qarzlari yopila boshlandi.
- Muhim tuzatish: billing grace enforcement API routerlarga ulanmoqda.

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

### Foundation Qarzlari

- [x] Forgot password/reset password backend va UI oqimi.
- [ ] Google OAuth va Telegram OAuth auth oqimlari.
- [ ] Real Eskiz SMS provider.
- [ ] Real SMTP/SendGrid provider.
- [ ] Users invite/update/delete.
- [ ] Custom role create/update/delete.
- [ ] Audit log UI.
- [ ] Notification settings UI.
- [ ] Active sessions UI va session revoke.
- [ ] Grace period UX: no-subscription, trial, read-only, locked holatlarini yakuniy product qaroriga moslash.

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

1. Full backend/frontend verification.
2. Foundation qarzlari ichidan auth reset + users invite + audit UI.
3. SMM MVP qarzlari ichidan brand wizard + structured knowledge base.
4. Real providerlar: Eskiz, SMTP, Meta OAuth.
5. CRM/Inbox/Ads prototiplarini product scope bo‘yicha ajratish.
