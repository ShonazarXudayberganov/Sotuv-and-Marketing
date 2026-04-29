# 02 — Kod konvensiyalari

> Komanda bo'lib ishlash uchun bir xil tartib. Claude Code ham shu qoidalarga
> rioya qiladi. Yangi qoida kerak bo'lsa — PR oching va komanda muhokamasi.

---

## Til siyosati

| Joy | Til | Misol |
|---|---|---|
| UI matn (foydalanuvchi ko'radigan) | O'zbek lotin | "Yangi mijoz qo'shish" |
| Kod identifierlar | English | `createContact()`, `contact_id` |
| Kod commentlar | English | `# Calculate AI score based on activity` |
| Hujjatlar (docs/) | O'zbek | Bu fayl |
| Commit messages | English (Conventional) | `feat(crm): add contact scoring` |
| DB jadval va maydonlar | English snake_case | `contacts.ai_score` |
| API endpoints | English kebab-case | `/api/v1/contact-segments` |
| Environment variables | UPPER_SNAKE_CASE | `DATABASE_URL` |

**Sabab:** Kod bo'lim — texnik birgalikda ishlash uchun (xalqaro standart).
UI bo'lim — foydalanuvchi uchun (mahalliy til).

---

## Python konvensiyalari (Backend)

### Linting

- **ruff** — formatter va linter
- **mypy** — type checking
- Pre-commit hook majburiy

`pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "B", "N", "UP", "ANN", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### Type hints

**Majburiy** har funksiyada va metodda:

```python
# ❌ Yomon
def get_contact(id):
    return db.query(Contact).get(id)

# ✅ Yaxshi
async def get_contact(id: int, db: AsyncSession) -> Contact | None:
    result = await db.execute(select(Contact).where(Contact.id == id))
    return result.scalar_one_or_none()
```

### Pydantic

Schema'lar har doim `app/<module>/schemas/`'da:

```python
# app/modules/crm/schemas/contact.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., pattern=r"^\+998\d{9}$")
    email: EmailStr | None = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    # Faqat o'zgartirish mumkin bo'lgan maydonlar

class ContactRead(ContactBase):
    id: int
    ai_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy ORM uchun
```

### Naming

| Element | Konvensiya | Misol |
|---|---|---|
| Module/file | snake_case | `contact_service.py` |
| Class | PascalCase | `ContactService` |
| Function/method | snake_case | `get_contact_by_id` |
| Variable | snake_case | `current_user` |
| Constant | UPPER_SNAKE | `MAX_TOKENS_PER_REQUEST` |
| Private | _prefix | `_internal_helper` |

### Docstrings

Public API uchun majburiy:

```python
async def calculate_ai_score(contact_id: int, db: AsyncSession) -> int:
    """
    Calculate AI score (0-100) for a contact.
    
    Score is based on: activity recency, message frequency,
    deal history, and source quality.
    
    Args:
        contact_id: ID of the contact in current tenant.
        db: Active async database session.
    
    Returns:
        Score from 0 (cold) to 100 (hot).
    
    Raises:
        ContactNotFoundError: If contact doesn't exist.
        AIServiceError: If AI provider unavailable.
    """
    ...
```

### Error handling

Custom exception'lar `app/core/exceptions.py`'da:

```python
class NexusAIError(Exception):
    """Base exception."""
    
class ContactNotFoundError(NexusAIError):
    """Contact not found."""
    
class TenantContextMissingError(NexusAIError):
    """Tenant context not set in request."""
```

API'da global exception handler:

```python
@app.exception_handler(ContactNotFoundError)
async def handle_contact_not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Mijoz topilmadi", "code": "CONTACT_NOT_FOUND"}
    )
```

### Tenant context

**HAR FUNCTION'da tekshiriladi:**

```python
async def get_contacts(
    request: Request,  # Tenant context middleware orqali
    db: AsyncSession = Depends(get_tenant_db)
) -> list[ContactRead]:
    # get_tenant_db dependency tenant schema'sini tanlaydi
    result = await db.execute(select(Contact))
    return result.scalars().all()
```

Hech qachon `tenant_id` filterini qo'lda yozma — middleware buni qiladi.

---

## TypeScript konvensiyalari (Frontend)

### Linting

- **ESLint** + Next.js config
- **Prettier** — format
- **TypeScript strict mode**

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### Type'lar

**Hech qachon `any`.** Agar tip noma'lum bo'lsa — `unknown` va keyin narrow.

```typescript
// ❌ Yomon
function process(data: any) {
  return data.name;
}

// ✅ Yaxshi
function process(data: Contact) {
  return data.name;
}

// ✅ Tip noma'lum bo'lsa
function process(data: unknown) {
  if (typeof data === 'object' && data !== null && 'name' in data) {
    return (data as { name: string }).name;
  }
  throw new Error('Invalid data');
}
```

### Naming

| Element | Konvensiya | Misol |
|---|---|---|
| File | kebab-case | `contact-card.tsx` |
| Component | PascalCase | `ContactCard` |
| Function | camelCase | `formatPhoneNumber` |
| Variable | camelCase | `currentUser` |
| Constant | UPPER_SNAKE | `MAX_FILE_SIZE` |
| Type/Interface | PascalCase | `Contact`, `ContactProps` |
| Hook | use prefix | `useContact` |

### Komponent shabloni

```typescript
// src/components/crm/contact-card.tsx
'use client';

import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Contact } from '@/lib/types';

interface ContactCardProps {
  contact: Contact;
  onEdit?: (contact: Contact) => void;
  className?: string;
}

export function ContactCard({ contact, onEdit, className }: ContactCardProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <h3 className="font-serif text-lg">{contact.name}</h3>
        <Badge variant={contact.aiScore > 80 ? 'gold' : 'secondary'}>
          AI Score: {contact.aiScore}
        </Badge>
      </CardHeader>
      <CardContent>
        {/* ... */}
      </CardContent>
    </Card>
  );
}
```

### Server Components vs Client Components

- **Server Components** — default. SEO, performance.
- **Client Components** — `'use client'` direktivasi. Interaktivlik kerak bo'lsa.

```typescript
// Server Component (default)
// src/app/crm/contacts/page.tsx
import { getContacts } from '@/lib/api/contacts';

export default async function ContactsPage() {
  const contacts = await getContacts();  // Server-side
  return <ContactList contacts={contacts} />;
}

// Client Component
// src/components/crm/contact-list.tsx
'use client';

import { useState } from 'react';

export function ContactList({ contacts }: Props) {
  const [filter, setFilter] = useState('');
  // ... interaktivlik
}
```

### State management

```typescript
// Server state — React Query
import { useQuery } from '@tanstack/react-query';

function useContacts() {
  return useQuery({
    queryKey: ['contacts'],
    queryFn: () => fetch('/api/v1/contacts').then(r => r.json()),
  });
}

// Client state (global) — Zustand
import { create } from 'zustand';

interface BrandStore {
  currentBrandId: number | null;
  setCurrentBrand: (id: number) => void;
}

export const useBrandStore = create<BrandStore>((set) => ({
  currentBrandId: null,
  setCurrentBrand: (id) => set({ currentBrandId: id }),
}));

// Form state — react-hook-form + Zod
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  phone: z.string().regex(/^\+998\d{9}$/),
});

function ContactForm() {
  const form = useForm({ resolver: zodResolver(schema) });
  // ...
}
```

---

## Git konvensiyalari

### Branch naming

```
main                            # Production-ready
develop                         # Joriy ishlanma
feature/<scope>-<short-desc>    # Yangi xususiyat
fix/<scope>-<short-desc>        # Bug fix
refactor/<scope>-<short-desc>   # Refaktoring
docs/<scope>                    # Hujjat o'zgarishi
chore/<short-desc>              # Routine ishlar
```

Misollar:
- `feature/crm-ai-scoring`
- `fix/inbox-message-duplicate`
- `refactor/auth-jwt-refresh`
- `docs/api-contracts`

### Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type:**
- `feat` — yangi xususiyat
- `fix` — bug fix
- `docs` — hujjat
- `style` — format (kod logikasi o'zgarmagan)
- `refactor` — refaktoring (xususiyat o'zgarmagan)
- `perf` — performance
- `test` — test qo'shish
- `chore` — routine (deps update, ...)

**Misollar:**

```
feat(crm): add AI scoring to contact card

- Calculate score on contact creation
- Update score hourly via Celery beat
- Display rangli badge based on score range

Closes #42

---

fix(inbox): prevent duplicate message on retry

When network error occurred, retry sometimes
created duplicate. Now uses idempotency key.

Fixes #67

---

docs(architecture): clarify multi-tenancy strategy

---

refactor(auth): extract JWT logic to separate module
```

### Pull Request

**Title:** Conventional commit'ga o'xshash.

**Description shabloni:**

```markdown
## Nima qilindi?

- [ ] Funksiya 1
- [ ] Funksiya 2

## Nima uchun?

[Mavzu konteksti, yechim sababi]

## Qanday tekshirildi?

- [ ] Unit test qo'shildi
- [ ] Integration test qo'shildi
- [ ] Manual testing: [tasvir]

## Screenshots (UI bo'lsa)

[Rasmlar]

## Tegishli issue/PR

Closes #42
Bog'liq: #45
```

---

## Test konvensiyalari

### Backend (pytest)

```
tests/
├── unit/                    # Pure logic, no DB
│   ├── services/
│   └── utils/
├── integration/             # DB + dependencies
│   ├── api/
│   └── services/
├── e2e/                     # Full workflow
└── conftest.py              # Fixtures
```

**Test naming:**

```python
# test_contact_service.py

async def test_create_contact_with_valid_data():
    """Contact yaratish to'g'ri ma'lumot bilan ishlaydi."""
    ...

async def test_create_contact_fails_when_phone_duplicated():
    """Telefon raqami dublikat bo'lganda xato qaytarilsin."""
    ...

async def test_ai_score_calculated_after_contact_create():
    """Contact yaratilgandan keyin AI score hisoblanadi."""
    ...
```

**Fixtures (conftest.py):**

```python
@pytest.fixture
async def test_db():
    """Har test uchun toza DB."""
    ...

@pytest.fixture
async def test_tenant(test_db):
    """Test tenant + schema yaratiladi."""
    ...

@pytest.fixture
async def authenticated_client(test_tenant):
    """Login qilingan API client."""
    ...
```

### Frontend (Vitest + React Testing Library)

```typescript
// contact-card.test.tsx
import { render, screen } from '@testing-library/react';
import { ContactCard } from './contact-card';

describe('ContactCard', () => {
  it('displays contact name', () => {
    render(<ContactCard contact={{ name: 'Akmal', ... }} />);
    expect(screen.getByText('Akmal')).toBeInTheDocument();
  });
  
  it('shows gold badge when AI score > 80', () => {
    render(<ContactCard contact={{ aiScore: 85, ... }} />);
    expect(screen.getByTestId('ai-badge')).toHaveClass('badge-gold');
  });
});
```

### E2E (Playwright)

Playwright — kritik foydalanuvchi yo'llari uchun (login, mijoz qo'shish, post yaratish).

---

## API endpoint qoidalari

### URL pattern

```
/api/v1/<resource>                 # List + create
/api/v1/<resource>/:id             # Read + update + delete
/api/v1/<resource>/:id/<action>    # Custom action
/api/v1/<resource>/:id/<sub-resource>  # Nested
```

**Misollar:**

```
GET    /api/v1/contacts              # List
POST   /api/v1/contacts              # Create
GET    /api/v1/contacts/42           # Read
PATCH  /api/v1/contacts/42           # Update
DELETE /api/v1/contacts/42           # Delete
POST   /api/v1/contacts/42/score     # Recalculate score
GET    /api/v1/contacts/42/timeline  # Sub-resource
```

### Response format

**Success:**

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 234
  }
}
```

**Error:**

```json
{
  "detail": "Mijoz topilmadi",
  "code": "CONTACT_NOT_FOUND",
  "field": "id"
}
```

### Status code'lar

| Code | Qachon |
|---|---|
| 200 | Muvaffaqiyatli read/update |
| 201 | Yangi resurs yaratildi |
| 204 | Muvaffaqiyatli, javob bo'sh (DELETE) |
| 400 | Validatsiya xatosi |
| 401 | Auth yo'q |
| 403 | Auth bor, lekin imtiyoz yo'q |
| 404 | Topilmadi |
| 409 | Konflikt (dublikat, ...) |
| 422 | Pydantic validation |
| 429 | Rate limit |
| 500 | Server xato |

---

## Performance qoidalari

1. **N+1 query'dan saqlaning** — `selectinload` yoki `joinedload`
2. **Index har FK va tez-tez filtrlanadigan ustunda**
3. **Pagination majburiy** — list endpointlarida default `limit=50`
4. **Cache aniq belgilangan TTL bilan**
5. **AI chaqiruv background'da** (Celery), agar > 5 sek bo'lsa
6. **Frontend image — Next.js Image component**, lazy load
7. **Bundle size monitor** — har sprint Lighthouse audit

---

## Tegishli fayllar

- [01-architecture.md](01-architecture.md) — Tizim arxitekturasi
- [03-design-system.md](03-design-system.md) — UI dizayn
- [05-api-contracts.md](05-api-contracts.md) — API tafsilotlari
- [adrs/](adrs/) — Yangi qoida uchun ADR yozing
