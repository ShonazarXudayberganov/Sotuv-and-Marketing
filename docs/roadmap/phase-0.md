# Bosqich 0 — Tayyorgarlik (Foundation)

> 1-2 oy. Hech qanday biznes funksiya emas, faqat poydevor.

---

## Maqsad

Kelajakdagi har modul ustida turuvchi ishonchli infratuzilma:
- Auth + multi-tenancy
- Asosiy UI shablon (sidebar, header, layout)
- 5 standart rol va RBAC
- Foundation jadvallari
- CI/CD, test, monitoring
- AI client'lar (Claude, OpenAI) skelet

## KPI

- 0 mijoz (hali sotilmaydi)
- 0 daromad
- Test coverage ≥ 80%
- Uptime SLA o'rnatilgan
- Security scan: 0 critical/high

## Sprintlar

### Sprint 1 (2 hafta) — Repository va backend skeleton
- Repo struktura, monorepo
- FastAPI base, Postgres, Redis
- Multi-tenancy middleware
- Auth (register, login, JWT)
- Test infra

### Sprint 2 (2 hafta) — Frontend skeleton
- Next.js base
- Luxury theme (shadcn/ui + Tailwind)
- Auth pages (login, register)
- Layout (sidebar, header)
- API client + auth context

### Sprint 3 (2 hafta) — Foundation funktsiyalari
- Onboarding wizard (7 qadam)
- Sozlamalar (10 sub-page)
- RBAC implementatsiya
- Bo'limlar (departments tree)

### Sprint 4 (2 hafta) — Vazifalar va bildirishnomalar
- Tasks moduli (Kanban, Ro'yxat, Kalendar)
- Notifications (DB + WebSocket)
- Email + SMS shablon
- Audit log

### Sprint 5 (2 hafta) — Billing va deployment
- Tarif tizimi (per-modul, paketlar)
- Bank o'tkazma (Invoice generatsiya)
- Production deploy (UzCloud)
- Monitoring (Sentry, Grafana)
- Smoke test va load test

## Deliverable'lar

1. Production'da ishlovchi auth tizimi
2. Yangi tenant ro'yxatdan o'tib, sozlanishi
3. 5 ta rol bilan xodim qo'shilishi
4. Vazifalar moduli ishlashi
5. Tarif sotib olib, faollashtirish
6. Hammasi mobile responsive

## Riski

- **Multi-tenancy bug** — eng katta xavf. Har sprint'da pen-test.
- **UI yetishmasligi** — dizayner kerak yoki Claude Code dizaynni hosil qilsin.
- **AI integration kechikishi** — bosqich 1 boshlanishini kechiktiradi.
