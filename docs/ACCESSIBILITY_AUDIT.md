# SelfDiary — Accessibility Audit Report (WCAG 2.1 AA)

> **Date:** 2026-03-14
> **Scope:** Web Client (`/web`) UI components, pages, and navigation
> **Standard:** WCAG 2.1 Level AA
> **Tools:** Manual code review, axe-core automated testing (Playwright integration)

---

## Executive Summary

The web client uses semantic HTML as its foundation (native `<button>`, `<input>`,
`<form>`, `<label>`, `<link>`, `<time>` elements), which provides a solid
accessibility baseline. However, several interactive patterns — notably the modal
dialog, tag badges, and mood selector — lack the ARIA semantics required for
screen reader and keyboard-only users.

| Rating | Count | Summary |
|--------|:-----:|---------|
| Critical | 1 | Modal has no `role="dialog"`, focus trap, or focus management |
| High | 4 | Error messages not linked to inputs, interactive spans with no role/keyboard, no skip-nav link, no `aria-live` on dynamic content |
| Medium | 5 | Missing `aria-pressed` on toggles, no `aria-current="page"`, color contrast failures on secondary text, no `aria-label` on icon-only buttons |
| Low | 3 | Placeholder contrast, missing `dateTime` attribute, decorative SVGs without `aria-hidden` |

---

## Findings by Criterion

### 1.1.1 Non-text Content (Level A)

| Component | Finding | Severity |
|-----------|---------|----------|
| EntryCard `★` (favorite) | Decorative star character has no `aria-label` or `role="img"` | Medium |
| Header hamburger SVG | SVG icon lacks `aria-hidden="true"` — screen readers may parse path data | Low |
| Modal close `×` button | No `aria-label="Close"` — announced as "times" or nothing | High |
| TagBadge remove `×` button | No `aria-label="Remove tag {name}"` | Medium |

**Remediation:**
```tsx
// Modal close button
<button onClick={onClose} aria-label="Close">×</button>

// Favorite star
<span role="img" aria-label="Favorite">★</span>

// SVG icons
<svg aria-hidden="true" ...>
```

---

### 1.3.1 Info and Relationships (Level A)

| Component | Finding | Severity |
|-----------|---------|----------|
| Input error message | `<p>` error not linked via `aria-describedby` to its input | High |
| Input `aria-invalid` | Missing when `error` prop is truthy | High |
| MoodSelector | No `role="radiogroup"` / `role="radio"` pattern; selected state not conveyed | Medium |
| Sidebar navigation | No `aria-label` on `<aside>`, no landmark distinction | Medium |

**Remediation for Input:**
```tsx
<input
  aria-invalid={!!error}
  aria-describedby={error ? `${inputId}-error` : undefined}
/>
{error && <p id={`${inputId}-error`} className="...">{error}</p>}
```

---

### 1.3.6 Identify Purpose (Level AAA — recommended)

| Component | Finding | Severity |
|-----------|---------|----------|
| LoginForm inputs | ✅ `autoComplete="email"` and `autoComplete="current-password"` present | Pass |

---

### 1.4.3 Contrast (Minimum) — Level AA: 4.5:1

| Element | Colors | Ratio | Status |
|---------|--------|:-----:|--------|
| Body text `text-gray-900` on `bg-gray-50` | #111827 on #F9FAFB | 16.8:1 | ✅ Pass |
| Entry body `text-gray-500` on white | #6B7280 on #FFFFFF | 4.6:1 | ✅ Pass (borderline) |
| Date text `text-gray-400` on white | #9CA3AF on #FFFFFF | 3.0:1 | ❌ **Fail** |
| Loading `text-gray-400` on white | #9CA3AF on #FFFFFF | 3.0:1 | ❌ **Fail** |
| Placeholder `placeholder-gray-400` | #9CA3AF on #FFFFFF | 3.0:1 | ⚠️ Low (placeholders advisory) |
| Error placeholder `placeholder-red-300` | #FCA5A5 on #FFFFFF | 2.4:1 | ⚠️ Low |
| TagBadge colors | User-defined | Varies | ❌ **No validation** |
| Disabled button (50% opacity) | Variable | ~2–3:1 | ⚠️ Medium (disabled exempt but poor UX) |

**Remediation:** Change `text-gray-400` → `text-gray-500` (4.6:1) for dates and
secondary text. Add contrast validation for user-defined tag colors.

---

### 2.1.1 Keyboard (Level A)

| Component | Finding | Severity |
|-----------|---------|----------|
| Buttons, Links, Inputs | ✅ All native elements are keyboard accessible | Pass |
| TagBadge with `onClick` | ❌ `<span>` is not focusable and has no keyboard handler | High |
| Modal backdrop | ❌ `onClick` on div but no keyboard equivalent | Medium |
| MoodSelector buttons | ✅ Native `<button>` elements — keyboard accessible | Pass |

**Remediation for TagBadge:**
```tsx
<span
  role="button"
  tabIndex={0}
  onClick={onClick}
  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick?.(); }}
>
```

---

### 2.4.1 Bypass Blocks (Level A)

| Component | Finding | Severity |
|-----------|---------|----------|
| Root layout | ❌ No skip-to-content link | High |

**Remediation:**
```tsx
// layout.tsx
<body>
  <a href="#main-content" className="sr-only focus:not-sr-only ...">
    Skip to content
  </a>
  ...
  <main id="main-content">...</main>
</body>
```

---

### 2.4.7 Focus Visible (Level AA)

| Component | Finding | Severity |
|-----------|---------|----------|
| Button | ✅ `focus:ring-2 focus:ring-offset-2` visible focus | Pass |
| Input | ✅ `focus:ring-2 focus:ring-indigo-500` visible focus | Pass |
| EntryCard (Link) | ⚠️ No explicit focus style — relies on browser default | Medium |
| MoodSelector buttons | ⚠️ No focus ring classes | Medium |
| TagBadge remove button | ❌ No focus styles | Medium |

---

### 4.1.2 Name, Role, Value (Level A)

| Component | Finding | Severity |
|-----------|---------|----------|
| Modal | ❌ Missing `role="dialog"`, `aria-modal="true"`, `aria-labelledby` | **Critical** |
| MoodSelector | ❌ Missing `aria-pressed` on toggle buttons | Medium |
| Sidebar active link | ❌ Missing `aria-current="page"` | Medium |
| Mobile nav | ❌ Same modal issues — no dialog role, no focus trap | Critical |

**Remediation for Modal:**
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <h2 id="modal-title">{title}</h2>
  ...
</div>
```

---

### 4.1.3 Status Messages (Level AA)

| Component | Finding | Severity |
|-----------|---------|----------|
| LoginForm error | ❌ No `role="alert"` or `aria-live="assertive"` | High |
| Loading state (Home) | ❌ No `role="status"` or `aria-live="polite"` | Medium |
| Search results | ❌ Result count changes not announced | Medium |

**Remediation:**
```tsx
{error && <div role="alert">{error}</div>}
```

---

## Automated Testing (axe-core + Playwright)

An automated accessibility test file has been created at
`web/e2e/accessibility.spec.ts` that uses `@axe-core/playwright` to scan key
pages for WCAG 2.1 AA violations.

**To run:**
```bash
cd web
npm install --save-dev @axe-core/playwright
npx playwright test e2e/accessibility.spec.ts
```

---

## Remediation Priority

| # | Finding | Criterion | Severity | Effort |
|---|---------|-----------|----------|--------|
| 1 | Modal: add `role="dialog"`, `aria-modal`, `aria-labelledby`, focus trap | 4.1.2 | Critical | Medium |
| 2 | Input: add `aria-describedby` + `aria-invalid` for errors | 1.3.1 | High | Small |
| 3 | Add `role="alert"` to form error messages | 4.1.3 | High | Small |
| 4 | TagBadge: add `role="button"`, `tabIndex`, keyboard handler | 2.1.1 | High | Small |
| 5 | Add skip-to-content link in root layout | 2.4.1 | High | Small |
| 6 | Fix color contrast: `text-gray-400` → `text-gray-500` | 1.4.3 | Medium | Small |
| 7 | MoodSelector: add `aria-pressed` to toggle buttons | 4.1.2 | Medium | Small |
| 8 | Add `aria-label` to icon-only buttons (`×` close, remove) | 1.1.1 | Medium | Small |
| 9 | Add `aria-current="page"` to active nav links | 4.1.2 | Medium | Small |
| 10 | Add focus ring to EntryCard, MoodSelector, TagBadge | 2.4.7 | Medium | Small |

---

## Conclusion

The application provides a solid HTML foundation with native interactive elements
and proper label associations on form fields. The primary areas requiring
attention are: (1) the modal dialog pattern which needs ARIA roles and focus
management, (2) linking error messages to inputs for screen reader users, and
(3) ensuring all interactive elements are keyboard accessible with visible focus
indicators.
