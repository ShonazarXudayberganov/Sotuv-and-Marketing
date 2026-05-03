# Bosqich 1 — MVP: SMM moduli

> 3-4 oy. Birinchi sotiladigan mahsulot.

---

## Maqsad

To'liq funktsional SMM moduli — multi-brand, AI bilimlar bazasi, AI Studio,
kontent rejasi, IG/FB/TG publishing, asosiy tahlil.

## KPI

- 50-100 to'lovli mijoz
- $30-50K MRR (yillik recurring revenue)
- Churn < 5%/oy
- AI cost per tenant < 30% Pro narxining

## Sprintlar

### Sprint 6-7 (4 hafta) — Brendlar va bilimlar bazasi
- Brand CRUD + 5-step wizard
- Knowledge Base 8 bo'lim
- 4 to'ldirish usuli (chat, file, site, IG)
- pgvector RAG infra

### Sprint 8-9 (4 hafta) — AI Studio
- Smart Wizard (3 savol)
- 3 variant generatsiya
- 5 tahrirlash usuli
- AI Chat assistant
- Hashtag avto-gen
- Reels ssenariy

### Sprint 10-11 (4 hafta) — Kontent rejasi va Publishing
- Kalendar/Ro'yxat/Kanban
- 30 kunlik AI reja
- Drag & drop ko'chirish
- Publishing: IG (post + Reels + Story)
- TG channel
- FB Page

### Sprint 12-13 (4 hafta) — Tasdiqlash va tahlil
- Approval workflow
- Asosiy tahlil (KPI dashboard)
- AI o'rganish (best posts → keyingi)
- Brand assets
- Multi-brand testing

## Joriy implementatsiya holati (2026-05-03)

Kodda Bosqich 1 allaqachon boshlangan:
- Brand CRUD, default brand va integration credentials encryption mavjud.
- Knowledge base text/file ingest, chunking, pgvector embedding/search mavjud.
- AI draft generation RAG context bilan ishlaydi; token usage tracking bor.
- Telegram, Meta va YouTube social account link/test/read flows mavjud.
- Posts draft/schedule/publish-now/retry/cancel lifecycle mavjud.
- SMM analytics overview, timeseries, top posts va insights mavjud.
- Web UI sahifalari: `/smm`, `/smm/brands`, `/smm/knowledge-base`,
  `/smm/ai-studio`, `/smm/social`, `/smm/posts`, `/smm/calendar`,
  `/smm/analytics`.

Hali Bosqich 1 MVP tugadi deb hisoblash uchun kerak:
- 5-step brand wizard.
- Knowledge Base 8 bo‘limli struktura va progress tracking.
- Website parse, Instagram import va AI chat orqali knowledge ingest.
- AI Studio 3 variant, tezkor tahrir, AI chat, hashtag, reels script.
- 30 kunlik AI content plan.
- Approval workflow va brand assets.
- Real provider credential/OAuth bilan production publishing.

## Deliverable

To'liq SMM moduli, mijozlar foydalanyapti.

## Risklar

- **AI kontent sifati** — o'zbek tilida sifat past bo'lishi mumkin. Continuous prompt iteration.
- **Meta API o'zgarishi** — abstraction layer kerak.
- **Mijoz onboarding** — bilimlar bazasini to'ldirish murakkab. Yaxshi UX.
