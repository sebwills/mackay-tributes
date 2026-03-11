# David MacKay Tributes — Site Spec

## Goals
- Public website honoring Sir David MacKay FRS, 10 years after his death.
- Beautiful, refined, typographically strong design inspired by his LaTeX typesetting.
- Simple hosting and maintenance.

## Hosting
- Hosted on Mythic Beasts (shell account).
- Prefer a static/JS site for simplicity. `cgi-bin` is available if needed later.
- Domain likely `davidmackay.uk`, but the base URL must be configurable in one place.

## Data Source
- Single source of truth: `tributes.csv`.
- Updates must not require rebuilding via an LLM.
- Acceptable update methods:
  - A local script that transforms CSV into static HTML (preferred for archival/scraping).
  - Runtime CSV reading in the browser (not acceptable for deep-link archival needs).
- CSV columns (header row): `Section, Name, How_knew_David, Tribute`.
 - Generated output is placed in `dist/` and fully re-creatable; source templates/scripts live outside `dist/`.

## Content Structure
- Tributes are grouped by section category (CSV values):
  - `CLARITY`: His intellectual strengths, first-principles thinking and insight.
  - `INFORMATION_THEORY`: His work on information theory (outside ITILA).
  - `ITILA`: Mentions of the book ITILA and its influence.
  - `SEWTHA`: Mentions of SEWTHA and sustainability work.
  - `DASHER`: His work on accessibility for disabled people.
  - `PERSON`: His humanity, generosity, bravery, campaigning, and genuineness.
- All sections can include tributes from close collaborators or distant admirers.

Each tribute displays:
- Tribute text.
- Author name.
- “How knew David” text shown after the author name at the bottom of each tribute.

## Navigation & Browsing
- Users can browse by:
  - Category.
  - Author.

### Category Browsing
- Each category view shows one tribute on screen at a time with easy navigation to the next/previous.
- Order is randomized on each visit/load (client-side reorder of already-present HTML).

### Author Browsing
- Author list with one-tribute-at-a-time navigation (same behavior as category browsing).
  - Each author has a single tribute; author pages typically show one tribute.
  - If multiple tributes share the same author name (e.g., "Anon"), list them all on that author page.

## Home Page
- Top section includes:
  - Title heading.
  - Short summary of who David was.
  - Photo from `images/` folder (CC licensed).
- Prominent links/buttons:
  - “Browse by author”.
  - “Browse by category”.
- Tribute carousel:
  - Randomly shuffled tributes.
  - Previous/next controls.
  - Auto-advance every 60 seconds.

## Design Direction
- Clean, refined, highly readable typography (serif-forward).
- Clear visual hierarchy, generous spacing.
- Overall aesthetic should feel intentional and calm.

## Configurability
- Base URL/domain is set in a single config location.

## App Architecture
- URL scheme supports deep links to category and author pages.
- Prefer static HTML output for each deep link (to allow archiving/scraping without JS).

## URL Scheme
- Category: `/category/<slug>` (slug is URL-safe; spaces and punctuation removed/normalized).
- Author: `/author/<slug>` (slug derived from author name).
- Slug rules: replace spaces with `-`, remove punctuation, lowercase, collapse multiple dashes.

## Open Questions
- Should the site be a single-page app with dynamic routing, or multiple static pages?
- Preferred CSV column names (so we can map fields precisely).
- Exact layout for “browse by author”: grouped list, index A–Z, or author detail pages?
- Any preferred fonts or typographic references to mirror David’s style?
