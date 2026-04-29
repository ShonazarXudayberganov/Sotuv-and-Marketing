# Modul 00 — Foundation (Tizim asosi)

> Har modul ustida turuvchi umumiy karkas. Bu kod birinchi bo'lib yoziladi —
> har keyingi modul shu poydevorga quriladi.

---

## Maqsad

Tizimning umumiy infratuzilmasini qurish:
- Authentication va authorization
- Multi-tenancy (schema-per-tenant)
- Foydalanuvchilar va rollar (RBAC)
- Bo'limlar
- Bildirishnomalar
- Vazifalar (umumiy modul)
- Sozlamalar
- Billing va tarif

---

## Sahifalar va URL

```
/login                     # Kirish
/register                  # Ro'yxatdan o'tish
/onboarding                # 7 qadamli wizard
/                          # Bosh sahifa (modul tanlash yoki dashboard)
/settings                  # Sozlamalar (10 sub-sahifa)
  /settings/profile        # Shaxsiy profil
  /settings/company        # Kompaniya ma'lumotlari
  /settings/departments    # Bo'limlar
  /settings/users          # Xodimlar va rollar
  /settings/notifications  # Bildirishnomalar
  /settings/integrations   # Integratsiyalar (qisqacha)
  /settings/billing        # Tarif va to'lovlar
  /settings/security       # Xavfsizlik (parol, 2FA, sessiyalar)
  /settings/api-keys       # API kalitlar
  /settings/audit          # Audit log
/tasks                     # Vazifalar (umumiy modul)
/help                      # Yordam markazi
```

---

## 1. Authentication

### Ro'yxatdan o'tish (`/register`)

**Maydonlar:**
- Kompaniya nomi (majburiy, 2-100 belgi)
- Soha (dropdown: Savdo / Restoran / Salon-Klinika / Ta'lim / Xizmat / IT / Boshqa)
- Telefon raqami (+998 maska, majburiy)
- Email (majburiy)
- Parol (8+ belgi, 1 katta harf, 1 raqam)
- ☐ Foydalanuvchi shartnomasi qabul qilaman (majburiy)

**Tugmalar:**
- `[Ro'yxatdan o'tish]` — primary gold CTA
- `[Google orqali]`
- `[Telegram orqali]`
- Link: "Akkauntim bor → Kirish"

**Jarayon:**
1. Forma submit
2. Email/telefon dublikat tekshirish
3. SMS kod (Eskiz) yuboriladi telefon raqamiga
4. Kod tasdiqlanadi (5 daqiqa muddat)
5. Tenant + Owner User yaratiladi (yangi schema)
6. JWT token qaytariladi
7. Onboarding wizard'ga yo'naltiriladi

### Kirish (`/login`)

**Maydonlar:**
- Email yoki telefon
- Parol
- ☐ Eslab qol (30 kun)

**Tugmalar:**
- `[Kirish]`
- `[Google]`, `[Telegram]`
- Link: "Parolni unutdingizmi?"

### API endpoints

```
POST /api/v1/auth/register
  Body: { company_name, industry, phone, email, password }
  Returns: { tenant_id, verification_id }

POST /api/v1/auth/verify-phone
  Body: { verification_id, code }
  Returns: { access_token, refresh_token, user, tenant }

POST /api/v1/auth/login
  Body: { email_or_phone, password, remember_me }
  Returns: { access_token, refresh_token, user, tenant }

POST /api/v1/auth/refresh
  Body: { refresh_token }
  Returns: { access_token }

POST /api/v1/auth/logout
  Headers: Authorization
  Returns: 204

POST /api/v1/auth/forgot-password
  Body: { email_or_phone }
  Returns: 200

POST /api/v1/auth/reset-password
  Body: { reset_token, new_password }
  Returns: 200

GET  /api/v1/auth/oauth/google
GET  /api/v1/auth/oauth/google/callback
GET  /api/v1/auth/oauth/telegram

POST /api/v1/auth/2fa/enable
  Returns: { qr_code, backup_codes }

POST /api/v1/auth/2fa/verify
  Body: { code }

POST /api/v1/auth/2fa/disable
  Body: { password }
```

### JWT struktura

**Access token** (TTL 1 soat):

```json
{
  "sub": "user_id",
  "tenant_id": "akme_salon",
  "tenant_schema": "tenant_akme_salon",
  "role": "owner",
  "exp": 1234567890
}
```

**Refresh token** (TTL 30 kun) — DB'da saqlanadi (revocation uchun).

---

## 2. Multi-tenancy

### Tenant yaratish jarayoni

```python
async def create_tenant(name: str, owner_email: str) -> Tenant:
    # 1. Public schema'da tenant yaratish
    tenant = Tenant(name=name, schema_name=generate_schema_name(name))
    
    # 2. Yangi schema yaratish
    await db.execute(text(f"CREATE SCHEMA {tenant.schema_name}"))
    
    # 3. Migration'larni shu schema'da bajarish
    await run_tenant_migrations(tenant.schema_name)
    
    # 4. Owner user yaratish
    await create_owner_user(tenant, owner_email)
    
    return tenant
```

### Middleware

```python
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    # Public endpoints (auth, health)
    if is_public_endpoint(request.url.path):
        return await call_next(request)
    
    # JWT'dan tenant_schema'ni ekstrakt qilish
    token = extract_token(request)
    payload = decode_jwt(token)
    
    request.state.tenant_id = payload["tenant_id"]
    request.state.tenant_schema = payload["tenant_schema"]
    request.state.user_id = payload["sub"]
    request.state.role = payload["role"]
    
    response = await call_next(request)
    return response
```

### DB session

```python
async def get_tenant_db(request: Request) -> AsyncSession:
    """Yield session with tenant schema set."""
    async with AsyncSessionLocal() as session:
        # Schema almashtirish
        await session.execute(
            text(f"SET search_path TO {request.state.tenant_schema}, public")
        )
        yield session
```

**Eslatma:** `search_path` tenant schema BIRINCHI, `public` IKKINCHI. Bu —
agar tenant schema'da jadval bo'lmasa, public'dan qidiradi (shared resurslar uchun).

---

## 3. Onboarding wizard (7 qadam)

### Qadam 1: Xush kelibsiz

```
┌─────────────────────────────────────┐
│   💎  NEXUS AI'ga xush kelibsiz!   │
│                                     │
│  [30 sek video]                     │
│                                     │
│  Sizni 7 ta oddiy qadamga olib      │
│  boramiz. ~3 daqiqa.                │
│                                     │
│         [Boshlash →]                │
└─────────────────────────────────────┘
```

### Qadam 2: Kompaniya ma'lumotlari

- Logo (drag & drop, max 2MB)
- INN/STIR (ixtiyoriy, validatsiya bilan)
- Manzil (Viloyat → Tuman → Ko'cha)
- Sayt URL (ixtiyoriy)
- Faoliyat tavsifi (textarea, 2-3 jumla — AI uchun muhim)

### Qadam 3: Bo'limlar

```
Standart shablon yoki o'z:

☑ Marketing
☑ Sotuv
☑ Qo'llab-quvvatlash
☐ Boshqaruv

[+ Yangi bo'lim]   [O'tkazib yuborish]
```

### Qadam 4: Xodimlar

```
Xodimlarni email yoki Telegram orqali taklif qiling:

[email/telegram]  [Rol ▾]  [Bo'lim ▾]  [+]

Taklif qilingan: 0

[O'tkazib yuborish]   [Keyingi →]
```

### Qadam 5: Modullar tanlash

6 ta modul kartochkasi (rasm + tavsif + narx). Foydalanuvchi tanlaydi:

```
☑ 👥 CRM        290k so'm/oy
☐ ✍️ SMM        390k so'm/oy
☑ 💬 Inbox      390k so'm/oy
...

Yoki paket:
○ Marketing Pack (-15%)
○ Sales Pack (-15%)
● Full Ecosystem (-25%)
```

### Qadam 6: Tarif

```
Tanlangan: Full Ecosystem

Start         690k so'm/oy
Pro          1.5M so'm/oy   ← Tavsiya
Business     3.0M so'm/oy

[7 kunlik bepul sinov]  [Karta talab qilinmaydi]
```

### Qadam 7: Tayyor!

```
🎉 Tabriklaymiz!

Akkauntingiz tayyor. Endi nimadan boshlasak?

[+ Birinchi mijoz qo'shish]
[+ Birinchi post yaratish]
[🔗 Akkauntlarni ulash]

[Keyinroq, bosh sahifaga →]
```

---

## 4. Asosiy interfeys layout

### Sidebar (chap menyu)

`/components/shared/sidebar.tsx`:

- Logo + kompaniya nomi (yuqorida)
- Modul ro'yxati (faqat ulanganlar — boshqalari kulrang)
- Pastida: AI Yordamchi (gold accent), Yordam
- Yig'ish tugmasi `[<<]` (faqat ikonlar holati)
- Active state: `bg-cream-100 + border-l-4 border-gold`

### Header

`/components/shared/header.tsx`:

Chapdan o'ngga:
- Brend tanlash dropdown (multi-brand bo'lsa)
- Global qidiruv (Cmd/Ctrl+K) — mijoz/post/xabar/hisobot global qidiradi
- Theme tugma (☀️/🌙)
- Bildirishnomalar (🔔 + qizil dot)
- Profil dropdown (avatar + ism + dropdown)

### Asosiy ish maydoni

```html
<main class="ml-64 min-h-screen bg-cream">
  <Header />
  <div class="p-8 max-w-7xl mx-auto">
    {/* Breadcrumb */}
    <nav>...</nav>
    
    {/* Page header */}
    <div class="flex justify-between mb-8">
      <h1>Sahifa nomi</h1>
      <Button variant="primary">Asosiy CTA</Button>
    </div>
    
    {/* Content */}
    {children}
  </div>
</main>
```

---

## 5. Rollar va imtiyozlar (RBAC)

### Standart 5 rol

| Rol | CRM | SMM | Reklama | Inbox | Vazifa | Hisobot | Integr. | Xodim | Billing |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Owner | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ |
| Admin | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | ✓✏ | 👁 |
| Manager | ✓✏* | ✓✏* | 👁 | ✓✏* | ✓✏* | 👁 | ✗ | 👁 | ✗ |
| Operator | ✓✏** | 👁 | ✗ | ✓✏** | ✓✏** | ✗ | ✗ | ✗ | ✗ |
| Viewer | 👁 | 👁 | 👁 | ✗ | 👁 | 👁 | ✗ | ✗ | ✗ |

`*` faqat o'z bo'limi · `**` faqat o'ziga biriktirilgan · `✓✏` tahrir · `👁` ko'rish · `✗` yo'q

### Custom rol yaratish

`Sozlamalar > Xodimlar va rollar > [+ Yangi rol]`:

Imtiyozlar matritsasi: har modul uchun 4 daraja
- Yo'q
- Ko'rish
- Tahrirlash
- To'liq

Qo'shimcha imtiyozlar:
- Sohasi: Hammasi / O'z bo'limi / O'zi yaratganlari
- Eksport: ✓/✗
- O'chirish: ✓/✗
- AI ishlatish: ✓/✗

### Texnik amalga oshirish

```python
# Permission decorator
@require_permission("contacts.create")
async def create_contact(request: Request, ...):
    ...

# Programmatic check
if not has_permission(user, "contacts.delete"):
    raise PermissionDenied()
```

```typescript
// Frontend
{can('contacts.create') && (
  <Button>Yangi mijoz</Button>
)}
```

---

## 6. Bo'limlar (Departments)

`Sozlamalar > Bo'limlar`:

- **Tree view** (drag & drop). Daraja chegarasi yo'q.
- Har bo'limda: nomi, boshliq (User), o'rinbosar(lar), xodimlar.
- Bir xodim bir nechta bo'limga (multi-membership).
- Bo'limlararo ko'rinish: default ON, OFF qilish mumkin.

```
🏢 NEXUS AI MChJ
├── 💼 Boshqaruv
│   ├── Direktor (Akmal Karimov)
│   └── Boshqaruv kotibi
├── 💰 Sotuv
│   ├── 👤 Boshliq: Sardor M.
│   ├── O'rinbosar: Dilfuza A.
│   └── 5 xodim
├── 📢 Marketing
└── 🛠 Qo'llab-quvvatlash
```

---

## 7. Vazifalar (Tasks) — umumiy modul

### Vazifa tarkibi

- Sarlavha (majburiy)
- Tavsif (rich text)
- Mas'ul(lar) — bir nechta
- Bog'liqlik (polymorphic) — Mijoz / Bitim / Post / Reklama / Xabar
- Muhimlik: Past / O'rta / Yuqori / Kritik
- Status: Yangi / Jarayonda / Tekshirishda / Bajarildi / Bekor
- Boshlanish va tugash sanasi
- Vaqt taxmini (soat)
- Ilovalar (fayl)
- Izohlar (thread)
- Subtask'lar (checklist)

### Sahifa `/tasks`

Uchta ko'rinish:
1. **Kanban** — status bo'yicha ustunlar (drag & drop)
2. **Ro'yxat** — jadval (filter, sort, eksport)
3. **Kalendar** — sana bo'yicha (oylik/haftalik view)

Filterlar: mas'ul, bo'lim, status, muhimlik, sana, bog'liqlik (modul).

Eslatuvchi (sozlanadi):
- 1 soat oldin
- 1 kun oldin
- 3 kun oldin

Bildirishnoma: tizim + Telegram.

---

## 8. Bildirishnomalar tizimi

### Asosiy hodisalar

| Hodisa | Tizim | Telegram |
|---|:---:|:---:|
| Yangi mijoz | ✓ | sozlanadi |
| Yangi xabar (Inbox) | ✓ | ✓ |
| Vazifa biriktirildi | ✓ | ✓ |
| Vazifa muddati yaqin | ✓ | ✓ |
| AI tasdiq kutmoqda | ✓ | ✓ |
| Anomaliya | ✓ | ✓ |
| To'lov muddati | ✓ | ✓ |
| Yangi xodim | ✓ | sozlanadi |

### Indamas vaqt (Do not disturb)

`Sozlamalar > Bildirishnomalar`:
- Vaqt oralig'i (masalan, 22:00 – 08:00)
- Dam olish kunlari
- Bayramlar

### Real-time

WebSocket orqali frontend'ga push:

```
Backend event → Redis pub/sub → WebSocket → Frontend (toast notification)
```

---

## 9. Sozlamalar (Settings) — to'liq

### Profil (Men)

- Avatar
- F.I.O.
- Lavozim
- Telefon, Email
- Til (uz lotin / uz kirill / ru)
- Tema (light / dark / auto)
- Telegram bog'lash
- [Akkauntni o'chirish]

### Kompaniya ma'lumotlari

- Logo
- Nomi
- INN/STIR
- Manzil
- Sayt URL
- Faoliyat tavsifi (AI uchun)
- Vaqt mintaqasi (default: Asia/Tashkent)
- Valyuta (default: UZS)
- Ish vaqti (kun va soat oralig'i)

### Xavfsizlik

- Parolni o'zgartirish (joriy parol talab qilinadi)
- 2FA yoqish/o'chirish (TOTP yoki SMS)
- Faol sessiyalar (qurilma, IP, joylashuv) — uzoqdan logout
- Audit log preview (oxirgi 30 kun)

### API kalitlar

- Token yaratish (nom, imtiyozlar, rate limit, IP whitelist, expires)
- Token bir martalik ko'rsatiladi yaratilganda
- Bekor qilish (revoke)

---

## 10. Tarif va Billing

### Tariflar va modullar

```
Per-modul narxlar:
👥 CRM           Start: 290k   Pro: 690k   Business: 1.4M
✍️ SMM           Start: 390k   Pro: 890k   Business: 1.8M
📈 Reklama       Start: 290k   Pro: 690k   Business: 1.4M
💬 Inbox         Start: 390k   Pro: 890k   Business: 1.8M
📊 Hisobotlar    Start: 190k   Pro: 490k   Business: 990k
🔗 Integratsiya  Start: 190k   Pro: 490k   Business: 990k
```

Paketlar:
- Marketing Pack (SMM + Reklama + Inbox) — 15% chegirma
- Sales Pack (CRM + Inbox + Hisobotlar) — 15% chegirma
- Full Ecosystem (hammasi) — 25% chegirma
- Enterprise — individual

Yillik chegirma: 6 oy −10%, 12 oy −20%.

### AI tokenlar

| Tarif | Oylik AI kreditlar |
|---|---|
| Start | 50,000 |
| Pro | 200,000 |
| Business | 1,000,000 |

Tugagandan keyin: 100k token = 99k so'm qo'shimcha.

### To'lov turlari

- Bank o'tkazmasi (yuridik shaxs uchun, Invoice generatsiya)
- Naqd (admin tomonidan tasdiqlanadi)
- Click / Payme / Uzum — Bosqich 4 da

### Grace period

- Muddat o'tdi → 7 kun banner ogohlantirish
- 7 kun + → faqat o'qish rejimi
- 30 kun + → akkaunt qulflanadi (data 90 kun saqlanadi)
- 90 kun + → arxivga, keyin o'chiriladi

---

## 11. Yordam markazi (`/help`)

- Qidiruv (FAQ + qo'llanmalar)
- Kategoriyalar: Boshlash, har modul, Billing
- Video qo'llanmalar (YouTube embed)
- PDF qo'llanmalar (yuklab olish)
- Live chat (pastki o'ng 💬)
- AI Yordamchi (kontekstga moslashgan, har sahifada)

---

## DB jadvallar

To'liq schema: [../04-database-schema.md](../04-database-schema.md#tenant-schema)

Ushbu modul jadvallari:
- `users` (public schema)
- `tenants` (public schema)
- `plans` (public schema)
- `invoices` (public schema)
- `departments` (tenant schema)
- `roles` (tenant schema)
- `user_roles` (tenant schema)
- `notifications` (tenant schema)
- `tasks` (tenant schema)
- `audit_log` (tenant schema)
- `verification_codes` (tenant schema)
- `api_keys` (tenant schema)

---

## API endpoints

To'liq: [../05-api-contracts.md](../05-api-contracts.md)

Asosiy:
- `/api/v1/auth/*` — autentifikatsiya
- `/api/v1/tenant` — kompaniya ma'lumotlari
- `/api/v1/users` — xodimlar
- `/api/v1/roles` — rollar
- `/api/v1/departments` — bo'limlar
- `/api/v1/tasks` — vazifalar
- `/api/v1/notifications` — bildirishnomalar
- `/api/v1/billing/*` — to'lov
- `/api/v1/audit` — audit log
- `/api/v1/api-keys` — API kalitlar

---

## Acceptance kriteriylari (Sprint 1-3)

Foundation tugagani uchun quyidagilar ishlashi kerak:

1. ✅ Yangi kompaniya ro'yxatdan o'tib, JWT token oladi
2. ✅ Kirish va chiqish ishlaydi
3. ✅ Onboarding wizard 7 qadam to'liq
4. ✅ Tenant schema avtomatik yaratiladi va izolyatsiyalanadi
5. ✅ Asosiy layout (sidebar + header) ishlaydi
6. ✅ 5 standart rol va imtiyozlar tekshiruvi
7. ✅ Bo'limlar yaratish, tahrirlash
8. ✅ Vazifalar moduli (Kanban + Ro'yxat + Kalendar)
9. ✅ Bildirishnomalar (real-time)
10. ✅ Sozlamalar 10 ta sub-sahifa
11. ✅ Bank o'tkazma orqali tarif faollashtirish
12. ✅ Audit log har muhim harakatni qayd qiladi
13. ✅ 2FA ishlaydi
14. ✅ API kalit yaratish va ishlatish
15. ✅ Test coverage ≥ 80%

---

## Tegishli fayllar

- [../00-overview.md](../00-overview.md)
- [../01-architecture.md](../01-architecture.md)
- [../02-conventions.md](../02-conventions.md)
- [../07-security.md](../07-security.md)
- [../adrs/0002-multi-tenancy-strategy.md](../adrs/0002-multi-tenancy-strategy.md)
