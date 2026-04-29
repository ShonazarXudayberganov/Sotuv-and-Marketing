# Birinchi sessiya — Claude Code uchun starter prompt

> Bu Claude Code'ga birinchi marta loyihani tushunish uchun uzatiladigan prompt.
> Loyiha boshida `claude` ishga tushirib, shu matnni nusxa qilib joylashtiring.

---

## Prompt:

```
Salom! Bu — NEXUS AI loyihasi. Multi-tenant SaaS platforma O'zbekiston bozori
uchun: 6 modul (CRM, SMM, Reklama, Inbox, Hisobotlar, Integratsiyalar).

Iltimos, quyidagi tartibda fayllarni o'qi:

1. CLAUDE.md — loyiha haqida umumiy ma'lumot va konvensiyalar
2. README.md — quick start
3. TODO.md — joriy sprint vazifalari
4. docs/00-overview.md — proyekt overview
5. docs/01-architecture.md — texnik arxitektura
6. docs/02-conventions.md — kod konvensiyalari

O'qib bo'lganingdan keyin menga quyidagilarni ayt:

1. Loyihani o'z so'zlaring bilan 2-3 jumlada tushuntir
2. Joriy bosqich va sprint qaysi
3. Qaysi vazifadan boshlash mantiqiy va nima uchun
4. Birinchi vazifa uchun qaysi qo'shimcha hujjatlarni o'qish kerak

Hozircha hech narsa qilma — faqat tushuntir.
```

---

## Keyingi prompt (vazifa boshlash):

```
Yaxshi! Endi Sprint 1, vazifa B1 (Backend Poetry init va paketlar) ustida
ishlaymiz.

Avval:
1. apps/api/ papkasi mavjud bo'lsa — uning ichini view qil
2. Yo'q bo'lsa — yangi yarat
3. pyproject.toml yarat (Poetry, dependencies CLAUDE.md va docs/01-architecture.md
   da ko'rsatilgan)
4. Asosiy folder strukturasi: app/core/, app/api/, app/models/, app/schemas/,
   app/services/, app/ai/, tests/

Test'larsiz hech narsa yozma — TDD'ga rioya qil.

Boshlanglikmi?
```

---

## Qoidalar:

1. **Har sessiya boshida** — CLAUDE.md va TODO.md o'qisin (claude code o'zi qiladi)
2. **Vazifa boshlashdan oldin** — modul spec va architecture o'qisin
3. **Test yozmasangiz** — vazifa tugamagan deyilmaydi
4. **PR oching** — har feature alohida PR
5. **TODO.md ni yangilab boring** — har sprint
