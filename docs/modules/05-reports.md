# Modul 05 — Hisobotlar va Tahlil (AI Sherik)

> Executive Dashboard, anomaliya monitor, AI Sherik (biznes maslahatchi).
> Bosqich 3 da quriladi.

---

## Sahifalar

```
📊 Hisobotlar
├─ 🏠 Executive          /reports
├─ 🚨 Anomaliyalar       /reports/anomalies
├─ 🤖 AI Sherik          /reports/ai-buddy
├─ 🎯 Maqsadlar (OKR)    /reports/goals
├─ 🔮 Prognoz            /reports/forecast
├─ 📊 Voronka            /reports/funnels
├─ 🧪 A/B test           /reports/ab-tests       [Bosqich 4]
├─ 👥 Kohorta            /reports/cohorts
├─ ⭐ Benchmarking        /reports/benchmarking   [Soon]
├─ 📅 Avto-hisobotlar    /reports/scheduled
└─ ⚙️ Sozlamalar          /reports/settings
```

---

## Executive Dashboard

Yuqorida 6 ta KPI kartochkasi:
- 💰 Daromad
- 📞 Yangi leadlar
- ✅ Yopilgan bitimlar
- 📈 ROI
- 👥 Faol mijozlar
- 🎯 Mas'uliyat KPI

Har biri: qiymat + o'zgarish (▲/▼) + spark line.

Pastida: AI Tavsiyalar (3-5 ta tavsiya, kontekstga moslashgan).

---

## Anomaliya detector

8 turdagi anomaliya:

| Tur | Misol |
|---|---|
| Kutilmagan ko'tarilish | "Lead 3x o'sdi — sabab nima?" |
| Kutilmagan tushish | "Sotuvlar 40% pasaydi" |
| O'rtachadan chetlanish | "Bu hafta CTR 2.3 sigma past" |
| Trend buzilish | "5 hafta o'sgan, bu hafta tushdi" |
| Mavsum buzilishi | "Iyul odatda yuqori, lekin past" |
| Tezlik o'zgarishi | "Mijoz javob beruv tezligi 2x oshdi" |
| Threshold buzilishi | "Kunlik byudjet 80% sarflandi" |
| Sifat tushishi | "Negativ xabarlar 3x oshdi" |

Aniqlanish: statistical (z-score, IQR) + threshold (custom). AI pastki sabab tahlili.

Bildirishnoma: tizim + Telegram + email (severity bo'yicha).

---

## AI Sherik (chatbot biznes maslahatchi)

```
Sen: "Bu hafta sotuv past nega?"

AI Sherik: 
🔍 Tahlil:
- Bu hafta 23 ta bitim yopildi (oldingi hafta — 38)
- Asosiy sabab: 5 ta yirik bitim 2-bosqichdan o'tmagan
- Mas'ul Sardor 3 kun ta'tilda edi

💡 Tavsiya:
1. Sardorning bitimlarini boshqa xodimga vaqtincha o'tkazing
2. "Iliq leadlar" filterida 12 ta mijoz follow-up kutmoqda
3. AI Score 80+ mijozlarga prioritet bering

[Bitimlarni ko'rish →] [Follow-up rejasi tuzish →]
```

Tier-bo'yicha limit:
- Start: 10 savol/oy
- Pro: 100 savol/oy
- Business: cheksiz

Proaktiv: kunlik xulosa, haftalik tahlil, oylik strategiya.

---

## OKR / Maqsadlar

Daraja: kompaniya / bo'lim / xodim. Misol:

```
Q3 maqsad: Daromadni 30% oshirish
├─ KR1: Yangi leadlar +50% (joriy: 65%)
├─ KR2: Konversiya +20% (joriy: 12%)
└─ KR3: O'rtacha chek +15% (joriy: 18%)

Umumiy progress: 73% ✓ Yo'lda
AI bashorati: muddat oxirida 87% bajariladi
```

Kunlik avto-update real ma'lumotlardan.

---

## Prognoz (Forecasting)

ML modeli (Prophet, statsmodels):
- Daromad bashorati (3, 6, 12 oy)
- Yangi mijozlar oqimi
- AI byudjet sarfi
- Confidence interval (kuchli/o'rta/sust)

**Talab:** kamida 3 oylik ma'lumotlar (bo'lmasa "Ma'lumot yetarli emas").

---

## Tayyor shablonlar (12-15 ta)

- Daromad va xarajat
- Mijoz LTV
- ROAS reklama
- Marketing voronka
- Kontent samaradorligi
- SMM ROI
- Mas'ul KPI
- Konversiya
- Mijoz oqimi (cohort)
- Anomaliya hisoboti
- Oylik rezyume
- Yillik strategik

PDF / Excel eksport. Avto-yuborish (kunlik/haftalik/oylik).

---

## Telegram WebApp (mobil)

Yo'lda kerakli statistikani ko'rish uchun:
- Bugungi sotuvlar
- Yangi leadlar
- Kritik bildirishnomalar
- AI Sherik chat

Push notification kritik anomaliyalar uchun.

---

## DB jadvallar

- `anomalies`
- `goals`, `key_results`
- `scheduled_reports`
- `ai_buddy_conversations`
- `forecasts`
- `ab_tests` (Bosqich 4)

---

## Acceptance (Bosqich 3)

1. ✅ Executive Dashboard (6 KPI + AI tavsiya)
2. ✅ 8 turdagi anomaliya
3. ✅ AI Sherik (tier limitlari)
4. ✅ OKR tizimi
5. ✅ Forecasting (3+ oy ma'lumot)
6. ✅ 12+ tayyor hisobot shablon
7. ✅ Telegram WebApp
8. ✅ Avto-hisobotlar
9. ✅ Test coverage ≥ 80%
