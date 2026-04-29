# ADR-0005: To'lov provayderlari

**Holat:** Qabul qilingan
**Sana:** 2026-04-29

## Kontekst

O'zbekiston SaaS uchun to'lov tizimlari.

## Qaror

### Bosqich 0-2 (sodda):
- **Bank o'tkazmasi** (yuridik shaxs uchun, asosiy)
- **Naqd** (admin tomonidan tasdiqlanadi)

### Bosqich 3+ (avtomatlash):
- **Click** — eng mashhur
- **Payme** — UX yaxshi
- **Uzum Pay** — yangi, tez o'sayotgan

### Bosqich 4 (xalqaro):
- **Stripe** (xalqaro mijozlar)
- **PayPal** (faqat Enterprise)

## Sabablar

- Boshlang'ich mijozlar yuridik shaxs (bank o'tkazma)
- Avtomatlash bosqich 3 da kerak (mijozlar ko'paygan)
- Stripe — xalqaro yo'nalish uchun

## Oqibatlar

- Invoice generatsiya (PDF, INN bilan) — Bosqich 0
- Click/Payme/Uzum integration — Bosqich 3
- Subscription billing model
