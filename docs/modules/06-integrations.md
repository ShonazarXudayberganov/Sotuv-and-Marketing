# Modul 06 — Integratsiyalar (Open Ecosystem)

> Marketplace, public API, webhook, white-label, custom builder.
> Bosqich 4 da quriladi.

---

## Sahifalar

```
🔗 Integratsiyalar
├─ 🛒 Marketplace        /integrations
├─ 🟢 Faollar            /integrations/active
├─ 📡 API kalitlar       /integrations/api-keys
├─ 🔔 Webhook'lar        /integrations/webhooks
├─ 📥 Import/Export       /integrations/data-transfer
├─ 💾 Backup/Restore     /integrations/backup
├─ 🤖 Custom builder     /integrations/builder       [Post-MVP]
├─ 🎨 White-label        /integrations/white-label   [Pro+]
└─ ⚙️ Sozlamalar          /integrations/settings
```

---

## Marketplace

Variant C: Featured (yuqorida 5-7 ta) + Categories (pastida).

Kategoriyalar:
- Mahalliy (Click, Payme, Eskiz, OnlinePBX, MyID, 1C)
- Tashqi (Google Workspace, Microsoft 365, Slack)
- Reklama (Meta, Google, TikTok)
- E-commerce (Shopify, WooCommerce)
- AI (OpenAI, Hugging Face)

Har integratsiya kartochkasi: logo, nom, tavsif, mashhur badge, sharhlar (4.8★).

---

## Phase'lar bo'yicha integratsiyalar

**Phase 1 (MVP):**
- Eskiz / Playmobile (SMS)
- Stripe / Click / Payme (to'lov)
- Meta Business
- Telegram Bot API

**Phase 2:**
- OnlinePBX (CRM uchun)
- AmoCRM import
- Google Calendar
- Email (SMTP/IMAP)

**Phase 3:**
- 1C (asosiy)
- Google Ads, Facebook Ads
- MyID
- Yandex.Metrica

**Phase 4:**
- Shopify, WooCommerce
- Slack, Microsoft Teams
- Zapier, Make
- Custom builder

---

## Sinxronizatsiya

**Two-way real-time** (sizning tanlovingiz):
- AmoCRM ↔ NEXUS CRM (mijozlar, bitimlar)
- 1C → NEXUS (mahsulotlar, narxlar)
- Google Calendar ↔ NEXUS Tasks

**Konflikt strategiyasi:** Mixed (per-field):
- Tezkor o'zgaradiganlar: oxirgi yozuv g'olib (telefon raqami)
- Muhimlar: foydalanuvchi tanlaydi (mijoz statusi)
- Audit: barcha konfliktlar log

---

## Public API

REST + GraphQL. OAuth 2.0 + API kalit (HMAC-SHA256).

Rate limit: 1000 req/min (Pro), 10000 req/min (Business).

OpenAPI 3.0 spec: `/api/v1/openapi.json`.

GraphQL playground: `/graphql`.

---

## Webhooks

Event subscription:
- `contact.created`
- `deal.stage_changed`
- `post.published`
- `message.received`
- `lead.captured`
- `automation.triggered`
- ...

HMAC-SHA256 signature header (`X-Nexus-Signature`).

Retry: 3 marta (5s, 30s, 5min).

Dashboard: history, retry manual, debug.

---

## Backup/Restore

**Avtomatik:** har kun 02:00 (server vaqti).
**Manual:** istalgan vaqtda.

**Saqlash:**
- Server-side (default): 30 kun
- User-side: AWS S3 / Google Drive / Dropbox (foydalanuvchi tokeni)

**Encryption:** AES-256 (kalit faqat foydalanuvchida — sizning tanlovingiz, "zero knowledge").

---

## White-label (Business+ va Enterprise)

- Domen: `app.kompaniyangiz.uz`
- Logo va brand
- Email shablon (custom domain)
- Color theme override
- Custom landing (login sahifasi)

---

## Custom Automation Builder (Post-MVP)

Zapier-style vizual editor:

```
Trigger: Yangi lead (CRM)
   ↓
Filter: AI Score > 70
   ↓
Action: Telegram bot xabar
   ↓
Action: Vazifa yaratish (Sardor)
   ↓
Action: 24 soat keyin SMS
```

100+ action blocks, conditional branching, loops.

---

## DB jadvallar

- `integrations` — ulanganlar
- `integrations_catalog` (public schema)
- `sync_jobs` — sync tarixi
- `webhooks` — webhook subscriptions
- `webhook_deliveries` — delivery log
- `api_keys`
- `backups`

---

## Acceptance (Bosqich 4)

1. ✅ Marketplace (Variant C)
2. ✅ Public API (REST + GraphQL)
3. ✅ Webhook tizimi (HMAC-SHA256)
4. ✅ Two-way sync (CRM, 1C, Calendar)
5. ✅ Backup/Restore (encrypted)
6. ✅ White-label (Business+)
7. ✅ Custom builder (Post-MVP)
8. ✅ Test coverage ≥ 80%
