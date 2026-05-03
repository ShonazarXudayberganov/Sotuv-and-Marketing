# 05 — API kontraktlari

> REST + GraphQL endpoint reyestri. OpenAPI 3.0 auto-generated.

---

## Asosiy konvensiyalar

### Base URL

```
Production:  https://api.nexus-ai.uz/api/v1
Staging:     https://api-staging.nexus-ai.uz/api/v1
Local:       http://localhost:8000/api/v1
```

### Auth

```
Authorization: Bearer <access_token>
```

### Response format

**Success:**
```json
{
  "data": { ... } | [ ... ],
  "meta": { "page": 1, "limit": 50, "total": 234 }
}
```

**Error:**
```json
{
  "detail": "Foydalanuvchi tilida xato",
  "code": "ERROR_CODE",
  "field": "field_name",   // validation xatolari uchun
  "trace_id": "uuid"
}
```

---

## Auth (`/api/v1/auth/*`)

| Method | Endpoint | Tavsif |
|---|---|---|
| POST | `/auth/register` | Ro'yxatdan o'tish |
| POST | `/auth/verify-phone` | SMS kod tasdiqlash |
| POST | `/auth/login` | Kirish |
| POST | `/auth/refresh` | Token yangilash |
| POST | `/auth/logout` | Chiqish |
| POST | `/auth/forgot-password` | Parolni tiklash |
| POST | `/auth/reset-password` | Yangi parol o'rnatish |
| GET | `/auth/oauth/google` | Google OAuth boshlash |
| GET | `/auth/oauth/google/callback` | Google callback |
| GET | `/auth/oauth/telegram` | Telegram OAuth |
| POST | `/auth/2fa/enable` | 2FA yoqish |
| POST | `/auth/2fa/verify` | 2FA tasdiqlash |
| POST | `/auth/2fa/disable` | 2FA o'chirish |
| GET | `/auth/me` | Joriy foydalanuvchi |

`/auth/forgot-password` SMS kod yuboradi va
`{ verification_id, phone_masked, expires_in_seconds }` qaytaradi.
`/auth/reset-password` body:
`{ verification_id, code, new_password }`; muvaffaqiyatli bo‘lsa `204`.

---

## Foundation (`/api/v1/*`)

### Tenant
- `GET    /tenant` — Joriy kompaniya ma'lumotlari
- `PATCH  /tenant` — Yangilash

### Users
- `GET    /users` — Xodimlar ro'yxati
- `POST   /users` — Yangi xodim taklif qilish
- `GET    /users/:id` — Detallar
- `PATCH  /users/:id` — Tahrirlash
- `DELETE /users/:id` — O'chirish
- `POST   /users/:id/invite` — Qayta taklif

### Roles
- `GET    /roles` — Rollar ro'yxati
- `POST   /roles` — Custom rol yaratish
- `PATCH  /roles/:id` — Tahrirlash
- `DELETE /roles/:id` — O'chirish (faqat custom)

### Departments
- `GET    /departments` — Tree ko'rinish
- `POST   /departments` — Yangi
- `PATCH  /departments/:id` — Tahrirlash
- `DELETE /departments/:id` — O'chirish
- `PATCH  /departments/:id/move` — Daraxtda ko'chirish

### Tasks
- `GET    /tasks` — Filter, sort
- `POST   /tasks` — Yaratish
- `GET    /tasks/:id`
- `PATCH  /tasks/:id`
- `DELETE /tasks/:id`
- `PATCH  /tasks/:id/status` — Status o'zgartirish
- `POST   /tasks/:id/comments`
- `GET    /tasks/calendar?start=...&end=...`
- `GET    /tasks/kanban`

### Notifications
- `GET    /notifications`
- `PATCH  /notifications/:id/read`
- `POST   /notifications/mark-all-read`
- `GET    /notifications/settings`
- `PATCH  /notifications/settings`

### Billing
- `GET    /billing/plan` — Joriy tarif
- `POST   /billing/upgrade` — Yangilash
- `GET    /billing/invoices`
- `GET    /billing/invoices/:id`
- `POST   /billing/invoices/:id/pay` — Click/Payme/Uzum

### Audit
- `GET    /audit?resource_type=...&resource_id=...`

### API Keys
- `GET    /api-keys`
- `POST   /api-keys`
- `DELETE /api-keys/:id` — Revoke

---

## CRM (`/api/v1/*`)

### Contacts
- `GET    /contacts?search=&assignee=&score_min=&score_max=&...`
- `POST   /contacts`
- `GET    /contacts/:id`
- `PATCH  /contacts/:id`
- `DELETE /contacts/:id`
- `POST   /contacts/import` — CSV/Excel
- `GET    /contacts/export?format=csv|excel`
- `POST   /contacts/:id/score` — AI score qayta hisoblash
- `GET    /contacts/:id/timeline`
- `GET    /contacts/:id/deals`

### Deals
- `GET    /deals?pipeline=&stage=&assignee=&...`
- `POST   /deals`
- `GET    /deals/:id`
- `PATCH  /deals/:id`
- `DELETE /deals/:id`
- `PATCH  /deals/:id/stage` — Bosqich o'zgartirish
- `GET    /deals/kanban?pipeline_id=`
- `POST   /deals/:id/win` — Yopish (sotildi)
- `POST   /deals/:id/lose` — Yopish (yo'qotildi, reason bilan)

### Pipelines
- `GET    /pipelines`
- `POST   /pipelines`
- `PATCH  /pipelines/:id`
- `DELETE /pipelines/:id`
- `GET    /pipelines/:id/stages`
- `PATCH  /pipelines/:id/stages` — Reorder

### Products
- `GET    /products`
- `POST   /products`
- `GET    /products/:id`
- `PATCH  /products/:id`
- `DELETE /products/:id`

### Activities
- `GET    /activities?contact_id=&deal_id=&type=`
- `POST   /activities`

### Automations
- `GET    /automations`
- `POST   /automations`
- `PATCH  /automations/:id`
- `DELETE /automations/:id`
- `POST   /automations/:id/test` — Test run
- `GET    /automations/:id/runs`

---

## SMM (`/api/v1/*`)

### Brands
- `GET    /brands`
- `POST   /brands`
- `GET    /brands/:id`
- `PATCH  /brands/:id`
- `DELETE /brands/:id`

### Knowledge Base
- `GET    /brands/:id/knowledge-base`
- `POST   /brands/:id/knowledge-base/section/:section`
- `POST   /brands/:id/knowledge-base/upload-file`
- `POST   /brands/:id/knowledge-base/parse-website`
- `POST   /brands/:id/knowledge-base/import-instagram`
- `POST   /brands/:id/knowledge-base/chat` — AI chat

### Social Accounts
- `GET    /brands/:id/social-accounts`
- `POST   /brands/:id/social-accounts/connect/:platform`
- `DELETE /brands/:id/social-accounts/:account_id`

### AI Generation
- `POST   /ai/generate-content` — 3 variant
- `POST   /ai/improve-content` — tezkor tahrir
- `POST   /ai/generate-hashtags`
- `POST   /ai/generate-reels-script`
- `POST   /ai/generate-30-day-plan`

### Posts
- `GET    /posts?brand_id=&status=&date_from=&...`
- `POST   /posts`
- `GET    /posts/:id`
- `PATCH  /posts/:id`
- `DELETE /posts/:id`
- `POST   /posts/:id/publish` — Darhol e'lon qilish
- `POST   /posts/:id/schedule` — Rejaga kiritish
- `POST   /posts/:id/approve`
- `POST   /posts/:id/reject`
- `GET    /posts/:id/metrics`
- `GET    /posts/calendar?brand_id=&start=&end=`

### Brand Assets
- `GET    /brands/:id/assets`
- `POST   /brands/:id/assets` — Upload
- `DELETE /brands/:id/assets/:asset_id`

---

## Reklama (`/api/v1/*`)

### Campaigns
- `GET    /campaigns?platform=&status=`
- `POST   /campaigns`
- `GET    /campaigns/:id`
- `PATCH  /campaigns/:id`
- `POST   /campaigns/:id/pause`
- `POST   /campaigns/:id/resume`
- `DELETE /campaigns/:id`
- `GET    /campaigns/:id/metrics`
- `POST   /campaigns/wizard` — 8-step wizard data

### Ad Sets / Ads
- `GET    /ad-sets?campaign_id=`
- `POST   /ad-sets`
- `GET    /ads?ad_set_id=`
- `POST   /ads`

### Audiences
- `GET    /audiences`
- `POST   /audiences`
- `POST   /audiences/lookalike` — AI lookalike yaratish

### Lead Forms
- `GET    /lead-forms`
- `POST   /lead-forms`
- `GET    /lead-forms/:id`
- `PATCH  /lead-forms/:id`
- `GET    /lead-forms/:id/leads`

### Landing Pages
- `GET    /landing-pages`
- `POST   /landing-pages`
- `GET    /landing-pages/:id`
- `PATCH  /landing-pages/:id`
- `POST   /landing-pages/:id/publish`

### AI Optimizer
- `GET    /campaigns/:id/recommendations`
- `POST   /campaigns/:id/apply-recommendation`
- `POST   /campaigns/:id/optimizer-mode` — off/recommend/auto/full

---

## Inbox (`/api/v1/*`)

### Conversations
- `GET    /conversations?channel=&status=&assignee=&...`
- `GET    /conversations/:id`
- `PATCH  /conversations/:id` — status, assignee, priority
- `POST   /conversations/:id/close`
- `POST   /conversations/:id/reopen`
- `POST   /conversations/:id/transfer` — boshqa xodimga

### Messages
- `GET    /conversations/:id/messages?limit=50&before=`
- `POST   /conversations/:id/messages`
- `POST   /conversations/:id/messages/draft` — AI draft so'rash

### Templates
- `GET    /templates`
- `POST   /templates`
- `PATCH  /templates/:id`
- `DELETE /templates/:id`

### AI Settings
- `GET    /inbox/ai-settings`
- `PATCH  /inbox/ai-settings`

---

## Hisobotlar (`/api/v1/*`)

### Dashboard
- `GET    /reports/dashboard?period=`
- `GET    /reports/dashboard/recommendations`

### Anomalies
- `GET    /anomalies?severity=&type=&from=`
- `POST   /anomalies/:id/acknowledge`

### AI Buddy
- `POST   /ai-buddy/chat`
- `GET    /ai-buddy/conversations`
- `GET    /ai-buddy/conversations/:id`

### Goals
- `GET    /goals?level=&owner=&period=`
- `POST   /goals`
- `PATCH  /goals/:id`
- `DELETE /goals/:id`
- `POST   /goals/:id/key-results`

### Forecasts
- `GET    /forecasts/revenue?months=3|6|12`
- `GET    /forecasts/leads`
- `GET    /forecasts/ai-cost`

### Reports
- `GET    /report-templates`
- `POST   /reports/generate?template=&period=`
- `GET    /reports/scheduled`
- `POST   /reports/scheduled`
- `DELETE /reports/scheduled/:id`

---

## Integratsiyalar (`/api/v1/*`)

### Catalog
- `GET    /integrations/catalog?category=&search=`
- `GET    /integrations/catalog/:code`

### Active integrations
- `GET    /integrations`
- `POST   /integrations` — Connect
- `DELETE /integrations/:id` — Disconnect
- `POST   /integrations/:id/test`
- `POST   /integrations/:id/sync`

### Webhooks
- `GET    /webhooks`
- `POST   /webhooks`
- `DELETE /webhooks/:id`
- `GET    /webhooks/:id/deliveries`
- `POST   /webhooks/:id/deliveries/:delivery_id/retry`

### Backup
- `GET    /backups`
- `POST   /backups` — Manual backup
- `POST   /backups/:id/restore`
- `GET    /backups/settings`
- `PATCH  /backups/settings`

---

## WebSocket (`/ws/*`)

```
wss://api.nexus-ai.uz/ws/inbox?token=<access_token>
wss://api.nexus-ai.uz/ws/notifications?token=<access_token>
```

### Events (server → client)

```json
{
  "type": "message.new",
  "data": { "conversation_id": 42, "message": { ... } }
}
```

Asosiy event'lar:
- `message.new`
- `conversation.updated`
- `notification.new`
- `task.assigned`
- `anomaly.detected`
- `automation.triggered`

---

## GraphQL (`/graphql`)

```graphql
type Query {
  contacts(filter: ContactFilter, page: Int, limit: Int): ContactConnection
  contact(id: ID!): Contact
  deals(filter: DealFilter): DealConnection
  posts(brandId: ID, status: PostStatus): [Post]
  conversations(filter: ConversationFilter): ConversationConnection
}

type Mutation {
  createContact(input: ContactInput!): Contact
  updateDeal(id: ID!, input: DealUpdateInput!): Deal
  generateContent(input: GenerateContentInput!): [PostVariant]
  publishPost(id: ID!): Post
}

type Subscription {
  conversationUpdated(id: ID!): Conversation
  newMessage(conversationId: ID): Message
}
```

Playground: `https://api.nexus-ai.uz/graphql`

---

## Rate limiting

Per endpoint group:

| Group | Limit (Pro) | Limit (Business) |
|---|---|---|
| Auth | 10/min | 10/min |
| Read (GET) | 1000/min | 10000/min |
| Write (POST/PATCH) | 200/min | 2000/min |
| AI generation | 60/min | 600/min |
| Bulk import | 10/hour | 100/hour |

Header'da: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

---

## OpenAPI

To'liq spec auto-generated FastAPI'dan: `https://api.nexus-ai.uz/openapi.json`.

Swagger UI: `https://api.nexus-ai.uz/docs` (faqat dev/staging).
