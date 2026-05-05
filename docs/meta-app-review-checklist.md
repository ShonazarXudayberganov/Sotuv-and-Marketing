# Meta App Review Checklist

> Holat: 2026-05-05 kuni official Meta docs bilan tekshirildi. Bu fayl checklist;
> app review'ning o'zi hali yuborilgan deb hisoblanmaydi.

## Maqsad

`meta_app` integratsiyasini development/test rejimidan production review va real
customer OAuth holatiga chiqarish.

## Official manbalar

- Meta App Review:
  `https://developers.facebook.com/docs/resp-plat-initiatives/individual-processes/app-review/`
- Meta Permissions Reference:
  `https://developers.facebook.com/docs/permissions/reference/`

## Repo ichidagi tayyor artefaktlar

- reviewer runbook:
  [docs/smm-reviewer-environment.md](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/docs/smm-reviewer-environment.md)
- demo seed script:
  [scripts/seed_smm_reviewer_demo.py](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/scripts/seed_smm_reviewer_demo.py)

## Hozir kodda so'raladigan OAuth scope'lar

- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`
- `instagram_basic`
- `instagram_content_publish`

Izoh:

- `business_management` scope ro'yxatdan olib tashlandi. Joriy Nexus AI flow'ida
  Business Manager asset boshqaruvi yo'q, Meta esa keraksiz permission so'rash
  review reject bo'lishining keng tarqalgan sababi ekanini ochiq aytadi.
- Meta permission reference hozir `instagram_content_publish` uchun
  `instagram_basic`, `pages_read_engagement`, `pages_show_list` dependency'larini
  ko'rsatadi.
- Meta permission reference hozir `pages_manage_posts` uchun
  `pages_read_engagement` va `pages_show_list` dependency'larini ko'rsatadi.
- Meta permission reference hozir `pages_read_engagement` uchun
  `pages_show_list` dependency'sini ko'rsatadi.

## App review'dan oldin tayyor bo'lishi kerak

1. **Business Verification**
   - Meta docs bo'yicha Advanced Access uchun Business Verification talab etiladi.
   - App review yuborishdan oldin business verification completed holatida bo'lsin.

2. **Reviewer kira oladigan demo muhit**
   - Production callback URL HTTPS bilan ishlasin.
   - Reviewer uchun login ishlasin.
   - Demo tenant ichida tayyor brend, post draft va ulangan sahifa bo'lsin.
   - Reviewer flow davomida local tunnel yoki vaqtinchalik session talab qilinmasin.

3. **Meta account prerequisites**
   - Test qilinadigan Facebook user Page admin bo'lsin.
   - Instagram akkaunt Business yoki Creator bo'lsin.
   - Instagram akkaunt Facebook Page bilan bog'langan bo'lsin.

4. **Permission bo'yicha aniq use-case**
   - `pages_show_list`: foydalanuvchiga boshqaradigan Page'larni ko'rsatish va
     to'g'ri Page tanlatish.
   - `pages_read_engagement`: Page metadata va mavjud holatni o'qish.
   - `pages_manage_posts`: Facebook Page post yaratish.
   - `instagram_basic`: Instagram Business profil metadata'sini olish.
   - `instagram_content_publish`: Instagram feed photo/video publish qilish.

5. **Reviewer ko'radigan end-to-end flow**
   - Sozlamalarda `app_id` + `app_secret` kiritiladi.
   - `/settings/integrations` ichida `Meta OAuth` boshlanadi.
   - Callback muvaffaqiyatli tugaydi.
   - `/smm/social` ichida Page list ko'rinadi va account link qilinadi.
   - `/smm/posts` yoki publish flow orqali haqiqiy Facebook post yuboriladi.
   - Instagram feed publish muvaffaqiyatli ishlashi ko'rsatiladi.
   - Publish status sync va oxirgi holat UI'da ko'rinadi.

6. **Submission hygiene**
   - Faqat real ishlatilayotgan permission'larni yuboring.
   - Reels/Story hali ishlab bo'lmagan bo'lsa ular uchun permission/use-case
     yuborilmasin.
   - Review note ichida reviewer qaysi foydalanuvchi bilan kirishi, qaysi menu'ga
     o'tishi va qaysi test postni publish qilishi aniq yozilsin.

## Dry-run paytida tekshiriladigan risklar

- OAuth callback URL exact match bo'lyaptimi
- `user_access_token` saqlanib, Page token qayta olinayaptimi
- `POST /api/v1/integrations/meta_app/oauth/finish` dan keyin
  `oauth_connected=true` qaytyaptimi
- `/api/v1/social-accounts/meta/pages` list real sahifalarni qaytaryaptimi
- Publish xatosi bo'lsa event log va retry metadata to'lyaptimi

## Ochiq qolayotgan ishlar

- IG formatlari hali to'liq emas: Reels va Story alohida production flow sifatida
  bitmagan.
- Real production reviewer environment hali tayyorlanishi kerak.
- Meta permission reference hozir `instagram_basic` uchun
  `pages_read_user_content` dependency'sini ko'rsatadi. Loyiha bu scope'ni hozir
  so'ramayapti; real app review dry-run paytida alohida talab qilinsa, faqat o'sha
  vaqtda qo'shilsin.
