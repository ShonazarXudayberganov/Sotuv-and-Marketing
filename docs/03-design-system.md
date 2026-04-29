# 03 — Dizayn tizimi (Luxury Theme)

> NEXUS AI dizayn tili: ranglar, tipografiya, komponentlar, interaktivlik.
> Frontend dasturchi va dizayner uchun majburiy o'qish.

---

## Falsafa

NEXUS AI **luxury** estetikasiga ega. Bu — premium SaaS, yuqori sifat hissi.

**Asoslar:**
- Kam — ko'p (less is more)
- Whitespace — element
- Tipografiya — birinchi
- Rang — diqqatli (kam aksent)
- Animatsiya — yumshoq
- Interaktivlik — silliq

**Inspiratsiya:** Linear.app, Notion, Apple, Stripe + traditional luxury (Cartier,
Louis Vuitton — oltin va ko'mir aksentlar).

---

## Rang palitrasi

### Kunduzgi (Light Luxury) — DEFAULT

| Rol | Hex | Tailwind | Foydalanish |
|---|---|---|---|
| **Asosiy fon** | `#FAF7F2` | `bg-cream` | Sahifa fon |
| **Kartochka fon** | `#FFFFFF` | `bg-white` | Card, modal |
| **Ikkilamchi fon** | `#F4F2EE` | `bg-cream-100` | Hover, alternating row |
| **Asosiy matn** | `#1A1A1A` | `text-charcoal` | Sarlavha, body |
| **Yordamchi matn** | `#6B6B6B` | `text-soft-gray` | Caption, label |
| **Aksent (oltin)** | `#C9A961` | `bg-gold` `text-gold` | CTA, highlight |
| **Aksent quyuq** | `#9C7E3D` | `bg-gold-dark` | Hover gold |
| **Aksent ochiq** | `#E8D5A4` | `bg-gold-light` | Subtle highlight |
| **Border** | `#E5E5E5` | `border-light-gray` | Card border |
| **Border gold** | `#E8D5A4` | `border-gold-light` | Premium card |
| **Muvaffaqiyat** | `#3D8B5A` | `text-success` | Success, positive |
| **Ogohlantirish** | `#D68C3C` | `text-warning` | Warning, pending |
| **Xato** | `#B5453C` | `text-danger` | Error, negative |
| **Ma'lumot** | `#1E3A5F` | `text-info` | Info banner |

### Tungi (Dark Luxury)

| Rol | Hex | Tailwind |
|---|---|---|
| Asosiy fon | `#0F0F12` | `dark:bg-charcoal-deep` |
| Kartochka fon | `#1A1A1F` | `dark:bg-graphite` |
| Asosiy matn | `#F5F0E8` | `dark:text-cream` |
| Aksent oltin | `#D4AF37` | `dark:text-gold-bright` |

### Tailwind config

```javascript
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: '#FAF7F2',
          100: '#F4F2EE',
        },
        charcoal: {
          DEFAULT: '#1A1A1A',
          deep: '#0F0F12',
        },
        gold: {
          DEFAULT: '#C9A961',
          dark: '#9C7E3D',
          light: '#E8D5A4',
          bright: '#D4AF37',
        },
        graphite: '#1A1A1F',
        'soft-gray': '#6B6B6B',
        'light-gray': '#E5E5E5',
        success: '#3D8B5A',
        warning: '#D68C3C',
        danger: '#B5453C',
        info: '#1E3A5F',
      },
    },
  },
};
```

---

## Tipografiya

### Shrift oilasi

```css
/* Sarlavhalar — serif (luxury) */
--font-serif: 'Playfair Display', 'Cormorant Garamond', Georgia, serif;

/* Asosiy matn — sans-serif (zamonaviy) */
--font-sans: 'Inter', 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;

/* Kod va raqamlar */
--font-mono: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
```

**Muhim:** Har shrift Cyrillic Extended va Latin Extended-A subset'ni
qo'llab-quvvatlashi shart (lotin va kirill ikkalasi uchun).

### Type scale

| Element | Size | Line height | Weight | Font |
|---|---|---|---|---|
| Display 1 | 56px | 64px | 700 | serif |
| Display 2 | 48px | 56px | 700 | serif |
| H1 | 36px | 44px | 700 | serif |
| H2 | 28px | 36px | 600 | serif |
| H3 | 22px | 30px | 600 | serif |
| H4 | 18px | 26px | 600 | sans |
| Body Large | 16px | 26px | 400 | sans |
| Body | 14px | 22px | 400 | sans |
| Body Small | 13px | 20px | 400 | sans |
| Caption | 12px | 18px | 400 | sans |
| Mono | 13px | 20px | 400 | mono |

### Tailwind utility'lar

```html
<h1 class="font-serif text-4xl font-bold leading-tight">
  Sarlavha
</h1>

<p class="font-sans text-base leading-relaxed text-charcoal">
  Asosiy matn.
</p>

<code class="font-mono text-sm bg-cream-100 px-2 py-0.5 rounded">
  identifier
</code>
```

---

## Spacing tizimi

8px grid — har spacing 4 yoki 8 ning ko'paytmasi.

| Token | Value | Tailwind |
|---|---|---|
| 1 | 4px | `p-1`, `m-1` |
| 2 | 8px | `p-2`, `m-2` |
| 3 | 12px | `p-3`, `m-3` |
| 4 | 16px | `p-4`, `m-4` |
| 6 | 24px | `p-6`, `m-6` |
| 8 | 32px | `p-8`, `m-8` |
| 12 | 48px | `p-12`, `m-12` |
| 16 | 64px | `p-16`, `m-16` |
| 24 | 96px | `p-24`, `m-24` |

**Generous whitespace** — luxury hissi uchun. Card padding `p-6` yoki `p-8`,
sahifa container `p-8`.

---

## Border radius

| Token | Value | Foydalanish |
|---|---|---|
| sm | 4px | Badge, chip |
| md | 8px | Button, input |
| lg | 12px | Card |
| xl | 16px | Modal |
| 2xl | 24px | Hero sections |
| full | 9999px | Avatar, pill |

---

## Soyalar

```css
/* Default elevations */
--shadow-sm: 0 1px 2px rgba(26, 26, 26, 0.04);
--shadow-md: 0 4px 12px rgba(26, 26, 26, 0.06);
--shadow-lg: 0 12px 32px rgba(26, 26, 26, 0.08);
--shadow-xl: 0 24px 64px rgba(26, 26, 26, 0.10);

/* Premium gold glow */
--shadow-gold: 0 4px 16px rgba(201, 169, 97, 0.20);
```

Tailwind: `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-gold`.

---

## Komponentlar

### Button

3 ta variant:

```typescript
// Primary (CTA) — gold
<Button variant="primary">Saqlash</Button>

// Secondary — ko'mir border
<Button variant="secondary">Bekor</Button>

// Ghost — transparent
<Button variant="ghost">Boshqa</Button>
```

3 ta o'lcham: `sm`, `md` (default), `lg`.

```css
.btn-primary {
  background: linear-gradient(135deg, #C9A961, #9C7E3D);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-gold);
}
```

### Card

```html
<div class="bg-white border border-light-gray rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow">
  <h3 class="font-serif text-lg mb-2">Sarlavha</h3>
  <p class="text-soft-gray">Mazmun</p>
</div>
```

**Premium card** (gold border):

```html
<div class="bg-white border-2 border-gold-light rounded-lg p-8 shadow-gold">
  <!-- ... -->
</div>
```

### Input

```html
<div>
  <label class="block text-sm font-medium text-charcoal mb-2">
    Telefon raqami
  </label>
  <input
    type="tel"
    class="w-full px-4 py-3 border border-light-gray rounded-md
           focus:border-gold focus:ring-2 focus:ring-gold/20
           transition-all bg-white text-charcoal
           placeholder:text-soft-gray"
    placeholder="+998 90 123 45 67"
  />
  <p class="text-xs text-soft-gray mt-1">Format: +998 XX XXX XX XX</p>
</div>
```

### Badge

```html
<!-- Default -->
<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-cream-100 text-charcoal">
  Yangi
</span>

<!-- Gold (premium) -->
<span class="bg-gold/10 text-gold-dark border border-gold-light">
  VIP
</span>

<!-- Status colors -->
<span class="bg-success/10 text-success">Sotildi</span>
<span class="bg-warning/10 text-warning">Kutilmoqda</span>
<span class="bg-danger/10 text-danger">Yo'qoltirildi</span>
```

### Sidebar

```
┌─────────────────────┐
│  💎 NEXUS AI        │  Brand area (gold accent)
├─────────────────────┤
│  🏠 Bosh sahifa     │  Active: bg-cream-100 + left gold border
│  👥 CRM             │  Hover: bg-cream-100/50
│  ✍️  SMM            │
│  📈 Reklama         │
│  💬 Inbox      🔴12 │  Badge — qizil dot
│  ✅ Vazifalar  🔴3  │
│  📊 Hisobotlar      │
│  🔗 Integratsiyalar │
├─────────────────────┤
│  👤 Xodimlar        │
│  ⚙️  Sozlamalar     │
├─────────────────────┤
│  💡 AI Yordamchi    │  Gold accent, doim pastda
│  📞 Yordam          │
└─────────────────────┘
```

Sidebar yig'iladi (`w-16` faqat ikonlar holati).

---

## Layout standartlari

### Sahifa container

```html
<div class="min-h-screen bg-cream">
  <Sidebar />
  <div class="ml-64">  <!-- Sidebar offset -->
    <Header />
    <main class="p-8 max-w-7xl mx-auto">
      <!-- Sahifa kontenti -->
    </main>
  </div>
</div>
```

### Sahifa header

```html
<div class="flex items-center justify-between mb-8">
  <div>
    <nav class="text-sm text-soft-gray mb-2">
      <a>CRM</a> / <a>Mijozlar</a>
    </nav>
    <h1 class="font-serif text-3xl text-charcoal">
      Mijozlar
    </h1>
  </div>
  <Button variant="primary">+ Yangi mijoz</Button>
</div>
```

### Grid

12-column grid (Tailwind):

```html
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-3">  <!-- Chap -->
    <Card />
  </div>
  <div class="col-span-6">  <!-- O'rta -->
    <Card />
  </div>
  <div class="col-span-3">  <!-- O'ng -->
    <Card />
  </div>
</div>
```

---

## Animatsiya va interaktivlik

### Tezliklar

```css
--duration-fast: 150ms;     /* Hover, focus */
--duration-base: 200ms;     /* Default */
--duration-slow: 300ms;     /* Modal, drawer */
--duration-page: 500ms;     /* Sahifa o'tish */

--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Mikrointeraktsiyalar

**Tugma hover:**
```css
transform: translateY(-1px);
box-shadow: var(--shadow-gold);
transition: all 200ms ease;
```

**Card hover:**
```css
box-shadow: var(--shadow-lg);
transition: box-shadow 200ms ease;
```

**Loading state:**
- Skeleton (cream-100 background, gold shimmer)
- Spinner (gold ring)
- Progress bar (gradient gold)

**Toast/notification:**
- Slide-in from top-right
- Auto-dismiss 4 sek (success), 6 sek (error)
- Gold accent line on left

### Page transitions

Framer Motion bilan:

```typescript
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {children}
</motion.div>
```

---

## Tasvir va illyustratsiya

### Logo

NEXUS AI logo — 💎 ikon (oltin) + "NEXUS AI" wordmark (serif, charcoal yoki cream).

### Empty state'lar

Har "ma'lumot yo'q" ekran uchun:
- Yumshoq illyustratsiya (line art, gold accent)
- Sarlavha (serif)
- Tushuntirish (1-2 jumla)
- CTA tugma

Misol:

```
┌────────────────────────────────┐
│       [Illyustratsiya]         │
│                                │
│   Mijozlar hali yo'q           │
│   Birinchi mijozingizni qo'shing│
│                                │
│   [+ Mijoz qo'shish]           │
└────────────────────────────────┘
```

### Avatar

- Default — ism initialari (gold gradient fon)
- Yuklangan rasm
- Status nuqta (online/offline) — pastki o'ng burchakda

---

## Iconography

**Lucide Icons** (lucide-react) — sodda, bir xil. 24x24 default.

```typescript
import { Home, Users, MessageCircle } from 'lucide-react';

<Home className="w-5 h-5 text-gold" />
```

**Maxsus ikonlar** (modul logolari): SVG, monokrom, 1.5px stroke.

---

## Responsive breakpointlar

```css
sm: 640px    /* Mobile landscape */
md: 768px    /* Tablet */
lg: 1024px   /* Desktop */
xl: 1280px   /* Wide desktop */
2xl: 1536px  /* Ultra-wide */
```

**Strategiya:** Mobile-first, lekin asosiy ish desktop'da. Telegram WebApp uchun
mobil ko'rinish alohida (375px viewport).

---

## Accessibility (a11y)

1. **Kontrast:** WCAG AA min (4.5:1 normal text, 3:1 large)
2. **Keyboard:** Har interaktiv element keyboard'dan kirish mumkin
3. **Focus state:** ko'rinarli (gold ring 2px)
4. **Aria labels:** har ikon-tugmaga
5. **Alt text:** rasm va illyustratsiyalar
6. **Reduced motion:** `prefers-reduced-motion` qo'llab-quvvatlash

---

## Theme switching

Light/Dark — har sahifada user tanlovi.

```typescript
// Header'da
<ThemeToggle />

// Tailwind dark: prefix
<div className="bg-cream dark:bg-charcoal-deep">
```

`useTheme` hook context orqali. localStorage'da saqlanadi.

---

## Component shablonlari

shadcn/ui'ni asos qilib oling, lekin **luxury theme bilan moslashtiring**:

```bash
# shadcn/ui o'rnatish
npx shadcn-ui@latest init

# Komponent qo'shish
npx shadcn-ui@latest add button
```

Keyin `components/ui/button.tsx`'da CSS variantlari va default classes'ni
luxury palette'ga moslashtiring.

---

## Tegishli fayllar

- [02-conventions.md](02-conventions.md) — Frontend kod konvensiyalari
- [modules/](modules/) — Har modulning UI tasviri
- shadcn/ui dokumentatsiyasi: https://ui.shadcn.com
- Tailwind: https://tailwindcss.com
