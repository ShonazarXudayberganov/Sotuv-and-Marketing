# Bug topish va tuzatish

> Bug paydo bo'lganda — Claude Code'ga shu prompt'ni bering.

---

## Prompt shabloni:

```
NEXUS AI'da bug topdim.

**Modul:** [...]
**Sahifa/endpoint:** [...]
**Xato turi:** [Frontend / Backend / DB / Integration]

**Kutilayotgan harakat:**
[Nima sodir bo'lishi kerak edi]

**Haqiqiy harakat:**
[Nima sodir bo'lyapti]

**Reproduce qilish qadamlari:**
1. ...
2. ...
3. ...

**Xato xabari (logs):**
```
[stack trace yoki konsol output]
```

**Environment:**
- Local / Staging / Production
- Browser (frontend bo'lsa)
- User role

Iltimos:
1. Tegishli fayllarni topib, kodni o'qi
2. Root cause'ni aniqlashtir (taxmin emas, isbot bilan)
3. Fix variantlarini taklif qil
4. Test yoz (avval — bug'ni reproduce qiluvchi test, keyin tuzatish)
5. Tasdiqlasam — fix qil.
```

---

## Misol:

```
NEXUS AI'da bug.

**Modul:** SMM
**Sahifa:** /smm/studio
**Xato turi:** Backend

**Kutilgan:** AI 3 variant qaytarishi kerak
**Haqiqiy:** Faqat 1 variant qaytmoqda, qolgan 2 si "null"

**Reproduce:**
1. Brand tanlash
2. "Yangi post" tugmasi
3. Mavzu: "Salomatlik haftasi"
4. [Variantlarni yarat] tugmasi
5. Faqat A variant ko'rinadi, B va C — null

**Logs:**
ERROR: KeyError: 'variant_b' in /api/v1/ai/generate-content

**Environment:** Staging, Pro tenant

Tahlil qil va fix taklif qil.
```
