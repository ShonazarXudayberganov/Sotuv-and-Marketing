# TODO — Joriy Holat Va Ish Rejasi

> Har sessiyada shu fayl real holatga moslab yangilanadi.
> Eski sprint loglar arxiv sifatida git tarixida qoladi; bu fayl esa hozirgi ishni boshqaradi.

---

## Joriy Holat

**Sana:** 2026-05-05
**Asosiy bosqich:** Bosqich 1 — SMM MVP hardening (Foundation 100% yopildi)  
**Amaldagi kod holati:** Foundation barcha qarzlari yopilgan; SMM ancha oldinga ketgan; CRM/Inbox/Ads/Reports/Marketplace prototiplari mavjud.  
**Joriy maqsad:** SMM MVP'ni production-ready holatga keltirish va real provider integratsiyalari (IG/FB/Eskiz/SMTP).

### Oxirgi Tekshiruv

- Backend testlar: `223 passed`, coverage `83.05%` (2 ta SQLAlchemy cleanup warning qoldi).
- Frontend format, lint, type-check, test, build: o‘tgan.
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
- [x] Knowledge Base 8 bo‘limli struktura va progress endpoint/UI.
- [x] Knowledge Base importlari: website parse, Instagram import, AI chat.
- [x] AI Studio: 3 variant draft generation, tezkor tahrir, AI chat, hashtag, reels script va 30 kunlik reja.
- [x] AI content draft generation, token usage tracking, RAG prompt context.
- [x] Telegram, Meta, YouTube social account link/test/read flows.
- [x] Posts: draft/schedule/publish-now/retry/cancel.
- [x] Posts approval workflow: review/approve/reject API va UI actionlari.
- [x] Brand assets CRUD/upload: logo, rasm, video, template, font, rang va referens.
- [x] SMM analytics overview/timeseries/top posts/insights.
- [x] Web UI: `/smm`, `/smm/brands`, `/smm/brand-assets`, `/smm/knowledge-base`, `/smm/ai-studio`, `/smm/social`, `/smm/posts`, `/smm/calendar`, `/smm/analytics`.
- [x] Brand yaratish 5-step wizard (`/smm/brands` create/edit flow).

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

- [x] Brand yaratish 5-step wizard.
- [x] Knowledge Base 8 bo‘limli strukturaga keltirish.
- [x] Knowledge Base import usullari: website parse, Instagram import, AI chat.
- [x] AI Studio: 3 variant generatsiya, tezkor tahrir, AI chat.
- [x] Hashtag generator.
- [x] Reels/Story script generator.
- [x] AI 30 kunlik kontent reja.
- [x] Approval workflow: reviewga yuborish, approve, reject, audit va posts UI actionlari.
- [x] Brand assets CRUD/upload.
- [x] Content plan 3-view: calendar/list/kanban, AI text import va plan itemdan post yaratish.
- [x] AI Studio yordamchi promptlarini alohida prompt fayllariga chiqarish.
- [ ] IG/FB publishingni real credential/OAuth bilan production holatga keltirish.
  - [x] Publish hardening #1: publication event log, transient retry scheduling,
        manual retry reset, platform status sync endpoint/UI.
  - [x] Meta token xatolarini ajratish va saqlangan user token bo‘lsa Page tokenni
        qayta olishga urinish.
  - [x] Full Meta OAuth connect callback flow (`start/finish` backend + callback UI).
  - [x] Meta permissions review va production app approval checklist.
  - [x] Reviewer demo seed script + staging runbook.
  - [ ] Production reviewer environment + real Meta app review submission.
  - [ ] IG formatlari: feed image/video, Reels, Story variantlari.
    - [x] Post contract: `content_format` (`feed` / `reels` / `story`) va create UI.
    - [x] Media-type aware Meta adapters: feed image/video, Reels, Story publish flows.
    - [ ] Real production smoke: Meta Graph API bilan feed video / reels / story publish verifikatsiyasi.
- [ ] SMM analyticsga real platform metrics ingestion.
  - [x] Meta publication snapshotda real engagement counterlarni olishga urinish
        (`likes`, `comments`, `shares`) va qolgan providerlarda synthetic fallback.
  - [ ] Meta views/reach real insight metrics.
  - [ ] YouTube va Telegram real metrics ingestion.

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

1. SMM MVP qarzlari: real publishing hardening + real metrics ingestion + AI prompt fayllari.
2. Real platform integratsiyalari: IG/FB OAuth bilan haqiqiy publishing, real platform metrics ingestion.
3. CRM/Inbox prototiplarini product scope bo‘yicha ajratish va automation builder.
4. Production deploy: UzCloud + Cloudflare + Sentry + smoke/load test.

> Bosqich 0 (Foundation) endi 100% yopildi. Keyingi sessiyalar Bosqich 1 ga to‘liq fokus.
