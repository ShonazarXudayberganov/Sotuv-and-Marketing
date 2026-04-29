# ADR-0001: Monorepo struktura

**Holat:** Qabul qilingan
**Sana:** 2026-04-29

## Kontekst

Loyiha 6 modul + frontend + backend + sayt widget. Bir nechta repo (multi-repo)
yoki bitta repo (monorepo)?

## Variantlar

### A. Multi-repo
Har modul — alohida repo (`nexus-crm`, `nexus-smm`, ...).
- ✅ Modullar mustaqil
- ❌ Cross-modul refactoring murakkab
- ❌ Shared types takrorlanadi
- ❌ CI/CD murakkab

### B. Monorepo (Turborepo / Nx)
Bitta repo, `apps/` va `packages/` strukturasi.
- ✅ Cross-modul refactoring oson
- ✅ Shared types — bitta package
- ✅ Atomik commits
- ❌ Repo katta bo'lishi mumkin

### C. Hybrid
Backend monorepo, frontend alohida.
- ❌ Murakkablik kam emas, ko'p

## Qaror

**Variant B — Monorepo** (Turborepo).

```
nexus-ai/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── web/          # Next.js frontend
│   └── widget/       # Sayt widget (alohida server)
├── packages/
│   ├── shared-types/ # TypeScript types (BE ↔ FE)
│   └── ui/           # Shared UI komponentlar (kerak bo'lsa)
├── infra/
└── docs/
```

## Oqibatlar

**Ijobiy:**
- Bir kishi har bo'lim ustida ishlay oladi
- Type safety BE va FE o'rtasida
- Tezroq iteratsiya

**Salbiy:**
- CI build vaqti uzunroq (Turborepo cache yordam beradi)
- Repo size

**Keyin:**
- Agar mikroservis kerak bo'lsa — Inbox real-time alohida service'ga ajratiladi (Bosqich 4)
