# Yangi xususiyat qo'shish

> Yangi feature qo'shish kerak bo'lganda — Claude Code'ga shu prompt'ni bering.

---

## Prompt shabloni:

```
NEXUS AI ga yangi xususiyat qo'shamiz.

**Modul:** [SMM / CRM / Inbox / ... / Foundation]
**Xususiyat:** [qisqa nom — masalan "Hashtag groups"]
**Tavsif:** [1-2 jumla — nima qiladi]

**Foydalanuvchi hikoyasi:**
"Foydalanuvchi sifatida men [...] qilishni xohlayman, chunki [sabab]."

**Acceptance kriteriylari:**
1. ...
2. ...
3. ...

Iltimos:
1. Avval docs/modules/[modul].md fayli'ni o'qi — tegishli kontekst topi
2. Xususiyatga ta'sir qiladigan boshqa fayllarni topib o'qi (DB, API, UI)
3. Quyidagilarni javob ber:
   - Kerakli o'zgarishlar ro'yxati (DB, API, UI, test)
   - Yangi ADR kerakmi?
   - Texnik xavf
   - Taxminiy hajm (S/M/L/XL)
4. Tasdiqlasam — TDD bilan boshlay (avval test).

Hozircha kod yozma.
```

---

## Misol:

```
NEXUS AI ga yangi xususiyat qo'shamiz.

**Modul:** SMM
**Xususiyat:** Hashtag guruhlari
**Tavsif:** Foydalanuvchi tez-tez ishlatadigan hashtag to'plamlarini saqlab,
keyingi postlarda bir tugma bilan qo'shishi mumkin.

**Foydalanuvchi hikoyasi:**
"SMM menejer sifatida men har post uchun 30 ta hashtag yozish o'rniga, oldindan
saqlangan guruhlardan tanlashni xohlayman."

**Acceptance:**
1. Foydalanuvchi guruh yaratishi mumkin (nom + hashtag list)
2. Har brend uchun cheksiz guruh
3. Post yaratganda guruh tanlash → matnga avtomatik qo'shish
4. Edit / Delete imkoniyat

Iltimos boshlanmaydan oldin tahlil qil va menga rejani ber.
```
