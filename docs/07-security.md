# 07 — Xavfsizlik

> Network'dan ma'lumot encryption'gacha — har qatlam.
> O'zbekiston PD qonuniga moslashtirilgan.

---

## Xavfsizlik qatlamlari

### 1. Network

- **TLS 1.3** majburiy (HTTP yo'q)
- **Cloudflare** — DDoS, WAF, bot protection
- **Rate limiting** (Nginx + application layer)
- **IP whitelist** (Enterprise tier uchun ixtiyoriy)
- **CORS** strict (faqat ruxsat etilgan domenlar)

### 2. Authentication

- **JWT** (access + refresh)
- Access token TTL: **1 soat**
- Refresh token TTL: **30 kun** (revocable)
- **bcrypt** parollar (cost factor 12)
- **2FA** (TOTP - Google Authenticator yoki SMS)
- **OAuth 2.0** (Google, Telegram)
- **MyID** (Bosqich 3) — O'zbekiston ID system
- **SSO** (Enterprise) — SAML, OIDC

### 3. Authorization

- **RBAC** (Role-Based Access Control)
- 5 ta standart rol + custom rollar
- **Scope-based** (all / department / own)
- **Resource-level** permissions (har endpoint'da check)
- **Audit log** har authorization qaroriga

### 4. Data — Encryption at rest

- **AES-256-GCM** sensitive ustunlar uchun:
  - Social media tokenlar (`social_accounts.access_token_encrypted`)
  - Integration credentials
  - API key hashlari (SHA-256)
  - Backuplar (foydalanuvchi kaliti bilan, zero-knowledge)
- **PostgreSQL TDE** (transparent disk encryption) — UzCloud level
- **Backup encryption** — kalit foydalanuvchida

### 5. Data — Encryption in transit

- TLS 1.3 har joyda
- WebSocket — WSS
- Internal services — mTLS (Bosqich 4)

### 6. Audit

Har muhim harakat log:
- Login / logout / failed attempt
- User CRUD
- Role o'zgartirish
- Data eksport
- Tarif o'zgarishi
- Mijoz ma'lumotlari o'chirish
- AI prompt o'zgarishi

Saqlanadi: **90 kun** (Standard tier), **1 yil** (Business+).

### 7. Secrets management

- `.env` faylda **hech qachon production secret yo'q**
- Production: HashiCorp Vault yoki UzCloud Key Management
- Rotation: har 90 kun
- Pre-commit hook: secret detection (`git-secrets`)

---

## Multi-tenancy xavfsizligi

### Schema isolation

```python
# Middleware har request'da
async def tenant_middleware(request, call_next):
    tenant_schema = extract_from_jwt(request)
    
    # Critical: schema name validatsiya
    if not is_valid_schema_name(tenant_schema):
        raise HTTPException(403, "Invalid tenant")
    
    # Set per-connection
    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {tenant_schema}"))
    
    return await call_next(request)
```

### Test xavfsizligi

```python
# tests/security/test_tenant_isolation.py
async def test_user_cannot_access_other_tenant():
    """Bitta tenantning user'i boshqa tenantning datasini ko'ra olmaydi."""
    user_a = await create_test_user_in_tenant("tenant_a")
    contact_b = await create_test_contact_in_tenant("tenant_b")
    
    response = await client_for_user(user_a).get(f"/contacts/{contact_b.id}")
    assert response.status_code == 404  # ko'rmasligi kerak
```

---

## OWASP Top 10 himoyasi

| Risk | Himoya |
|---|---|
| 1. Broken access control | RBAC + tenant middleware + tests |
| 2. Cryptographic failures | TLS 1.3, AES-256, bcrypt 12, no MD5/SHA1 |
| 3. Injection (SQL) | SQLAlchemy parametrized, no raw SQL with user input |
| 4. Insecure design | Threat modeling per modul, security review |
| 5. Security misconfiguration | Strict CSP, secure headers, no debug in prod |
| 6. Vulnerable components | Dependabot, regular updates, SCA |
| 7. Auth failures | Rate limit login, lockout, 2FA |
| 8. Data integrity | Signed tokens, HMAC webhooks, code review |
| 9. Logging failures | Structured logs, audit log, Sentry |
| 10. SSRF | URL validation, allowlist, no external fetch from user input |

---

## O'zbekiston qonun talablari

### Personal data (PD) qonuni

1. **Mahalliy saqlash:** mijoz ma'lumotlari O'zbekiston serverlarida (UzCloud)
2. **Rozilik:** har foydalanuvchi privacy policy + ToS qabul qiladi
3. **Huquqlar:**
   - Ma'lumotni ko'rish (data export)
   - Ma'lumotni o'chirish (right to be forgotten)
   - Ma'lumot to'g'rilash (edit)
4. **Yo'naltirish:** AI uchun anonimlashtirilgan ma'lumot tashqi servislarga
5. **Buzilish bildirishi:** 24 soat ichida regulyatorga

### Implementation

```python
# Foydalanuvchi o'z ma'lumotlarini ko'chirib olishi
@router.get("/me/data-export")
async def export_my_data(user: User):
    """GDPR + O'zbekiston PD qonuni uchun."""
    data = await collect_all_user_data(user)
    return create_zip_archive(data)

# Akkauntni o'chirish (right to be forgotten)
@router.delete("/me/account")
async def delete_my_account(user: User, reason: str):
    """30 kun grace period, keyin to'liq o'chirish."""
    await mark_for_deletion(user, deletion_date=now + timedelta(days=30))
    await send_deletion_notification(user)
```

---

## Incident response

### Severity levels

- **P0 (Critical):** ma'lumot leak, downtime, security breach — 15 daqiqada javob
- **P1 (High):** modul ishlamayapti — 1 soat
- **P2 (Medium):** xususiyat qisqarishi — 4 soat
- **P3 (Low):** kichik bug — keyingi sprint

### Playbook

1. **Aniqlash** — monitoring + alert
2. **Izolyatsiya** — affected tenantlarni alohida
3. **Bartaraf etish** — root cause va patch
4. **Tiklash** — service restore
5. **Postmortem** — Confluence'da, 5 ish kuni ichida

---

## Penetration testing

- Yiliga 1 marta — uchinchi tomon firma
- Quarterly — internal security review
- Continuous — automated security scanning (Dependabot, Snyk)

---

## Compliance roadmap

- [x] **O'zbekiston PD qonuni** — Bosqich 0
- [ ] **GDPR-ready** — Bosqich 2 (xalqaro mijozlar uchun)
- [ ] **ISO 27001** — Bosqich 3 (Enterprise sotuvi uchun)
- [ ] **SOC 2 Type II** — Bosqich 4 (xalqaro Enterprise)

---

## Tegishli fayllar

- [02-conventions.md](02-conventions.md) — Auth code qoidalari
- [04-database-schema.md](04-database-schema.md) — Encryption ustunlari
- [adrs/0002-multi-tenancy-strategy.md](adrs/0002-multi-tenancy-strategy.md)
