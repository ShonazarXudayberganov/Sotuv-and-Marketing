# Modul 04 — Inbox (Omnikanal yagona xabarlar)

> Barcha kanallar bitta joyda: IG DM, FB Messenger, Telegram, sayt widget, SMS.
> 3 ta AI engine: sentiment, auto-respond, draft creator.
> Bosqich 2 da quriladi.

---

## Sahifalar

```
💬 Inbox
├─ 💬 Suhbatlar         /inbox
├─ 📋 Shablonlar        /inbox/templates
├─ 🤖 AI sozlash         /inbox/ai-settings
├─ 📊 Tahlil            /inbox/analytics
└─ ⚙️ Sozlamalar         /inbox/settings
```

---

## Kanallar (MVP)

| Kanal | Texnik |
|---|---|
| Instagram DM | Meta Graph API |
| Facebook Messenger | Meta Graph API |
| Telegram | Bot API (kompaniya boti) |
| Sayt widget | **Alohida server** (sizning tanlovingiz), WebSocket |
| SMS | Eskiz, Playmobile |
| WhatsApp Business | Bosqich 4 |

---

## Layout (3-pane)

```
┌─────────────┬───────────────────┬─────────────┐
│  SUHBATLAR  │      DIALOG       │ MIJOZ INFO  │
│             │                   │             │
│ 🟢 Akmal K. │  [Ism]            │ [Avatar]    │
│   IG · 2 daq│  💬 IG · Online   │ Akmal K.    │
│   "Soat..." │                   │ +998 90...  │
│             │  ─ Salom!         │             │
│ 🟡 Sardor M │  Soat nechida     │ AI Score:65 │
│   TG · 5 daq│  ish boshlaysiz?  │             │
│   "Narxlar" │                   │ 📋 Bitimlar │
│             │  ✓ Bizda 09:00    │ 1 ta faol   │
│ ⚫ Dilfuza  │  dan 21:00 gacha  │             │
│   FB · 1 s  │                   │ 📜 Tarix    │
│             │  ─ Rahmat         │ 5 ta xabar  │
│             │                   │             │
│             │  [📎][🎤][😀]     │ 🤖 AI Insight│
│             │  [Yozing...]  [►] │ "Bog'lanish │
│             │                   │ ehtimoli yu-│
│             │  💡 AI taklifi:   │ qori (78%)" │
│             │  "Salom! Biz..."  │             │
│             │  [Foydalanish]    │             │
└─────────────┴───────────────────┴─────────────┘
```

Filterlar: kanal, status, mas'ul, sentiment, sana, prioritet.

---

## 3 ta AI engine

### 1. Sentiment Engine (har xabar)

Real-time har kelgan xabar tahlil:
- 😊 Ijobiy
- 😐 Neytral
- 😟 Negativ
- 🚨 Tahdid (urgent flag — admin'ga bildirishnoma)

Daraja: 0-100 (kuchli ijobiy → kuchli negativ).

### 2. Auto-Respond Engine

AI **90% confidence** bo'lganda avtomatik javob beradi (sizning tanlovingiz).
Past confidence — Draft Creator'ga o'tadi.

Mezonlar:
- Bilimlar bazasidan aniq javob bor
- Sentiment neytral yoki ijobiy
- Sodda savol (narx, ish vaqti, manzil)

Sozlamalar:
- Faqat ish soatlarida
- Faqat ma'lum kanallarda
- Faqat ma'lum savol turlariga
- AI avtonomiya darajasi (slider 0-100)

### 3. Draft Creator Engine

Operator dialog ochganda — AI **darhol javob qoralasini yaratadi**:

```
[Mijoz xabari]: "Salomatlik haftasida narx qanday?"

💡 AI takliflari:
1. "Salom! Salomatlik haftasida 25% chegirma..."
2. "Hurmatli mijoz, hozir bizda maxsus aksiya..."
3. "Salomatlik haftasi munosabati bilan..."

[Foydalanish] [Tahrir] [Boshqa variant]
```

---

## Shablonlar

Tez javoblar uchun, hashtag bilan: `#salom`, `#narx`, `#manzil`.

Multi-til (uz lotin / uz kirill / ru). Variabllar: `{ism}`, `{kompaniya}`,
`{vaqt}`, `{summa}`.

Rich content: matn + emoji + rasm + button.

---

## Komanda hamkorlik

- Suhbatni boshqa xodimga o'tkazish (handover)
- Notes (mijoz ko'rmaydigan ichki yozuvlar)
- @mention boshqa xodimni
- Internal chat dialog ostida

---

## SLA

Per-platforma sozlama:
- IG DM: 1 soat
- TG: 30 daqiqa
- Sayt widget: 5 daqiqa

Buzilganda — bildirishnoma + Telegram alert.

---

## CRM bilan bog'lanish

Yangi mijozdan xabar kelsa:
1. Telefon raqami CRM'da qidiriladi
2. Topilsa → mavjud kontaktga timeline'ga qo'shiladi
3. Topilmasa → "Yangi mijoz, qo'shamizmi?" modal

Har xabar mijoz timeline'da ko'rinadi.

---

## DB jadvallar

- `conversations`
- `messages`
- `templates`
- `ai_settings_inbox`
- `sla_rules`

---

## Acceptance (Bosqich 2)

1. ✅ 5 kanal (IG, FB, TG, sayt widget, SMS)
2. ✅ Sayt widget alohida serverda
3. ✅ 3 AI engine (sentiment, auto-respond, draft)
4. ✅ AI auto-respond 90% confidence threshold
5. ✅ Shablonlar (hashtag bilan)
6. ✅ Komanda hamkorlik (handover, mention, internal chat)
7. ✅ SLA monitoring
8. ✅ CRM bilan integratsiya
9. ✅ Test coverage ≥ 80%
