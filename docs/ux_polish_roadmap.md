# Soundmaze — UX Polish Roadmap

## Context

The audio player PoC is fully working: books load with audio, the player page has a dark immersive theme with choice reveal on audio end, and the Enchanted Forest demo book loads automatically on `docker-compose up`. The core flow (browse → play → choose → continue) works end to end.

The problem is everything *around* the player still looks like a 2019 Flask boilerplate. The player page is polished; the rest of the app is not. A first-time user encounters generic white pages, boilerplate text about Hack4Impact, and then suddenly drops into a dark immersive player — it feels like two different apps.

This document outlines the UX improvements needed to make the whole experience feel cohesive and purposeful.

---

## Current State (What the User Sees)

| Page | Current State | Problem |
|------|--------------|---------|
| **Homepage** (`main/index.html`) | Hack4Impact boilerplate text. Mentions Flask, SCSS, Miguel Grinberg. | No indication this is an audiobook platform. Confusing for any non-developer. |
| **Login/Register** (`account/login.html`) | White background, generic Semantic UI form. | No branding, no atmosphere. Looks like a developer admin panel. |
| **Book Library** (`books/index.html`) | Title says "Booklist". White cards on white background. | No cover art, no mood, no visual hierarchy. Doesn't invite exploration. |
| **Player** (`books/player.html`) | Dark theme (#1a1a2e), orange accents, choice reveal on audio end. | Best page in the app. But the visual jump from white pages to dark player is jarring. |
| **Story Endings** | "The End" + "Return to library" link. | No sense of accomplishment. No invitation to try other paths. |
| **Navigation** | Black Semantic UI top bar. Links: Home, About, Books, Dashboard, Account. | Generic. "About" goes to nothing useful. No Soundmaze identity. |
| **Progress/Continuity** | None. Close browser = lose your place. | No way to resume, no awareness of which paths you've explored. |

---

## Improvement Plan (Ordered by Impact)

### 1. Unified Dark Theme
**Effort:** Medium | **Impact:** High

Extend the player's dark aesthetic (`#1a1a2e` background, light text, orange/coral accents) to ALL pages — login, library, homepage, navigation. This is the single highest-impact change because it eliminates the "two different apps" feeling.

**Scope:**
- Create a new base stylesheet or override Semantic UI defaults with a dark theme
- Update `layouts/base.html` to use dark background and light text globally
- Restyle the navigation bar to match the player aesthetic
- Ensure forms (login, register, book upload) work on dark backgrounds
- The player page already has the right look — it becomes the reference for everything else

**Reference:** Player page styles in `templates/books/player.html` (the `<style>` block)

---

### 2. New Homepage
**Effort:** Low-Medium | **Impact:** High

Replace the Hack4Impact boilerplate with a Soundmaze-branded landing page.

**Content:**
- Soundmaze logo or stylized text header
- Tagline: "Choose your own path"
- Brief description: what the app is (interactive audiobooks with branching stories)
- Featured book: show the Enchanted Forest with a "Start Listening" call to action
- If user is logged in: skip marketing copy, show "Continue listening" or "Your books"
- If user is not logged in: show login/register CTA

**What to remove:**
- All references to Hack4Impact, Flask, SCSS, Semantic UI, Miguel Grinberg
- The "About" page link (or repurpose it as a "How it works" section)

---

### 3. Redesigned Book Library
**Effort:** Medium | **Impact:** High

Make the library page feel like browsing an audiobook catalogue, not a data table.

**Design:**
- Dark background consistent with new theme
- Book cards with: gradient or placeholder cover image, title, author, description (truncated), prominent "▶ Listen" button
- If the user has an in-progress session (future): show a "Continue" badge on the card
- Visual hierarchy: featured/newest books first

**Current file:** `templates/books/index.html`

---

### 4. Player Polish
**Effort:** Low | **Impact:** Medium-High

Small improvements to the best page in the app.

**Additions:**
- **Breadcrumb / chapter indicator** at the top: "Chapter 2" or a simple step counter. The waypoint number relative to the user's path, not the total book.
- **Richer ending screen:** Instead of just "The End", show: a brief congratulations, which path the user took (list of waypoint titles), "You found 1 of 4 endings", and a "Try a different path" button that links back to the start.
- **Smooth transition between waypoints:** Instead of a full page reload, consider a fade-out/fade-in CSS transition when clicking a choice.

**Data note:** The "1 of 4 endings" count requires knowing how many terminal waypoints (waypoints with no options) exist in the book. This is a simple query: `Waypoint.query.filter_by(book_id=X).filter(~Waypoint.id.in_(Option.query.with_entities(Option.sourceWaypoint_id))).count()`

---

### 5. Login/Register Styling
**Effort:** Low | **Impact:** Medium

Apply the dark theme to auth pages. Add Soundmaze branding.

**Changes:**
- Dark background, light text
- Soundmaze logo or name above the form
- Style form inputs for dark theme (dark input backgrounds, light borders, light text)
- "Forgot password" and "Register" links in accent colour

**Current files:** `templates/account/login.html`, `templates/account/register.html`

---

### 6. Basic Progress via localStorage
**Effort:** Low | **Impact:** Medium

Before building a full server-side UserSession model, use browser localStorage to track progress. This is cheap and gives immediate value.

**Implementation:**
- On the player page, when a waypoint loads: save `{bookId: X, waypointId: Y, timestamp: Z}` to localStorage
- On the library page: check localStorage for any saved progress, show a "Continue listening" badge on the book card with a link to the saved waypoint
- On story endings: save the ending to localStorage (`{bookId: X, endingsFound: [4, 7]}`)
- On the library card: show "2 of 4 endings found" if data exists

**Limitations:** Per-device only, cleared if browser data is cleared. But for a PoC this is perfectly fine. A server-side `UserSession` model can replace it later.

**Important:** This is purely additive JS in the player and library templates. No backend changes needed.

---

## Technical Notes

- **Semantic UI dependency:** The whole app currently uses Semantic UI for layout and components. The dark theme work will likely involve overriding a lot of Semantic UI defaults. At some point it may be cleaner to strip Semantic UI entirely and use simple custom CSS — but that's a bigger scope decision. For now, override in place.
- **CSS approach:** The player page uses an inline `<style>` block. For the unified theme, consider extracting shared styles into a new `dark-theme.css` file in `app/static/styles/` and including it from `_head.html`. Keep the player's inline styles for player-specific things.
- **No JS framework needed:** All interactions (transcript toggle, choice reveal, localStorage) are simple enough for vanilla JS. Don't introduce React/Vue for this.
- **Mobile-first:** All new CSS should be mobile-first. Test with Chrome DevTools device mode. The player already works well on mobile — maintain that standard.

---

## Suggested Session Order

**Session A: Visual Identity** (items 1, 2, 5)
- Create the dark theme base styles
- Restyle login/register
- Build new homepage
- One session because these are interconnected — the theme informs every page

**Session B: Library & Cards** (item 3)
- Redesign the book library with the new dark theme
- Build the book card component

**Session C: Player Polish** (item 4)
- Add breadcrumbs/chapter indicator
- Build the rich ending screen
- Add waypoint transitions

**Session D: Progress Tracking** (item 6)
- Add localStorage-based progress to player and library
- Show continuation badges and ending counts

---

## Files to Read Before Starting

For any session touching the frontend:
- `app/templates/layouts/base.html` — base template
- `app/templates/partials/_head.html` — asset includes
- `app/templates/macros/nav_macros.html` — navigation
- `app/templates/books/player.html` — the reference for the target aesthetic
- `app/assets.py` — Flask-Assets bundle definitions
- `app/static/styles/` — existing CSS
