# ADR-0002: Multi-tenancy strategiyasi

**Holat:** Qabul qilingan
**Sana:** 2026-04-29

## Kontekst

NEXUS AI multi-tenant SaaS. Mijozlar (kompaniyalar) ma'lumotlari izolyatsiya
bo'lishi shart.

## Variantlar

### A. Shared schema, tenant_id ustun
Hamma jadval'da `tenant_id` ustun. Har query'da `WHERE tenant_id = ?`.
- ✅ Sodda
- ❌ Xavfli — agar dasturchi WHERE'ni unutsa, leak
- ❌ Backup/restore murakkab (per-tenant)

### B. Schema-per-tenant
Har tenant — alohida PostgreSQL schema (`tenant_<name>`).
- ✅ Ma'lumot izolyatsiya — fizik
- ✅ Per-tenant backup
- ✅ Migration per-tenant
- ❌ Schema o'zgarishi har tenantda yangilanishi kerak

### C. Database-per-tenant
Har tenant — alohida database.
- ✅ Maximum izolyatsiya
- ❌ DB connection pool murakkab
- ❌ Cross-tenant analytics imkonsiz
- ❌ Resource consumption yuqori

## Qaror

**Variant B — Schema-per-tenant.**

PostgreSQL'da `CREATE SCHEMA` har yangi tenant uchun. Application
middleware'da `SET search_path` har request'da.

## Implementatsiya

```python
# Tenant yaratish
async def create_tenant(name):
    schema_name = generate_schema_name(name)
    await db.execute(f"CREATE SCHEMA {schema_name}")
    await run_migrations(schema_name)
    return Tenant(schema_name=schema_name)

# Middleware
async def tenant_middleware(request, call_next):
    schema = extract_from_jwt(request)
    request.state.tenant_schema = schema
    return await call_next(request)

# DB session
async def get_db(request):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(f"SET search_path TO {request.state.tenant_schema}, public")
        )
        yield session
```

## Oqibatlar

**Ijobiy:**
- Forgot tenant_id WHERE? — impossible (schema scoped)
- Per-tenant backup oddiy
- Per-tenant migration

**Salbiy:**
- Migration har tenant'da bajariladi (slow with 1000+ tenants)
- Cross-tenant report — `public` schema'dan via `tenants` jadvalini ishlatamiz

**Keyin (5000+ tenant):**
- Sharding (multiple PG instances by tenant_id hash)
