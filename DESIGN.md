# DESIGN.md

> 让“时令特色产品市场”像一个清爽、可信、好操作的地方特产交易工作台。

## 1. Visual Theme & Atmosphere

**Style**: Organic Professional Market UI  
**Keywords**: 自然、清爽、可信、信息清晰、轻盈、季节感、可操作  
**Tone**: 温润但不松散，友好但不幼稚，专业但不冰冷  
**Feel**: 像一个整洁的农产品集市管理台，商品、订单、投诉都能快速扫读。

**Interaction Tier**: L2 流畅交互  
**Dependencies**: CSS + 原生 JavaScript + Bootstrap Icons；不引入 GSAP/Lenis。

## 2. Color Palette & Roles

```css
:root {
  --bg: #f3f7f1;
  --bg-soft: #eef5ec;
  --surface: #ffffff;
  --surface-alt: #fbf8ef;
  --surface-hover: #f7fbf5;

  --border: #dfe8dc;
  --border-strong: #bed0b8;
  --border-hover: #93b58a;

  --text: #1f2f28;
  --text-secondary: #5c6f63;
  --text-tertiary: #879589;
  --text-inverse: #ffffff;

  --accent: #3f7d4f;
  --accent-hover: #326540;
  --accent-soft: #e4f1df;
  --accent-blue: #386c8f;
  --accent-clay: #b86f42;
  --accent-red: #b5473f;

  --bg-rgb: 243, 247, 241;
  --surface-rgb: 255, 255, 255;
  --accent-rgb: 63, 125, 79;
  --blue-rgb: 56, 108, 143;
  --clay-rgb: 184, 111, 66;
  --red-rgb: 181, 71, 63;

  --success: #3f7d4f;
  --error: #b5473f;
  --warning: #b86f42;
  --info: #386c8f;
}
```

**Color Rules:**
- 所有自定义颜色通过 CSS 变量引用。
- 主操作使用绿色，信息类使用蓝色，投诉和退款使用陶土/红色。
- 背景只做轻微冷暖分层，避免整页变成单一绿色。

## 3. Typography Rules

**Font Stack:**
```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700;800&display=swap');
```

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| App H1 | Noto Sans SC | 1.55rem | 800 | 1.35 | 0 |
| Section H2 | Noto Sans SC | 1.2rem | 700 | 1.45 | 0 |
| H3 | Noto Sans SC | 1rem | 700 | 1.5 | 0 |
| Body | Noto Sans SC | 0.94rem | 400 | 1.75 | 0.02em |
| Label | Noto Sans SC | 0.8rem | 700 | 1.4 | 0.02em |
| Small | Noto Sans SC | 0.82rem | 500 | 1.6 | 0.02em |

**Typography Rules:**
- 中文字体必须优先使用 Noto Sans SC，保证中文界面稳定。
- 页面标题控制在应用级字号，不使用落地页巨型标题。
- 正文行高不低于 1.7，提升中文可读性。
- **NEVER use**: Comic Sans、纯英文系统字体链、负字距。

**Text Decoration:**
- 当前风格不使用渐变文字和投影。
- 小标题可使用细边框或浅色底强调。
- 正文不添加阴影、描边或渐变。

## 4. Component Stylings

### Buttons
```css
.btn {
  border-radius: 8px;
  min-height: 40px;
  font-weight: 700;
  transition: transform .18s ease, box-shadow .18s ease, background-color .18s ease, border-color .18s ease;
}
.btn:hover { transform: translateY(-1px); box-shadow: var(--shadow-soft); }
.btn:active { transform: translateY(0) scale(.98); box-shadow: none; }
.btn:focus-visible { outline: 3px solid rgba(var(--accent-rgb), .22); outline-offset: 2px; }
.btn:disabled { opacity: .55; cursor: not-allowed; transform: none; box-shadow: none; }
```

### Cards
```css
.product-card,
.data-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.product-card:hover,
.data-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-hover);
  box-shadow: var(--shadow-lift);
}
.product-card:focus-within,
.data-card:focus-within { border-color: var(--accent); }
```

### Navigation
```css
.navbar {
  background: rgba(31, 47, 40, .94);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(var(--surface-rgb), .12);
}
.navbar.scrolled {
  box-shadow: var(--shadow-nav);
}
```

### Links
```css
.nav-link,
a {
  transition: color .18s ease, background-color .18s ease;
}
.nav-link:hover,
a:hover { color: var(--accent-soft); }
.nav-link:focus-visible,
a:focus-visible { outline: 3px solid rgba(var(--accent-rgb), .22); outline-offset: 2px; }
```

### Tags / Badges
```css
.badge {
  border-radius: 999px;
  font-weight: 700;
  padding: .4rem .58rem;
}
```

### Forms and Tables
```css
.form-control,
.form-select {
  border-radius: 8px;
  border-color: var(--border);
  min-height: 42px;
}
.form-control:focus,
.form-select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 .22rem rgba(var(--accent-rgb), .14);
}
.table-responsive {
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
}
```

## 5. Layout Principles

**Container:**
- Max width: 1220px
- Desktop padding: 24px
- Mobile padding: 14px

**Spacing Scale:**
- Section padding: 24px desktop / 16px mobile
- Component gap: 16px
- Card internal padding: 18px

**Grid:**
```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}
```

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | no shadow, border only | tables, forms |
| Subtle | 0 10px 24px rgba(31,47,40,.06) | cards |
| Elevated | 0 18px 42px rgba(31,47,40,.12) | hover cards, modals |
| Nav | 0 10px 30px rgba(31,47,40,.14) | sticky nav |

## 7. Animation & Interaction

**Motion Philosophy**: 用轻微位移、透明度和阴影做节奏，不做重滚动叙事。  
**Tier**: L2

### Dependencies
```html
<!-- Bootstrap + Bootstrap Icons already used. No new animation dependency. -->
```

### Entrance Animation
```css
.reveal {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity .55s cubic-bezier(.16,1,.3,1), transform .55s cubic-bezier(.16,1,.3,1);
}
.reveal.in-view {
  opacity: 1;
  transform: translateY(0);
}
```

### Scroll Behavior
```js
function initScrollReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
}
```

### Hover & Focus States
```css
button,
.product-card,
.data-card,
.nav-link {
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, color .18s ease;
}
```

### Special Effects
- 首页顶部使用轻量背景图片和数据摘要，不做全屏 hero。
- 商品卡片图片 hover 轻微放大。
- 导航滚动后加阴影。

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
  .reveal { opacity: 1; transform: none; }
}
```

## 8. Do's and Don'ts

### Do
- 优先让商品、订单、投诉信息可扫读。
- 用图标辅助动作按钮，但文字命令必须保留。
- 商品卡片必须有真实图片。
- 管理页保持表格密度，不做宣传式大卡片。
- 移动端按钮触摸区域不小于 44px。

### Don't
- 不做全屏营销首页。
- 不使用大面积紫蓝渐变。
- 不把卡片嵌套进卡片。
- 不使用纯色图片占位。
- 不使用大圆角卡片，卡片半径不超过 8px。
- 不让文字和按钮在移动端挤出容器。
- 不引入重动画库。
- 不使用装饰性圆球、光斑或背景 blob。

## 9. Responsive Behavior

**Breakpoints:**
| Name | Width | Key Changes |
|------|-------|-------------|
| Desktop | > 992px | 三列商品，导航横向展示 |
| Tablet | 600px-992px | 两列商品，工具栏换行 |
| Mobile | < 600px | 单列商品，操作按钮换行，表格横向滚动 |

**Touch Targets:** minimum 44px  
**Collapsing Strategy:** Bootstrap navbar collapse；表格使用横向滚动；卡片操作按钮自动换行。

```css
@media (max-width: 600px) {
  .app-shell { padding-inline: 14px; }
  .product-grid { grid-template-columns: 1fr; }
  .btn { min-height: 44px; }
  .table-action-group { display: flex; flex-wrap: wrap; gap: 8px; }
}
```
