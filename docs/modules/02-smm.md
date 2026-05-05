# Modul 02 — SMM Assistenti (MVP — birinchi modul)

> Bu **Bosqich 1 (MVP)** uchun birinchi va asosiy modul. Bizning eng kuchli
> farqlovchi tomon — o'zbek tilida AI bilan kontent yaratish.

---

## Maqsad

Multi-brand kontent yaratish va e'lon qilish ekotizimi. AI bilimlar bazasidan
kontent yaratadi, foydalanuvchi tahrirlaydi, IG/FB/TG/YT ga publish qiladi.

---

## Sahifalar

```
✍️ SMM
├─ 🏠 Dashboard         /smm
├─ 🎨 Brendlar          /smm/brands
├─ 📚 Bilimlar bazasi   /smm/knowledge-base
├─ ✨ Studio             /smm/studio
├─ 📅 Kontent rejasi    /smm/content-plan
├─ 📤 E'lonlar          /smm/publishing
├─ ✅ Tasdiqlash        /smm/approvals
├─ 📊 Tahlil            /smm/analytics
├─ 🔥 Trendlar          /smm/trends           [Bosqich 4]
├─ 🕵️ Raqobatchilar    /smm/competitors      [Bosqich 4]
├─ 🎯 Brend assets      /smm/brand-assets
└─ ⚙️ Sozlamalar        /smm/settings
```

---

## 1. Multi-brand arxitekturasi

**Brend = mustaqil "olam":** o'z bilimlar bazasi, ijtimoiy akkauntlari, kontent
rejasi, brend assets, auditoriya va tahlili.

Bir kompaniya **5+ brend** bilan ishlay oladi (agentlik holati uchun).

Yuqori header'da brend tanlash dropdown.

### Brend yaratish wizard (5 qadam)

**1. Asosiy:**

- Nomi
- Soha (dropdown)
- Tavsif (textarea)
- Logo

**2. Bilimlar bazasini qanday to'ldirasiz:**

- 📝 Qo'lda
- 📄 Fayl yuklash (PDF/Word/Excel/PowerPoint)
- 🌐 Saytdan parsing
- 📱 Instagram'dan import (oxirgi 50-100 post tahlil)
- 💬 AI bilan suhbat (savol-javob)

**3. Ijtimoiy akkauntlarni ulash:**

- Instagram Business (OAuth)
- Facebook Page (OAuth)
- Telegram channel (bot orqali)
- YouTube channel (OAuth)

**4. Brend assets:**

- Logo (asosiy + variantlar)
- Ranglar (HEX kod)
- Fontlar (kelgusi posterlar uchun)
- Vizual stil (referenslar)

**5. Tayyor:**

- "AI bazani tahlil qilmoqda... (~2 daqiqa)"
- [Birinchi postni yaratish →]

---

## 2. Bilimlar bazasi (eng muhim sahifa)

8 ta bo'lim, har bo'lim uchun progress bar:

### Bo'limlar

| #   | Bo'lim                      | Mazmun                                                                                                       |
| --- | --------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | Kompaniya haqida            | Nomi, missiya, vizyon, tarixi, qadriyatlar, brend hikoyasi                                                   |
| 2   | Mahsulot/Xizmatlar          | Har biri: nomi, kategoriya, tavsif, narxi, afzalliklari, foto/video. CRM Mahsulot katalogi bilan **sinxron** |
| 3   | Maqsadli auditoriya         | Persona avatar(lar): yosh, jinsi, daromad, joylashuv, qiziqishlar, og'riq nuqtalari                          |
| 4   | Brend ovozi (Tone of Voice) | Xarakter (3-5 sifat), ohanglar, stop-words, yozish uslubi, misol postlar                                     |
| 5   | Raqobatchilar               | Har biri: nomi, akkauntlar, kuchli/zaif tomonlari                                                            |
| 6   | FAQ                         | Savol-javob juftliklar (kontent g'oyalari uchun)                                                             |
| 7   | Aktsiyalar va chegirmalar   | Doimiy va vaqtinchalik (sana oralig'i)                                                                       |
| 8   | Manba materiallar           | Brand book (PDF), eski reklama postlar, mediya                                                               |

### To'ldirish 4 yo'li

**1. AI bilan suhbat:**

```
AI: Salom! Avval kompaniyangiz nima qiladi va siz kimga sotasiz?
User: Biz ayollar uchun salon ochganmiz, asosan 25-45 yosh ayollar...
AI: Ajoyib! Salonda qanday xizmatlar bor?
User: Soch kesish, bo'yash, manikyur, qoshlar...
[real-time bilimlar bazasi to'ldiriladi]
```

**2. Fayl yuklash:**

- PDF/Word/Excel/PowerPoint
- AI tahlil qiladi
- Kerakli ma'lumotlarni chiqarib oladi
- Foydalanuvchiga preview ko'rsatadi
- ✅ Tasdiqlash → bazaga qo'shiladi

**3. Saytdan parsing:**

- URL kiritiladi
- AI sayt o'qib (web crawler — Bosqich 1 da oddiy fetch + parsing)
- "Biz haqimizda", narxlar, xizmatlar, aloqa ekstrakt qilinadi
- Foydalanuvchi tasdiqlaydi

**4. Instagram import:**

- Akkaunt ulangan bo'lishi kerak
- Oxirgi 50-100 post tahlil
- Brend ovozi, mavzular, asosiy ranglar (Vision API) ekstrakt
- Fayl 4 da bilimlar bazasiga qo'shiladi

### AI proaktiv

```
🔔 "Sizning narxlar 2 oydan beri o'zgarmagan, yangilash kerakmi?"
🔔 "Auditoriya bo'limi 3 oy davomida yangilanmagan"
```

### Texnik (RAG)

Har bo'lim bo'laklarga (chunk) ajratiladi → embedding (OpenAI) → pgvector.

```python
async def update_knowledge_section(brand_id: int, section: int, content: str):
    chunks = split_into_chunks(content, max_tokens=500)
    for chunk in chunks:
        embedding = await openai.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        )
        await db.execute(
            insert(KnowledgeBase).values(
                brand_id=brand_id,
                section=section,
                content=chunk,
                embedding=embedding.data[0].embedding
            )
        )
```

---

## 3. AI Studio (`/smm/studio`)

Eng muhim sahifa. Bu yerda kontent yaratiladi.

### Smart Wizard (faqat 2-3 savol)

**1. Mavzu:** matn yozish yoki AI tezkor g'oyalardan tanlash:

```
- Mahsulot/xizmat reklama
- Bayram tabriki
- Aktsiya/chegirma
- Education (ta'lim post)
- Behind the scenes
- ...
```

**2. Platforma va format:**

```
☑ Instagram   → ○ Post  ○ Reels  ○ Story
☑ Telegram    → matn + rasm
☐ YouTube     → ○ Video  ○ Shorts
☐ Facebook
```

**3. Maqsad:**

- 🎯 Sotuv
- 📢 Tanishtirish
- 💬 Engagement
- 🎓 Ta'lim
- ◯ Auto (AI o'zi tanlaydi)

Avtomatik baza'dan: ohang, auditoriya, til, hashtaglar, brend ovozi, mahsulot
tafsilotlari, CTA stili.

### Studio interfeysi

```
┌──────────────┬───────────────────────────┬────────────────┐
│  VARIANTLAR  │       PREVIEW             │   AI YORDAM    │
│              │                           │                │
│ ○ Variant A  │  [Instagram preview]      │ Tezkor:        │
│ ● Variant B  │                           │ - Qisqartir    │
│ ○ Variant C  │                           │ - Uzaytir      │
│              │                           │ - Hazilroq     │
│ [+ Yana]     │                           │ - Rasmiyroq    │
│              │                           │ - Boshqa CTA   │
│              │  [Rich text editor]       │ - Qaytadan yoz │
│              │                           │                │
│              │  Hashtag: 30 avto         │ 💬 AI Chat     │
│              │                           │                │
└──────────────┴───────────────────────────┴────────────────┘

[← Bekor]    [💾 Qoralama]    [📅 Rejaga]    [📤 E'lon qil]
```

### 3 ta variant

AI default 3 variant yaratadi (boshqacha yondashuvlar bilan):

1. **Qisqa va energichno** — 50-100 so'z
2. **Hikoya tarzida** — 150-250 so'z
3. **Ekspert maslahati** — list shaklida

[+ Yana variant] tugmasi (Variant B yondashuv) — 4-chi variant uchun token sarflanadi.

### Tahrirlash usullari

1. **Inline edit** — matnni to'g'ridan-to'g'ri o'zgartirish
2. **Tezkor tugmalar** — Qisqartir, Uzaytir, Hazilroq, ...
3. **Parchani belgilab "Yaxshila"** — selection menyu
4. **AI Chat** — "Bu paragrafni qaytadan yoz, lekin..."
5. **Versiya tarixi** — har o'zgarishni saqlaydi (undo cheksiz)

### Vizual kontent

**Variant C strategiyasi (sizning tanlovingiz):**

1. AI rasm prompti yaratadi → [🖼 AI'da yarating] → **GPT image** chaqiruvi
2. Foydalanuvchi o'z rasmini yuklaydi
3. Brend assets bazasidan tanlash
4. AI brend assets bazasidan eng mosini taklif qiladi

### Hashtag avto-generatsiya

30 ta hashtag (Instagram limiti):

- Mahalliy (5-7): #toshkent #ozbekiston
- Sohaviy (5-10): #sochstilist #salon
- Mavzuviy (3-5)
- Brend (1-2): #akmesalon
- Trend (2-3, real-time — Bosqich 4)

### Reels/Story ssenariy

```
🎬 REELS SSENARIY
─────────────────
00:00 - 00:03 (HOOK)
"Yozda sochlar nega tushadi? Sabab — bu..."
[Vizual: kamera ayolga zoom]

00:03 - 00:10 (PROBLEM)
"Quyosh, xlorli suv, namlik..."
[Vizual: 3 kadr montaj]

00:10 - 00:25 (SOLUTION)
"Mana 3 ta oddiy qoida..."
[Vizual: matn overlay]

00:25 - 00:30 (CTA)
"To'liq ko'rsatma — bio link"
[Vizual: yopiluvchi kadr]

🎵 Tavsiya: trending audio
📝 Caption: ...
```

---

## 4. Kontent rejasi (`/smm/content-plan`)

3 ta ko'rinish:

### 📅 Kalendar

Oylik grid. Har kun ostida nechta post (rangli ikonlar IG/TG/YT).

Ranglar:

- 🔵 Qoralama
- 🟡 Rejalashtirilgan
- 🔴 Tasdiqlash kutyapti
- 🟢 E'lon qilingan
- ⚫ Xato

Drag & drop boshqa kunga.

### 📋 Ro'yxat

Jadval: Sana, Vaqt, Format, Sarlavha, Platform, Mas'ul, Status, Harakatlar.
Filter va sort.

### 🗂 Kanban

5 ustun: 💡 G'oya · ✍ Yaratilmoqda · 👁 Tasdiq · ✅ Tayyor · 🟢 E'lon.

### AI 30 kunlik reja

Wizard:

1. Davr (hafta / 30 kun / 90 kun)
2. Maqsadlar (multi-select: brend, sotuv, trafik, audience)
3. Tezislar (ixtiyoriy: "yangi xizmat chiqaramiz")
4. Format taqsimoti (AI tavsiya: 60% Reels, 30% Post, 10% Story)
5. Chastota (AI: "Sohangiz uchun haftada 4 post + 7 story optimal")

Natija: 30 ta g'oyalar ro'yxati. Foydalanuvchi tasdiqlaydi → birinchi 5-7 ta
to'liq matn darhol, qolganlari 5-7 kun oldin (token tejash).

Status: `content_plans` item modeli, CRUD API, AI reja matnini itemlarga import
qilish, itemdan post yaratish va web UI'da calendar/list/kanban view mavjud.
Keyingi hardening: to'liq wizard savollari va auto-generation scheduling.

---

## 5. Publishing (`/smm/publishing`)

### Per-post tanlov

- 🤖 **Avtomatik** — vaqti kelganda tizim API orqali yuboradi
- 👤 **Qo'lda** — mas'ulga bildirishnoma + [E'lon qilish] tugma

### Platformalar (MVP)

- **Instagram:** post + Reels + Story (Meta Graph API)
- **Telegram:** kanal post (Bot API)
- **Facebook:** page post (Meta Graph API)
- **YouTube:** video upload (Data API) — Bosqich 1 oxirida

### Cross-posting

Bitta post → bir nechta platforma. Har birida avto-moslashish:

- IG: to'liq matn + 30 hashtag
- TG: matn + 5 hashtag
- FB: matn (cropped 60 belgi preview)

### Multi-account

Bir brend → bir nechta IG (asosiy + filiallar), bir nechta TG bot.

### Optimal vaqt

AI auditoriya faolligini tahlil qiladi (Insights API'dan) va eng yaxshi soatni
taklif qiladi.

### Xato boshqaruvi

Publish bo'lmasa retry: 5 daq → 30 daq → 1 soat. Status ⚠ + bildirishnoma + Telegram.

2026-05-05 implementatsiya holati:

- `post_publications` endi `last_attempt_at`, `remote_status`, `last_checked_at`,
  `permanent_failure` maydonlarini saqlaydi.
- `post_publication_events` append-only logi har publish urinish, retry, xato va
  status sync natijasini yozadi.
- `POST /api/v1/posts/:id/sync-status` published platform holatini qayta
  tekshiradi; `/smm/posts` sahifasida platform tafsilotlari va oxirgi xato
  ko'rinadi.
- `POST /api/v1/integrations/meta_app/oauth/start` va
  `POST /api/v1/integrations/meta_app/oauth/finish` qo'shildi; frontend callback
  route `/settings/integrations/meta/callback` orqali Meta OAuth yakunlanadi.
- Meta production checklist `docs/meta-app-review-checklist.md` ga kiritildi;
  OAuth scope ro'yxatidan ishlatilmayotgan `business_management` olib tashlandi.
- Reviewer staging oqimi uchun seed script va runbook qo'shildi:
  `scripts/seed_smm_reviewer_demo.py` va `docs/smm-reviewer-environment.md`.
- Meta token auth xatosida saqlangan `user_access_token` bo'lsa Page token qayta
  olinadi va publish bir marta qayta uriniladi.

---

## 6. Tasdiqlash workflow (`/smm/approvals`)

**Sozlamalardan yoqilgan bo'lsa.** Sizning tanlovingiz: kompaniya o'zi sozlasin —
kim tasdiqlay oladi (rollar yoki konkret xodim).

### Sahifa ko'rinishi

```
┌─────────────────────────────────────────────────┐
│  Tasdiqlash kutmoqda (3)                        │
├─────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ [Preview]│  │ [Preview]│  │ [Preview]│      │
│  │ Post #15 │  │ Reels #2 │  │ Story    │      │
│  │ IG, TG   │  │ IG only  │  │ IG       │      │
│  │ Sardor   │  │ Dilfuza  │  │ Akmal    │      │
│  │ 2 soat   │  │ 5 soat   │  │ 1 kun    │      │
│  │  oldin   │  │  oldin   │  │  oldin   │      │
│  │ [👁][✏][❌][✅]│ ...     │              │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
```

Modal ochilganda:

- To'liq preview
- Matn (read-only yoki edit imkoniyat)
- [✅ Tasdiqlash] / [💬 Izoh va qaytarish] / [❌ Rad etish]

---

## 7. Tahlil (`/smm/analytics`)

| Bo'lim                | Tarkib                                                   |
| --------------------- | -------------------------------------------------------- |
| Yuqori KPI            | Reach · Engagement Rate · Follower o'sishi · Saytga klik |
| Vaqt grafigi          | Har kun reach, engagement, followers (line chart)        |
| Eng yaxshi postlar    | Top 10 (engagement bo'yicha) — thumbnail + statistika    |
| Eng yomon postlar     | Past natija + AI "nima uchun"                            |
| Format taqqoslash     | Post vs Reels vs Story (bar chart)                       |
| Vaqt heatmap          | Kun × soat — qachon eng faol                             |
| Hashtag samaradorligi | Yaxshi va kuchsiz hashtaglar                             |
| AI Insights           | "Hazil postlar 2.3x ko'p engagement"                     |

### AI o'rganish (eng kuchli xususiyat)

Insights avto kontent yaratishga ta'sir qiladi — AI keyingi postlarni shunga
moslab yaratadi (yaxshi natija bergan postlardan kontekst — RAG).

```python
async def generate_post_with_learning(brand_id: int, prompt: str):
    # Get top 10 best performing posts
    best_posts = await get_top_posts(brand_id, limit=10)

    # Build context
    context = "Best performing posts examples:\n"
    for post in best_posts:
        context += f"- {post.content[:200]}... (engagement: {post.engagement})\n"

    # Generate with examples in system prompt
    response = await claude.messages.create(
        model="claude-sonnet-4",
        system=f"You are a social media expert. {context}",
        messages=[{"role": "user", "content": prompt}]
    )
```

---

## 8. Trendlar (`/smm/trends`) — Bosqich 4

- O'zbekiston bugungi trendlari (top 30 hashtag real-time)
- Trend audio (Reels)
- Trend mavzular
- Sizning sohangiz trendlari (AI brend bazasidan filtrlaydi)
- Trend taqvimi (bayramlar — 15 kun oldin tayyorlay boshlaydi)
- [Postga aylantir] tugmasi

---

## 9. Raqobatchi tahlili (`/smm/competitors`) — Bosqich 4

3-5 raqobatchi qo'shish (IG @, sayt, TG kanal). Haftalik tahlil:

- Postlar soni
- Engagement rate
- Asosiy mavzular
- Eng yaxshi postlar
- Format taqsimoti
- Hashtag strategiya

**Sizning tanlovingiz: engagement statistikasi ham olinadi** (Meta Ad Library +
ochiq postlardan like/comment/view).

---

## 10. Brend assets (`/smm/brand-assets`)

- Logo galereyasi (asosiy + variantlar)
- Ranglar palitrasi (HEX, RGB)
- Fontlar (yuklash, preview)
- Vizual stil (referenslar, mood board)
- Tayyor shablonlar (post, story, reels)
- Mediya zaxirasi (rasm, video — kelgusi postlar uchun)

Status: backend `brand_assets` jadvali, `/api/v1/brand-assets` CRUD/upload API,
`/api/v1/brands/:id/assets` contract endpointlari va web UI mavjud. Upload
qilingan fayllar hozircha tenant ichida data URL sifatida saqlanadi; production
storage/S3 keyingi hardening qismida ajratiladi.

---

## DB jadvallar

To'liq: [../04-database-schema.md](../04-database-schema.md#smm-modul-jadvallari)

- `brands`
- `knowledge_base` (pgvector!)
- `social_accounts` (encrypted tokens)
- `posts`
- `post_variants`
- `post_metrics`
- `content_plans`
- `brand_assets`
- `competitors` (Bosqich 4)
- `trends` (Bosqich 4)

---

## API endpoints

To'liq: [../05-api-contracts.md](../05-api-contracts.md#smm)

Asosiy:

- `/api/v1/brands`
- `/api/v1/brands/:id/knowledge-base`
- `/api/v1/ai/generate-content` (3 variant)
- `/api/v1/ai/improve-content` (tezkor tahrir)
- `/api/v1/ai/generate-plan` (30 kunlik)
- `/api/v1/posts` (CRUD)
- `/api/v1/posts/:id/publish`
- `/api/v1/posts/:id/schedule`
- `/api/v1/posts/:id/metrics`
- `/api/v1/brand-assets` (CRUD + filter)
- `/api/v1/brand-assets/upload`
- `/api/v1/brands/:id/assets` (contract list/upload/delete)

---

## AI promptlar

`apps/api/app/ai/prompts/` papkasida:

```
post_generator.txt         # Asosiy post yaratish prompt
improve_content.txt        # Tahrir
ai_chat.txt                # AI chat yordamchi prompti
generate_30_day_plan.txt   # Reja
generate_hashtags.txt      # Hashtag generatsiya
generate_reels_script.txt  # Reels ssenariy
system_guardrails.txt      # Draft generatsiya guardrail'i
assistant_guardrails.txt   # Yordamchi AI guardrail'i
```

Target bajarildi: AI Studio yordamchi promptlari ham alohida prompt fayllariga
chiqarildi va render helper orqali yuklanadi.

---

## Acceptance kriteriylari (Bosqich 1 — MVP)

2026-05-05 holatiga ko‘ra bu ro‘yxat yakuniy target, quyidagi status bilan:

1. ✅ Brend yaratish wizard (5 qadam) — Brand CRUD + `/smm/brands` create/edit wizard bor
2. ✅ Bilimlar bazasi 8 bo‘lim, 4+ to‘ldirish usuli — 8 section + progress UI + text/file/website/IG/AI chat import + pgvector bor
3. ✅ AI Studio: 3 variant + AI chat + tezkor tahrir — API/UI bor, draftlar saqlanadi
4. ✅ Hashtag avto-generatsiya — `/ai/generate-hashtags` + UI
5. ✅ AI 30 kunlik reja — `/ai/generate-30-day-plan` + UI
6. ✅ Kontent rejasi (3 ko‘rinish) — `/smm/content-plan` calendar/list/kanban, AI import va postga aylantirish bor
7. 🟡 Publishing: IG (post+Reels+Story) + TG + FB — Telegram/Meta test/publish flow bor; retry event log, status sync, token refresh, Meta OAuth callback, app review checklist va reviewer seed/runbook bor; post `content_format` contracti (`feed/reels/story`), create UI va Meta adapterda format-aware container payload qo‘shildi; real Meta smoke verification va app review submission hali tugallanmagan
8. ✅ Tasdiqlash workflow — review/approve/reject API + posts UI actionlari bor
9. 🟡 Asosiy tahlil (post statistikasi, AI o‘rganish) — analytics bor, AI learning hali yo‘q
10. ✅ Brend assets boshqaruvi — CRUD/upload API + `/smm/brand-assets` UI bor
11. 🟡 Multi-brand to‘g‘ri ishlaydi (chegaralash) — brand scope bor, membership/access boundary hardening kerak
12. ✅ Test coverage ≥ 80% — backend coverage 83.05%

---

## Bu modul YO'Q (keyingi bosqichlarda)

- ❌ AI rasm generatsiyasi (faqat prompt beradi MVP'da, GPT image — Bosqich 4)
- ❌ Trend tracker (Bosqich 4)
- ❌ Raqobatchi to'liq tahlili (Bosqich 4)
- ❌ A/B test (Bosqich 4)
- ❌ AI Voice o'rganish chuqur (Bosqich 4)
- ❌ YouTube full integratsiya (Bosqich 1 oxirida boshlanadi)

---

## Tegishli fayllar

- [00-foundation.md](00-foundation.md) — Auth, multi-tenancy, RBAC
- [../06-ai-strategy.md](../06-ai-strategy.md) — AI integratsiya
- [../03-design-system.md](../03-design-system.md) — UI tili
- [../roadmap/phase-1.md](../roadmap/phase-1.md) — Bosqich 1 batafsil
