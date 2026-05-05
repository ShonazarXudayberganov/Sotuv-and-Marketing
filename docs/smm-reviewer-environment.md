# SMM Reviewer Environment

Bu hujjat SMM modulini Meta App Review va staging reviewer demo uchun tayyorlash
oqimini beradi.

## Maqsad

Quyidagi narsalar bir joyda tayyor bo'lsin:

- reviewer kira oladigan login
- demo tenant va demo brand
- tayyor draftlar va content plan itemlari
- optional `meta_app` integration (`app_id` + `app_secret`)
- Meta OAuth, page link va publish smoke-test uchun aniq operator qadamlari

## 1. Public staging prerequisites

Avval staging muhit ishlashi kerak:

- public `https` web URL
- public `https` api URL
- `CORS_ORIGINS` ichida staging web origin bor
- `NEXT_PUBLIC_API_URL` staging API'ga qaragan
- GitHub deploy secrets/variables to'g'ri o'rnatilgan

Infra bazasi README ichida bor:

- [README.md](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/README.md)
- [infra/docker-compose.prod.yml](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/infra/docker-compose.prod.yml)
- [.github/workflows/deploy.yml](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/.github/workflows/deploy.yml)

## 2. Demo tenant seed

Repo ichida reviewer demo seed skript qo'shildi:

- [scripts/seed_smm_reviewer_demo.py](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/scripts/seed_smm_reviewer_demo.py)
- [scripts/check_smm_reviewer_readiness.py](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/scripts/check_smm_reviewer_readiness.py)

Ishlatish:

```bash
cd apps/api
poetry run python ../../scripts/seed_smm_reviewer_demo.py \
  --email reviewer.demo@nexusai.uz \
  --password 'ReviewerDemo123' \
  --full-name 'Reviewer Demo' \
  --company-name 'Nexus AI Reviewer Demo' \
  --brand-name 'Nexus AI Demo Brand' \
  --app-base-url 'https://staging.nexusai.uz' \
  --meta-app-id 'YOUR_META_APP_ID' \
  --meta-app-secret 'YOUR_META_APP_SECRET'
```

Skript nimalarni qiladi:

- owner user yaratadi yoki yangilaydi
- tenant schema yaratadi yoki self-heal qiladi
- default brand yaratadi/yangilaydi
- sample brand assetlar yaratadi
- sample content draftlar yaratadi
- sample content plan itemlar yaratadi
- `meta_app` integration'ga `app_id` + `app_secret` saqlaydi

## 2.1. Readiness smoke-check

Deploy va seed'dan keyin reviewer muhitni quyidagi skript bilan tekshiring:

```bash
python3 scripts/check_smm_reviewer_readiness.py \
  --web-base-url 'https://staging.nexusai.uz' \
  --api-base-url 'https://api-staging.nexus-ai.uz' \
  --email 'reviewer.demo@nexusai.uz' \
  --password 'ReviewerDemo123' \
  --require-meta-connected \
  --require-content-plan
```

Bu skript tekshiradi:

- web `/login`
- web Meta callback route
- API `/health`
- reviewer login
- `/api/v1/integrations`
- `/api/v1/brands`
- `/api/v1/content-plan`

Reviewer OAuth ham tayyor bo'lganidan keyin:

```bash
python3 scripts/check_smm_reviewer_readiness.py \
  --web-base-url 'https://staging.nexusai.uz' \
  --api-base-url 'https://api-staging.nexus-ai.uz' \
  --email 'reviewer.demo@nexusai.uz' \
  --password 'ReviewerDemo123' \
  --require-meta-connected \
  --require-meta-oauth \
  --require-content-plan
```

Izoh:

- Skript OAuth token yaratmaydi. Reviewer yoki operator Meta OAuth'ni UI orqali
  yakunlaydi.
- Skript idempotent. Bir necha marta ishlatilsa duplikat sample row'lar
  ko'paymaydi.

## 3. Reviewer flow

Seed'dan keyin operator quyidagi yo'l bilan staging'ni tayyorlaydi:

1. `/login` ga kiring
2. `/settings/integrations` ga o'ting
3. `Meta OAuth` tugmasini bosing
4. Meta callback muvaffaqiyatli tugaganini tekshiring
5. `/smm/social` ga o'tib kerakli Facebook Page / Instagram Business account'ni link qiling
6. `/smm/posts` yoki AI Studio orqali demo post yarating
7. Real Facebook post publish qiling
8. Real Instagram feed publish qiling
9. `sync-status` va event log UI'da statuslarni tekshiring

## 4. Smoke checklist

Reviewer submissiondan oldin operator shu checklistni yopishi kerak:

- `/settings/integrations` ichida `meta_app.connected=true`
- `oauth_connected=true`
- `/smm/social` ichida Page list real qaytadi
- linked social account `last_error=null`
- `/smm/posts` ichida publish urinish eventlari yoziladi
- publish bo'lgach `remote_status=published`
- xato bo'lsa foydalanuvchi tushunadigan matn chiqadi

## 5. Screencast outline

Meta App Review uchun video shuni ko'rsatsin:

1. Login
2. Integrations sahifasida Meta app konfiguratsiyasi mavjudligi
3. `Meta OAuth` boshlanishi
4. Callback muvaffaqiyatli tugashi
5. `/smm/social` ichida real Page list chiqishi
6. Page/account link qilish
7. `/smm/posts` yoki AI draft'dan demo post ochish
8. Publish bosilishi
9. Facebook yoki Instagram'da post real chiqqanini ko'rsatish
10. Nexus AI ichida publish status va event log ko'rinishi

## 6. Submission note template

Quyidagi matnni submission note uchun asos qilib ishlatish mumkin:

```text
Reviewer login:
Email: reviewer.demo@nexusai.uz
Password: ReviewerDemo123

Use case:
Nexus AI allows a business user to connect the Facebook Pages and Instagram Business
accounts they manage, create marketing content, and publish that content from inside
the application.

Reviewer steps:
1. Sign in with the reviewer demo account.
2. Go to Settings -> Integrations and confirm the Meta integration is configured.
3. Start Meta OAuth and authorize the managed Page / Instagram Business account.
4. Go to SMM -> Social and link the returned Page/account.
5. Go to SMM -> Posts, open a prepared draft or create a short post.
6. Publish the post to Facebook Page or Instagram feed.
7. Return to the post detail and verify the published status and event log.
```

Bu template real staging login va final menu label'lariga moslab yakuniy tahrir
qilinadi.

## 7. Nima hali qo'lda qoladi

Quyidagilar hali manual:

- public HTTPS staging DNS/SSL
- Meta Business Verification
- Meta Advanced Access review submission
- real Page admin account bilan OAuth
- real publish smoke-test videoni yozish

## 8. Bog'liq hujjatlar

- [docs/meta-app-review-checklist.md](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/docs/meta-app-review-checklist.md)
- [docs/modules/02-smm.md](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/docs/modules/02-smm.md)
- [docs/roadmap/phase-1.md](/Users/shonazarxudayberganov/Documents/Sotuv%20and%20marketing%20/nexus-ai-docs/docs/roadmap/phase-1.md)
