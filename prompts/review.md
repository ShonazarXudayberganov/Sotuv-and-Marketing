# Code review

> PR review uchun Claude Code'ga shu prompt'ni bering.

---

## Prompt shabloni:

```
PR #[N] review qilish kerak.

**Branch:** feature/[...]
**Vazifa:** [TODO.md dagi vazifa kodi, masalan B5]
**Modul:** [...]

Iltimos:
1. Branch'ni view qil yoki diff'ni o'qi
2. Quyidagilarni tekshir:
   - ✅ Konvensiyalarga rioya (docs/02-conventions.md)
   - ✅ Test mavjudligi va sifati
   - ✅ Multi-tenancy izolyatsiya buzilmagan
   - ✅ Type hints / strict mode
   - ✅ Error handling
   - ✅ Performance (N+1 query, indexes)
   - ✅ Xavfsizlik (SQL injection, XSS, secret leak)
   - ✅ UI luxury theme (frontend bo'lsa)
   - ✅ Hujjatlanish (docstrings, README/CLAUDE.md update)
3. Topilgan muammolarni:
   - 🔴 BLOCKER (merge bo'lmaydi)
   - 🟡 MAJOR (yaxshi bo'lardi tuzatilsa)
   - 🟢 MINOR (tavsif uchun)
4. Tasdiqlash yoki o'zgartirish kerakligini ayt.
```

---

## Auto-review checklist (har PR):

- [ ] Test qo'shilganmi?
- [ ] Coverage tushib ketmadi?
- [ ] Linter xato yo'qmi (ruff, mypy, eslint)?
- [ ] CI green?
- [ ] CHANGELOG.md yangilandi?
- [ ] Kerakli ADR yozildi?
- [ ] DB migration yoziddi (DB o'zgarishi bo'lsa)?
- [ ] Migration rollback testlandi?
- [ ] Multi-tenancy buzilmadi (test bo'lsin)?
- [ ] AI integration token sarfini hisoblay oladimi?
- [ ] Frontend luxury theme'ga moslashtirilganmi?
- [ ] Mobile responsive (frontend)?
- [ ] Accessibility (WCAG AA)?
