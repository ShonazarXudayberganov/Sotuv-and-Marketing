# Modul 01 — CRM tizimi

> Mijozlar, bitimlar, voronka va sotuv jarayonlarini boshqarish.
> AI Score, OnlinePBX, avtomatlashuv bilan.
> Bosqich 2 da quriladi.

---

## Sahifalar

```
👥 CRM
├─ 🏠 Dashboard         /crm
├─ 👤 Mijozlar          /crm/contacts
├─ 💼 Bitimlar          /crm/deals
├─ 📞 Faoliyat          /crm/activities
├─ 📦 Mahsulotlar       /crm/products
├─ 📊 Hisobotlar        /crm/reports
├─ 🤖 Avtomatlash       /crm/automation
└─ ⚙️ Sozlamalar        /crm/settings
```

---

## Asosiy ob'ektlar

| Ob'ekt | Tavsif |
|---|---|
| Kontakt (Mijoz) | Jismoniy yoki yuridik shaxs (yuridik ichida vakillar) |
| Bitim (Deal) | Aniq sotuv jarayoni |
| Pipeline | Sotuv bosqichlari (multi-pipeline) |
| Mahsulot/Xizmat | Katalog (CRM va SMM bilan sinxron) |
| Faoliyat | Har muloqot: qo'ng'iroq, xabar, eslatma, uchrashuv |
| AI Score | 0-100 — sotib olish ehtimoli |
| Avtomatlash | Trigger → Shart → Harakat zanjiri |

---

## Standart pipeline bosqichlari

| Bosqich | Tavsif | Default ehtimol |
|---|---|---|
| 🆕 Yangi lead | Endi keldi, hali bog'lanmagan | 10% |
| 📞 Bog'lanildi | Birinchi aloqa | 25% |
| 💬 Muzokara | Faol muloqot | 40% |
| 💰 Taklif yuborildi | KP yuborildi | 60% |
| 🤝 Kelishildi | Asosiy shartlar kelishildi | 80% |
| ✅ Sotildi | Yopildi muvaffaqiyat | 100% |
| ❌ Yo'qotildi | Sotuv amalga oshmadi | 0% |

Multi-pipeline: "Asosiy sotuv", "VIP klientlar", "Servis xizmati" — alohida sozlash.

---

## Mijoz kartochkasi (3-ustunli layout)

**Chap (3 col, sticky):**
- Avatar, Ism, Telefon, AI Score badge
- Tezkor harakatlar: 📞 Qo'ng'iroq · 💬 Xabar · 📧 Email · 📅 Uchrashuv · 📝 Eslatma · 📋 Vazifa
- Status, Bo'lim, Mas'ul
- Ijtimoiy tarmoqlar
- Custom maydonlar (inline tahrir)
- AI tavsiyalari

**O'rta (6 col):** Timeline tablari (Hammasi, Xabarlar, Qo'ng'iroqlar, Emaillar, Eslatmalar, Vazifalar, Fayllar). Vertikal timeline sanaga ajratilgan (Bugun / Kecha / Bu hafta / Eski).

**O'ng (3 col):** Tablar — Bitimlar, Vazifalar, Fayllar, AI Tahlil.

---

## AI Score

**Inputlar:**
- Oxirgi muloqotdan o'tgan vaqt
- Muloqot tezligi (qancha tez javob beradi)
- Savollar mazmuni (narx so'raganmi, mahsulot detali)
- Bitim summalari tarixi
- Manba sifati
- Faol bitimlar holati

**Output:** 0-100 ball + tushuntirish (nima uchun shuncha).

| Ball | Daraja | Tavsif |
|---|---|---|
| 80-100 | 🔥 Issiq lead | Darhol qo'ng'iroq qiling |
| 50-79 | 🟡 Iliq | Faol mijoz, follow-up kerak |
| 20-49 | 🔵 Sovuq | Qiziqish past |
| 0-19 | ⚫ Faolsiz | Uzoq vaqt javob yo'q |

**Auto-adapt:** AI har biznes uchun mezonlarni biznes ma'lumotlari asosida o'zi belgilaydi (sizning tanlovingiz).

Har soatda yangilanadi (Celery beat task).

---

## Boshqa AI imkoniyatlar

| Funksiya | Tavsif |
|---|---|
| Sotuv prognozi | Win probability % bashorat |
| Keyingi qadam tavsiyasi | "5 kun javob yo'q, qo'ng'iroq qiling" |
| Mijoz klasterlash | "Tez harid qiluvchilar", "Narxga sezgir", "VIP" |
| Xabar qoralama | AI mijozga javob qoralaydi |
| Aloqa tarixi summary | Bir paragraf jamlash |
| Anomaliya | "Bu mijoz odatda 2 kun ichida javob beradi, lekin 5 kun bo'ldi" |
| Qo'ng'iroq transkripsiyasi | Whisper → matn → AI summary + sentiment |

---

## OnlinePBX integratsiyasi

`Sozlamalar > CRM > PBX` → API kalit. Har xodimga ichki raqam.

**Chiquvchi:**
1. Mijoz kartochkasida 📞
2. PBX → xodim raqamiga qo'ng'iroq
3. Mijoz raqamiga ulanadi
4. Tugaganda — davomiyligi yoziladi
5. Audio yozuv saqlanadi (mijoz roziligi bilan)
6. AI transkripsiya + summary
7. Avtomatik timeline'ga

**Kiruvchi:**
1. PBX raqamga qo'ng'iroq
2. Tizim raqamni CRM'da qidiradi
3. Topilsa → pop-up mijoz kartochkasi
4. Topilmasa → "Yangi mijoz, qo'shamizmi?" modal

---

## Avtomatlashtirish (block-based vizual editor)

Trigger → Shart → Harakat → zanjir.

**Trigger turlari:**
- Yangi mijoz qo'shilganda
- Bitim bosqichi o'zgarganda
- Bitim N kundan beri o'zgarmaganda
- Mas'ul biriktirilganda
- AI Score N dan oshganda
- Vazifa muddati o'tganda
- Yangi xabar (Inbox)
- Tug'ilgan kun

**Harakat turlari:**
- SMS yuborish (shablon)
- Email yuborish
- Vazifa yaratish
- Mas'ul biriktirish (round-robin yoki AI)
- Teg qo'shish
- Bitim bosqichini o'zgartirish
- Bildirishnoma
- Telegram bot xabar
- Webhook chaqirish
- AI ga so'rov

**Tayyor shablonlar:**
- "Yangi lead → mas'ulga avtomatik + SMS"
- "5 kun javob yo'q → eslatma"
- "Bitim sotildi → minnatdorchilik"
- "Tug'ilgan kun → tabriklash"
- "Inbox xabar → kontakt yarat → Yangi lead"

---

## DB jadvallar

To'liq: [../04-database-schema.md](../04-database-schema.md#crm-modul-jadvallari)

- `contacts` — mijozlar
- `deals` — bitimlar
- `pipelines`, `deal_stages`
- `products` — mahsulot katalog (CRM + SMM sync)
- `deal_products` — bitimdagi mahsulotlar
- `activities` — aloqa tarixi
- `contact_score_history` — AI score tarixi
- `automations`, `automation_runs`

---

## Acceptance (Bosqich 2)

1. ✅ Mijoz CRUD (jismoniy + yuridik), Custom maydonlar
2. ✅ Bitim CRUD, Multi-pipeline
3. ✅ Kanban + Ro'yxat + Kalendar ko'rinishlar
4. ✅ AI Score (auto-adapt) ishlaydi
5. ✅ Mahsulot katalog SMM bilan sync
6. ✅ Faoliyat timeline
7. ✅ Block-based automation builder
8. ✅ AmoCRM import
9. ✅ OnlinePBX integratsiyasi
10. ✅ Test coverage ≥ 80%
