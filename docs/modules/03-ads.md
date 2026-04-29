# Modul 03 — Reklama (Ads Manager)

> Meta + Google + Telegram reklamalarini bitta joydan boshqarish.
> AI Optimizer, True ROI, Landing builder.
> Bosqich 3 da quriladi.

---

## Sahifalar

```
📈 Reklama
├─ 🏠 Dashboard         /ads
├─ 📢 Kampaniyalar      /ads/campaigns
├─ 🎨 Kreativlar        /ads/creatives
├─ 👥 Auditoriyalar     /ads/audiences
├─ 📋 Lead formalar     /ads/lead-forms
├─ 🌐 Landing pages     /ads/landings
├─ 📊 Tahlil            /ads/analytics
└─ 🤖 AI Optimizator    /ads/optimizer
```

---

## Platformalar (MVP)

| Platforma | Kampaniya turlari |
|---|---|
| **Meta (Facebook+Instagram)** | Reach, Traffic, Engagement, Lead, Conversion, Sales, App install |
| **Google Ads** | Search, Display, Video (YouTube), Performance Max |
| **Telegram Ads** | Channel sponsorship (CPM bid) |

Kelajakda: Yandex.Direct, OK, VK.

---

## Smart Wizard (8 qadam)

1. **Maqsad:** Lead / Sotuv / Trafik / Tanishtirish / App install / Engagement
2. **Auditoriya:** Saqlangan / Yangi / AI Lookalike / O'rgatilgan
3. **Geografiya:** O'zbekiston (viloyatlar, shaharlar)
4. **Vaqt:** boshlanish/tugash sanasi, kun va soat oralig'i
5. **Byudjet:** kunlik yoki umumiy, taqsimlash AI ga
6. **Kreativ:** rasm/video/carousel/Reels — yuklash yoki SMM bazasidan
7. **Matn:** AI 3 variant taklif qiladi (mahsulot va auditoriya bo'yicha)
8. **Pre-flight:** AI tahlil — "kampaniya tayyor, eslatma 2 ta"

---

## AI Optimizator

3 ta rejim:
- **Tavsiya beradi** (default ON) — taklif beradi, foydalanuvchi tasdiqlaydi
- **Avto-optimizatsiya** (default OFF) — limit ichida o'zi qaror qiladi
- **To'liq AI boshqaruvi** — kampaniya umuman avtonom (limit majburiy)

Optimizatsiya nimalarni ko'radi:
- Auditoriya samaradorligi (yosh, geo, qiziqish bo'yicha CPL)
- Kreativ samaradorligi (qaysi rasm/matn yaxshi)
- Vaqt samaradorligi (qaysi soat/kun)
- Bid strategy (CPM vs CPL vs CPA)

**Xavfsizlik chegaralari:**
- Kunlik xarajat limit (qattiq cheklov)
- O'zgarish limit (24 soatda 30%+ o'zgarish bo'lsa — to'xtaydi va inson tekshiruvi)
- Audit log har AI qarori uchun

---

## Lead formalar

Drag & drop builder:
- Maydonlar: Ism · Telefon · Email · Tug'ilgan kun · Custom
- Validatsiya
- Custom dizayn (logo, ranglar)
- Spam filter (AI)
- Avto: CRM ga lead bo'lib qo'shilish

Embed code (sayt uchun) yoki direct link.

---

## Landing pages

5-10 ta tayyor shablon (sohaviy):
- Yoga studio
- Restoran
- Salon
- Klinika
- Online kurs
- ...

Drag & drop tahrirlash: hero, features, testimonials, CTA, form.

A/B test (Bosqich 4): variant 1 vs variant 2, AI traffic split.

---

## True ROI tracking

Reklama → Lead → CRM bitim → Sotuv. Tizim har qadamni kuzatadi.

```
Kampaniya "Yozgi aksiya"
├─ Sarflanldi: 5,000,000 so'm
├─ Lead: 234
├─ Bitim ochildi: 89
├─ Sotildi: 31
└─ Daromad: 47,500,000 so'm
   ROI: +850%
```

CRM'ning bitim source field'i orqali (UTM parameter avtomatik to'ldiriladi).

---

## DB jadvallar

- `campaigns`
- `ad_sets`
- `ads`
- `audiences`
- `creatives`
- `lead_forms`
- `leads`
- `landing_pages`
- `landing_versions`
- `telegram_ads`

---

## Acceptance (Bosqich 3)

1. ✅ Smart Wizard 8 qadam (Meta, Google, Telegram)
2. ✅ Auditoriya konstruktor
3. ✅ Lead form builder
4. ✅ Landing builder (5+ shablon)
5. ✅ AI Optimizer (3 rejim, default Tavsiya)
6. ✅ True ROI hisoblash (CRM bilan)
7. ✅ Xavfsizlik limitlari ishlaydi
8. ✅ Test coverage ≥ 80%
