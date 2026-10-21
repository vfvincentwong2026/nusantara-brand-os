# Web Design System & UI/UX Engineering Skill

A comprehensive design engineering framework synthesized for modern, immersive, and high-conversion Web platforms. Designed for immediate application across UI/UX design, visual hierarchy, motion design, interactive states, component architecture, and accessibility standards.

---

## 1. Core Design Principles (设计原则)

* **Visual Hierarchy (层级):** Establish non-ambiguous visual weight using font sizing, font weight, contrast ratios, depth, and vertical space. Direct the user's primary attention to core actions before secondary contextual information.
* **Contrast (对比):** Maintain strong structural contrast between elements. Contrast must drive both intent (primary vs. secondary actions) and accessibility compliance.
* **Alignment (对齐):** Enforce strict visual grid alignment. Every layout node must attach cleanly to a vertical grid column or a horizontal alignment baseline.
* **Repetition & Consistency (重复与一致性):** Standardize design primitives across all views. Design tokens (colors, padding, border radii, motion curves, iconography) must remain cohesive across all interactive states.
* **Whitespace & Breathing Room (留白):** Treat space as an active visual material. Use deliberate, rhythmic spacing to lower visual clutter and enhance reading comprehension.
* **Immediate Feedback (反馈):** Every tactile, keyboard, or pointer interaction must trigger immediate, deterministic visual feedback (focus rings, state changes, audio/haptic responses).
* **Error Tolerance & Prevention (容错与防错):** Design system states defensively. Offer inline validation, clear error recovery steps, non-destructive undo patterns, and context-aware inputs.

---

## 2. Layout, Grid & Spacing Systems (布局与空间系统)

### Grid Structure
* **Desktop (1440px+):** 12-column dynamic grid | Margins: `80px` – `120px` | Gutter: `24px` or `32px`
* **Tablet (768px - 1023px):** 8-column layout | Margins: `32px` | Gutter: `16px`
* **Mobile (< 768px):** 4-column layout | Margins: `16px` or `20px` | Gutter: `12px` or `16px`

### Container Max-Widths
* **Reading/Editorial Container:** `680px` – `768px` (Optimized for 60–75 characters per line)
* **Standard Content Container:** `1200px`
* **Wide Dashboard/Gallery Container:** `1440px`
* **Full-Bleed Media Sections:** `100vw` with controlled interior padding.

### Spatial Scale (Base-8 System with Base-4 Sub-steps)
```css
--space-1:  4px;   /* Micro spacing, tight badge paddings */
--space-2:  8px;   /* Standard element gap, icon-to-text spacing */
--space-3: 12px;   /* Input inner padding, dense list spacing */
--space-4: 16px;   /* Base component padding, card internal spacing */
--space-6: 24px;   /* Standard section gap, card grid gutter */
--space-8: 32px;   /* Major component spacing, modal paddings */
--space-12: 48px;  /* Section padding, landing page vertical gaps */
--space-16: 64px;  /* Section separation for desktop layouts */
--space-24: 96px;  /* Major landing section gaps */
--space-32: 128px; /* Hero section top/bottom padding */
```

---

## 3. Visual System & Token Architecture (视觉与 Token 系统)

### Color Tokens
* **Primary / Accent:** Brand identity color, focus states, primary call-to-actions.
* **Surface / Background:**
  * `surface-base`: Global body background color.
  * `surface-card`: Elevated container surface.
  * `surface-overlay`: Modals, tooltips, popovers.
* **Neutral / Typography:**
  * `text-primary`: Pure contrast or near-black/white for maximum readability.
  * `text-secondary`: Muted labels, metadata, captions (60%–70% opacity).
  * `text-disabled`: Non-interactive labels (30%–40% opacity).
* **Feedback System:**
  * `status-success`: Positivity, completion, active connectivity.
  * `status-warning`: Cautionary alerts, non-blocking state notices.
  * `status-error`: Critical system failure, destructiveness, inline input errors.
  * `status-info`: Neutral informational banners.

### Typography Scale
```css
/* Base Line-Height Rules: Headings (1.1 - 1.25) | Body (1.5 - 1.6) */
--text-display: clamp(2.5rem, 5vw, 4.5rem); /* Display Titles */
--text-h1:      clamp(2.0rem, 3.5vw, 3.25rem);
--text-h2:      clamp(1.5rem, 2.5vw, 2.25rem);
--text-h3:      1.5rem;   /* 24px */
--text-h4:      1.25rem;  /* 20px */
--text-body-lg: 1.125rem; /* 18px */
--text-body:    1.0rem;   /* 16px */
--text-sm:      0.875rem; /* 14px */
--text-xs:      0.75rem;  /* 12px */
```

### Elevation & Border Radius
```css
--radius-sm: 4px;   /* Badges, tags, tiny buttons */
--radius-md: 8px;   /* Standard buttons, input fields, dropdowns */
--radius-lg: 16px;  /* Cards, dialog windows */
--radius-xl: 24px;  /* Floating navbars, prominent heroes */
--radius-full: 9999px; /* Pill buttons, avatars */

/* Layering Depth */
--elevation-flat: 0 0 0 1px var(--border-subtle);
--elevation-low:  0 2px 8px -2px rgba(0, 0, 0, 0.08);
--elevation-med:  0 8px 24px -4px rgba(0, 0, 0, 0.12);
--elevation-high: 0 20px 48px -8px rgba(0, 0, 0, 0.22);
```

---

## 4. Rich Motion, Cursor & Immersion System (动态视觉与鼠标交互)

### Media & Video Integration (动图与视频融合)
* **Background Blending:** Use WebP animations or loop MP4/WebM videos. Blend media into surrounding DOM nodes via `mix-blend-mode: screen` (dark UI) or `mix-blend-mode: multiply` (light UI) to hide background frame artifacts.
* **Performance Playback:**
  * Enforce `autoplay`, `muted`, `loop`, and `playsinline` attributes.
  * Utilize `IntersectionObserver` to trigger `.play()` when media elements enter the viewport and `.pause()` when scrolled out.

### Micro-interactions & Smooth Motion (微动效与过渡)
* **Physics Curves:**
  * Entrance / Easing Out: `cubic-bezier(0.16, 1, 0.3, 1)` (`easeOutExpo` – Snappy start, organic, smooth high-damping rest).
  * Exit / Easing In: `cubic-bezier(0.7, 0, 0.84, 0)` (`easeInExpo`).
  * Micro-interactions: `150ms` – `200ms` duration.
  * Modal/Drawer Transitions: `300ms` – `400ms` duration.

### Custom Cursor & Pointer Interactions (自定义光标)
* **Decoupled Architecture:** Dual-layer structure consisting of a hardware-accelerated center dot (`4px–6px`) and an outer tracking ring (`30px–40px`) updated via `requestAnimationFrame` and `transform: translate3d(x, y, 0)`.
* **Dynamic Hover States:**
  * **Magnetic Pull:** Outer button node pulls towards cursor within proximity radius (`20px`), while internal label shifts slightly toward cursor vector.
  * **Context Switching:** Hovering over dynamic cards scales the ring and displays contextual actions (`"VIEW"`, `"DRAG"`, `"EXPAND"`).
  * **Interactive Blend Mode:** Custom cursor applies `mix-blend-mode: difference` over contrasting backdrop zones.

### Mouse Parallax & Dynamic Light Effects (视差与光影)
* **Spotlight Tracker:** Attach CSS variables `--mouse-x` and `--mouse-y` dynamically on pointer move. Cards compute radial background gradients based on cursor position:
  ```css
  background: radial-gradient(
    600px circle at var(--mouse-x) var(--mouse-y),
    rgba(255, 255, 255, 0.06),
    transparent 40%
  );
  ```
* **Depth Parallax:** Apply subtle reverse shift on background vectors (`transform: translate3d(calc(x * -0.02px), calc(y * -0.02px), 0)`) relative to foreground elements to create spatial depth.

---

## 5. Component Standards (组件库与状态规范)

### Interactive State Matrix
All interactive components (Buttons, Inputs, Cards, Nav Links) must implement 5 distinct states:
1. **Default:** Baseline visual styling.
2. **Hover:** Surface contrast shifts up/down, cursor transitions, subtle upward translate (`translateY(-2px)`).
3. **Focus:** Keyboard focus indicator visible (`outline: 2px solid var(--primary)`, `outline-offset: 2px`).
4. **Active / Pressed:** Downward translate (`translateY(0)`), scale reduction (`scale(0.98)`).
5. **Disabled:** Opacity reduced to `0.4 - 0.5`, `pointer-events: none`, cursor reset.

### Core Component Specification
* **Buttons:** Primary, Secondary, Ghost, Destructive, Icon-Only. Always specify loading state spinners within button bounding boxes.
* **Forms & Fields:** Float/persistent labels, inline helper text, dynamic field validation (Success/Error icons + message below field).
* **Modals & Drawers:** Backdrop blur (`backdrop-filter: blur(12px)`), scroll-lock on document body, default focus trap, keyboard `Escape` key close trigger.
* **Empty States:** Clear visual indicator/illustration, plain English message, and direct action button.
* **Loading & Skeleton Screens:** Use matching component dimensions with a moving linear shimmer gradient instead of indefinite spinners for structural layouts.

---

## 6. Accessibility & Web Standards (可访问性)

* **Contrast Ratios (WCAG 2.1 AA):**
  * Normal Text (< 18pt / 24px): Minimum contrast ratio `4.5:1`.
  * Large Text (>= 18pt or bold 14pt): Minimum contrast ratio `3.0:1`.
  * Interactive UI Elements & Borders: Minimum contrast ratio `3.0:1`.
* **Keyboard Navigation:**
  * Logical tab indexing (`tabindex="0"` for custom interactive widgets, `tabindex="-1"` for script-focused containers).
  * No hidden focus states (`:focus-visible` must be explicit).
* **DOM Semantics & ARIA:**
  * Native HTML tags take priority (`<button>`, `<nav>`, `<aside>`, `<main>`, `<header>`).
  * Non-standard elements require ARIA tags (`role="dialog"`, `aria-expanded="false"`, `aria-live="polite"`).
* **Alternative Text & Media:**
  * Mandatory `alt` descriptions on context-rich images.
  * Purely decorative assets require `alt=""` or `aria-hidden="true"`.

---

## 7. Platform Constraints & Contexts (跨平台差异)

* **Web Desktop:** Hover-first interactions, cursor tracking, keyboard shortcut support, large viewport space utilization.
* **Mobile / Touch Web:**
  * Touch targets minimum size: `44x44px` or `48x48px`.
  * No critical information hidden purely behind hover states.
  * Account for mobile browser address bar height changes (`100vh` vs `100dvh`).
* **Admin / Web Applications:** Dense spatial scale, low visual embellishment, high information display density, fast pagination, deep filter structures.

---

## 8. Internationalization & Localization (本地化适配)

* **Text Expansion Safeguards:**
  * Container components must accommodate **20% to 40% length variance** (e.g., English to German or Indonesian).
  * Avoid strict fixed-width text containers; utilize flexbox/grid auto-fit and wrapping logic.
* **Typography & Line Heights for CJK vs. Latin:**
  * CJK (Chinese, Japanese, Korean) text requires **higher line-heights** (minimum `1.6` to `1.75`) compared to English (`1.4` to `1.5`) due to character complexity.
* **RTL (Right-to-Left) Support:** Use CSS Logical Properties (`margin-inline-start`, `padding-block-end`) instead of directional properties (`margin-left`, `padding-bottom`).
* **Formatting Localized Values:** Format dates, numbers, and currencies dynamically via the JS `Intl` API (`Intl.NumberFormat`, `Intl.DateTimeFormat`).