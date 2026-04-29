# ADR-0004: Dizayn tizimi (Luxury theme)

**Holat:** Qabul qilingan
**Sana:** 2026-04-29

## Kontekst

UI dizayn tili — premium SaaS hissi yaratish.

## Variantlar

### A. Material Design (Google)
- ✅ Tayyor
- ❌ Generic, "Google-vibe"

### B. Apple HIG
- ✅ Sifatli
- ❌ Mobile-first, web uchun moslashish

### C. Custom Luxury (premium fintech / SaaS uslubida)
- ✅ Differentiator
- ✅ Brand identity
- ❌ Ko'proq dizayn ishi

## Qaror

**Variant C — Custom Luxury Theme.**

- Asos: shadcn/ui + TailwindCSS (komponent freedom)
- Inspiratsiya: Linear, Notion, Stripe, Apple + Cartier/LV (gold accents)
- Palitra: Cream + Charcoal + Gold (#C9A961)
- Tipografiya: Playfair (sarlavhalar) + Inter (body)
- Animatsiya: yumshoq (200ms ease)

## Implementatsiya

`docs/03-design-system.md` — to'liq spec.

`apps/web/src/styles/theme.css` — CSS variabllar.
`apps/web/tailwind.config.ts` — extended palette.
