---
name: single-file-app
description: Build complete web tools as a single HTML file - vanilla JS, inline CSS, localStorage, offline-first. Use when creating calculators, dashboards, generators, or any standalone browser tool without a backend.
tags:
  - html
  - vanilla-js
  - offline
  - single-file
  - no-framework
version: 1.3
---

# Single-File Apps - Claude Skill

> Start simple.
> One HTML file, vanilla JavaScript, zero dependencies, offline-first.
> Add complexity only when the problem proves it is necessary.
> Simplicity is the default, not a religion.

---


## When to Use This Skill

Use this skill when building:
- **Calculators** - electrical, financial, unit converters, estimators
- **Dashboards** - personal analytics, trackers, monitors
- **Generators** - invoice, document, PDF, QR code
- **Editors** - markdown, text, code snippet tools
- **Utilities** - formatters, validators, converters
- **Small business tools** - inventory, booking, quoting

Do NOT use this skill when building:
- Multi-user applications requiring real-time sync
- Apps with complex authentication flows
- Large-scale SPAs with 10+ views
- Projects that already have a React/Vue codebase

## Core Philosophy

Every problem has a simple solution. Your job is to find it - not to engineer around it.
A single HTML file with inline CSS and JS is not a limitation. It is a feature.
If it works offline, opens instantly, and requires no installation - it is better by default.

---

## Rules

### 1. Start with one file
- HTML, CSS, and JavaScript live in one `.html` file by default
- Split into multiple files **only** when a single file exceeds ~800 lines and becomes genuinely hard to navigate
- No `package.json`. No `node_modules`. No build step - unless they solve a real problem
- If you catch yourself thinking "I'll just add a second file" - stop and ask: does the complexity truly require it?

### 2. Dependencies must justify their existence
- Vanilla JS first. Always
- Every dependency must earn its place - ask "what problem does this solve that I can't solve in 10 lines?"
- Need a chart? Try Canvas API before reaching for Chart.js
- Need animations? Try CSS before reaching for GSAP
- CDN libraries are fine for online tools - load from cdnjs.cloudflare.com
- **If the app must work offline or via `file://`** - inline the library instead of CDN: copy the minified source into a `<script>` tag
- Avoid build tools (npm, webpack, vite) unless they solve a real problem. Vite is not evil - using it for a 200-line calculator is

### 3. Keep it lean
- Target under 500 lines for simple tools, under 1000 for complex ones
- If approaching the limit - simplify the feature, not the code quality
- Every line must earn its place

### 4. Ask before big changes
- If a task requires restructuring more than 30% of existing code - ask first
- Never silently refactor working code
- Never rename variables or functions unless asked
- "It works" is always more important than "it's elegant"

### 5. Offline first
- Never assume internet access for core functionality
- Data stays local - localStorage, sessionStorage, or in-memory
- No API calls to external services unless explicitly requested
- Backend is fine when the problem genuinely requires it: auth, multi-user sync, backups. Not for a todo list
- **CDN vs offline:** CDN is fine when internet is assumed. If the app must work via `file://` or without internet - inline all dependencies

---

## HTML Structure

Use semantic HTML. Not everything is a `div`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Name</title>
  <style>
    /* All CSS here */
  </style>
</head>
<body>
  <header><!-- navigation, logo, actions --></header>
  <main><!-- primary content --></main>
  <footer><!-- secondary info --></footer>
  <script>
    // All JavaScript here
  </script>
</body>
</html>
```

- Use `<header>`, `<main>`, `<nav>`, `<section>`, `<footer>` - not `<div>` for everything
- CSS always in `<style>` in `<head>`
- JS always in `<script>` before `</body>`
- No inline `style=""` attributes unless dynamic
- No `onclick=""` attributes - use `addEventListener` in JS

---

## Accessibility

Every app must be usable by keyboard and screen readers:

- Every `<input>` must have a `<label>` or `aria-label`
- Icon-only buttons must have `aria-label` or `title`
- Visible `:focus` style on all interactive elements
- Color contrast must be readable (4.5:1 minimum)
- Keyboard navigation must work - `Tab`, `Enter`, `Escape`

```html
<!-- Good -->
<label for="taskInput">Task name</label>
<input id="taskInput" type="text" aria-label="Task name">
<button aria-label="Delete task" title="Delete">✕</button>

<!-- Bad -->
<input type="text" placeholder="Task name">
<button>✕</button>
```

---

## JavaScript Rules

- Use vanilla JS. No jQuery. No lodash for simple tasks
- Use `const` and `let`. Never `var`
- Prefer functions over classes - but use whichever makes the code simpler
- Keep functions small and named clearly
- Comment only what is not obvious
- Use event delegation for dynamic lists:

```javascript
// Good - one listener for all items
container.addEventListener('click', e => {
  if (e.target.matches('.delete')) deleteItem(e.target.dataset.id);
  if (e.target.matches('.checkbox')) toggleItem(e.target.dataset.id);
});

// Bad - listener on every item
items.forEach(item => {
  item.querySelector('.delete').addEventListener('click', ...);
});
```

---


## Security - XSS Prevention

**Never insert user input directly into innerHTML.** Single-file apps often render user content - always sanitize first:

```javascript
// DANGEROUS - XSS vulnerability
element.innerHTML = userInput;

// SAFE - escape before inserting
function escape(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
element.innerHTML = escape(userInput);

// SAFEST - use textContent for plain text
element.textContent = userInput;
```

This applies to: todo items, notes, invoice fields, search results, any user-typed content rendered to the DOM.

---

## CSS Rules

- CSS variables for all colors, spacing, and radius - defined in `:root`
- No magic numbers - extract everything to variables:

```css
:root {
  --radius: 8px;
  --gap: 16px;
  --header-height: 60px;
}
```

- Mobile-first. Always add `max-width` and responsive layout
- No CSS frameworks (Bootstrap, Tailwind) unless explicitly asked
- Flexbox and Grid - use them
- Always support both dark and light themes
- Default: follow system preference via `prefers-color-scheme`
- Always add a manual toggle button in the header

```css
/* Dark theme - default */
:root {
  --bg: #0F1117; --bg2: #1A1D27; --bg3: #232635;
  --border: #2E3148; --accent: #6C63FF; --accent2: #5A52E0;
  --accent-dim: rgba(108,99,255,0.12);
  --text: #F0F0F0; --text2: #8B8FA8;
  --green: #4ADE80; --red: #F87171; --radius: 10px;
}

/* Light theme */
[data-theme="light"] {
  --bg: #F8F9FC; --bg2: #FFFFFF; --bg3: #F0F2F8;
  --border: #E2E5F0; --accent: #6C63FF; --accent2: #5A52E0;
  --accent-dim: rgba(108,99,255,0.08);
  --text: #1A1A2E; --text2: #6B7280;
  --green: #16A34A; --red: #DC2626;
}

@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --bg: #F8F9FC; --bg2: #FFFFFF; --bg3: #F0F2F8;
    --border: #E2E5F0; --text: #1A1A2E; --text2: #6B7280;
    --green: #16A34A; --red: #DC2626;
  }
}
```

> **Accent color guide:**
> `#6C63FF` purple - productivity · `#0EA5E9` blue - tech
> `#10B981` green - finance · `#F59E0B` amber - creative
> `#FF6B00` orange - industrial (e.g. ElectroKit)

---

## Theme Toggle Pattern

```javascript
function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  document.getElementById('themeBtn').textContent = theme === 'dark' ? '☀️' : '🌙';
  save('theme', theme);
}
applyTheme(load('theme', null) || getSystemTheme());
document.getElementById('themeBtn').addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme');
  applyTheme(cur === 'dark' ? 'light' : 'dark');
});
```

---

## Data & Storage

- Use `localStorage` for persistent data
- Always wrap in try/catch - localStorage can fail in private mode
- Version your data to handle future migrations

```javascript
const APP_VERSION = 1;

function save(key, data) {
  try { localStorage.setItem(key, JSON.stringify(data)); } catch(e) {}
}

function load(key, fallback) {
  try {
    const v = localStorage.getItem(key);
    const data = v ? JSON.parse(v) : fallback;
    return migrate(data);
  } catch(e) { return fallback; }
}

// Version migration - runs automatically on every load()
function migrate(data) {
  if (!data || !data.__version || data.__version < APP_VERSION) {
    // add migration logic here when APP_VERSION bumps
    if (data) data.__version = APP_VERSION;
  }
  return data;
}
```

---

## Export / Import Data

Every app that stores user data should support export and import:

```javascript
// Export to JSON file
function exportData() {
  const data = JSON.stringify(load('appData', {}), null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'backup.json';
  a.click();
}

// Import from JSON file
function importData(file) {
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      save('appData', data);
      location.reload();
    } catch(e) { alert('Invalid file'); }
  };
  reader.readAsText(file);
}
```

---

## Print & PDF

Use `window.print()` - no libraries needed:

```css
@media print {
  header, .no-print, button { display: none !important; }
  body { background: white; color: black; }
  .card { box-shadow: none; border: 1px solid #ddd; }
}
```

---

## What to Say vs What to Do

| User says | You do |
|-----------|--------|
| "Add a feature" | Add it in the same file |
| "Make it look better" | Improve CSS only |
| "Refactor this" | Ask what specifically |
| "Add a database" | Use localStorage |
| "Deploy this" | GitHub Pages - 3 steps |
| "Split into components" | Only if file is 800+ lines |
| "Add a backend" | Only if auth/sync truly requires it |
| "Add React" | Ask why - if complexity justifies it, proceed |

---

## Optional: PWA Support

Add PWA only when users need to install the app on their device and use it daily offline.

**Use PWA for:** tools used every day, installed on device (BabyKit, StockKit, AutoKit)
**Skip PWA for:** one-time generators, calculators, simple utilities

> **Note:** PWA (service worker + manifest) requires https or localhost - it does NOT work when opening via `file://`. If your app opens directly as a file, skip PWA.

Requires 2 additional files - this is the only justified exception to the one-file rule:

**manifest.json**
```json
{
  "name": "App Name",
  "short_name": "App",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#YOUR_BG_COLOR",
  "theme_color": "#YOUR_ACCENT_COLOR",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**sw.js** (minimal service worker)
```javascript
const CACHE = 'app-v1';
const FILES = ['./', './index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
});
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
```

**In your HTML `<head>`:**
```html
<link rel="manifest" href="manifest.json">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js');
  }
</script>
```

---

## Priority When Used With ship-it

When both `single-file-app` and `ship-it` skills are active together:
- `ship-it` controls **scope and speed** - cut features, ship fast
- `single-file-app` controls **how to build** - one file, vanilla JS, offline
- Accessibility minimum (label, aria-label, keyboard) is **never cut** even under ship-it pressure
- localStorage safety (try/catch) is **never cut**

---

## Pre-ship Checklist

Before publishing your single-file app:

- [ ] Works offline - no network requests for core features
- [ ] `localStorage` wrapped in `try/catch`
- [ ] Keyboard navigation works - `Tab`, `Enter`, `Escape`
- [ ] Dark / light theme toggle present and saves to localStorage
- [ ] Mobile layout tested - resize to 375px width
- [ ] Export / import implemented if app stores user data
- [ ] All inputs have `label` or `aria-label`
- [ ] Icon-only buttons have `title` or `aria-label`
- [ ] Empty state shown when no data exists
- [ ] File opens directly in browser without a server

---

## Anti-Patterns

❌ Creating `src/` folder for a simple tool
❌ Adding React for "better component management"
❌ TypeScript for a 200-line script
❌ Setting up a build pipeline before writing logic
❌ Silently refactoring working code
❌ Using a backend for data a localStorage can hold
✅ One file. Vanilla JS. Works offline. Ships in minutes.

---

## Deployment

```
1. Create GitHub repository
2. Upload the .html file
3. Settings → Pages → Deploy from branch
```

Live at `https://username.github.io/repo-name/` - free, forever, no server.

---

## Real World Examples

| App | Lines |
|-----|-------|
| Calculator | ~80 |
| Todo list + localStorage | ~150 |
| Markdown editor + preview | ~200 |
| Budget tracker + charts | ~350 |
| Invoice generator + PDF | ~400 |
| Electrical calculator + estimates | ~900 |

If these fit in one file - your app probably does too.

---


