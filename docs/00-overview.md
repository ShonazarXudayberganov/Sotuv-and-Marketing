# 00 — Loyiha umumiy ko'rinishi

> Loyiha haqida birinchi marta o'qiyotgan har kim shu fayldan boshlasin.
> 5 daqiqada loyihani tushunish.

---

## 1 paragrafda

NEXUS AI — O'zbekiston bozori uchun mo'ljallangan multi-tenant SaaS platforma.
6 ta modul (CRM, SMM, Reklama, Inbox, Hisobotlar, Integratsiyalar) bitta tizimda,
har joyda AI bilan. Maqsadli mijozlar — 10-50 xodimli o'rta biznes, asosan
xizmat va savdo sohasida (B2C). Strategiya — bosqichma-bosqich (Wedge):
SMM moduldan boshlab, 2-3 yil ichida to'liq ekotizimga.

## Nima uchun bu loyiha?

O'zbekistondagi o'rta biznes uchun zamonaviy AI bilan jihozlangan biznes
boshqaruv tizimi yo'q. AmoCRM, Bitrix24 — qisman ishlaydi, lekin:
1. O'zbek tilini yaxshi tushunmaydi
2. Mahalliy ekotizim bilan bog'lanmagan (1C, Click/Payme, MyID)
3. AI imkoniyatlari sustligi yoki yo'qligi
4. Bitta moduldek ishlaydi, hammasi bir joyda emas

NEXUS AI — bu bo'shliqni to'ldiradi.

## 4 ta farqlovchi tomon

1. **O'zbek tilida sifatli AI** — kontent yaratish, sentiment, suhbat
2. **Mahalliy moslashish** — 1C, Click/Payme, Eskiz/Playmobile, OnlinePBX, MyID
3. **Hammasini bir joyda** — vertikal yondashuv, ko'p moduli yagona ekosistemada
4. **AI har joyda — Action layer** — faqat tahlil emas, harakat ham (auto-optimize)

## Maqsadli mijoz portreti

| Atribut | Tavsif |
|---|---|
| Geografik | O'zbekiston (keyin MDH) |
| Hajm | 10-50 xodim |
| Faoliyat | Salonlar, klinikalar, restoranlar, do'konlar, kurslar, agentliklar |
| To'lov | $100-500/oy SaaS xizmatga |
| Qaror beruvchi | Owner yoki Marketing direktor |
| Asosiy muammolar | CRM yo'q, SMM noaniq, Reklama tushunmaydi, hammasi tarqoq |

## Roadmap qisqacha

```
Bosqich 0 — Tayyorgarlik         [1-2 oy]   ✅ Tugagan
Bosqich 1 — SMM MVP              [3-4 oy]   ← Hozir: hardening
Bosqich 2 — CRM + Inbox          [3-4 oy]   Prototype boshlangan
Bosqich 3 — Reklama + Hisobotlar [3-4 oy]   Prototype boshlangan
Bosqich 4 — Integratsiyalar      [3-6 oy]   Prototype boshlangan
```

2026-05-03 holatiga ko‘ra kod roadmapdan oldinga ketgan: Bosqich 2-4 modullari
uchun dastlabki modellar, endpointlar, UI sahifalar va testlar bor. Ular hali
commercial-ready deb hisoblanmaydi; joriy fokus Bosqich 1 SMM MVP ni yakunlash
va Foundation qarzlarini yopish.

## Texnologiyalar (qisqacha)

- **Backend:** Python + FastAPI + PostgreSQL + Redis + Celery
- **Frontend:** Next.js + TypeScript + Tailwind + shadcn/ui
- **AI:** Claude (asosiy), GPT-4o (backup), Whisper, Embeddings
- **Infra:** Docker + UzCloud
- **Multi-tenancy:** Schema-per-tenant (PostgreSQL)

Tafsilotlar: [docs/01-architecture.md](01-architecture.md)

## Loyiha qoidalari (qisqacha)

1. **Bosqichma-bosqich** — hammasini birvarakayiga emas
2. **Test driven** — test bo'lmasa kod yozilmaydi
3. **Multi-tenancy birinchi** — har funksiyada tenant kontekstini tekshir
4. **AI cap** — har tenant uchun token cheklov
5. **Inson nazorati** — kritik joylarda (auth, billing) majburiy
6. **Hujjat har doim yangi** — kod va hujjat parallel rivojlanadi

## Keyingi qadam

- Texnik tafsilot kerakmi? → [01-architecture.md](01-architecture.md)
- Modul ustida ishlayapsizmi? → [modules/](modules/)
- Joriy vazifalarni ko'rmoqchimisiz? → [../TODO.md](../TODO.md)
- Roadmap kerakmi? → [roadmap/](roadmap/)
- Atamalar tushunarsizmi? → [glossary.md](glossary.md)
