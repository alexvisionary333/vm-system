# Site structure & AI-readability scan — visionarymedia.us

**Scanned:** 2026-08-28 · **Scope:** homepage + /contact, live production (Vercel, Next.js prerendered)
**Method:** raw HTML fetch as a non-JS crawler sees it, plus robots/sitemap/JSON-LD probe.
This is the Stage 2 site probe only. Stages 3–9 (prompt set, capture, platform metrics,
interpretation, record, call, pricing, proposal) have not been run.

---

## 1. Crawlability — not the constraint

| Check | Result |
|---|---|
| robots.txt | `User-Agent: * / Allow: /` — every AI crawler permitted |
| Sitemap declared | Yes, in robots.txt |
| Homepage status | 200, TTFB 0.27s, `x-nextjs-prerender: 1` |
| Server-rendered text | Yes — full copy present in HTML without JS |
| HSTS / HTTPS | `max-age=63072000` |

Rule this cause out. The engines can read the site fine. What they read is the problem.

---

## 2. Structure — findings

### 2.1 The sitemap declares one URL
`sitemap.xml` contains only `https://visionarymedia.us`. `/contact` is a real,
indexable 200 page and is **not in the sitemap**.

### 2.2 There is only one page
- `/services` → 307 → `/`
- `/case-studies` → 307 → `/`
- `/about` → 307 → `/`
- `/blog`, `/faq` → 404

All nav is in-page anchors (`/#services`, `/#work`, `/#contact`). An AI engine
cites a **URL**. There is exactly one citable URL, and it has to answer every
question at once. Four services, six case studies and four FAQ answers are all
competing for the same document embedding.

### 2.3 Heading outline is flat and incomplete

```
H1  Visionary Media — New York digital marketing and web development
H2  Our Story & Founding Principals
H2  What We Do
H2  Works
H2  Ready to grow?
H2  The things people ask first.
H2  Services / Company / Connect / Newsletter   (footer)
```

Zero `<h3>` on the page. The four services (`[01]`–`[04]`) and the four FAQ
questions are **not headings** — they are plain spans. Nothing below H2 is
addressable, so no engine can lift "Visionary Media — AI Search Visibility"
as a discrete claim.

### 2.4 Services are wrapped in anchor tags
Each service block sits inside `<a href="#contact">`, so the entire service
description is anchor text pointing at a fragment. That is link text, not
prose, to a parser.

### 2.5 Case studies link off-domain
GAME 7, Original Syndicate, Civic, OWATCH ME, Serafina, L'HOME all link to the
**client's** domain. Six proof assets, zero owned pages, six outbound links.
Nothing on visionarymedia.us describes what was done or what happened.

### 2.6 Missing semantic containers
`<article> 0` · `<ol> 0` · `<table> 0` · `<details>/<summary> 0` · `<time> 0` ·
`<figcaption> 0` · `<blockquote> 0` · `<strong>/<em> 0`.

Zero emphasis markup across ~600 words of unique copy means no term is marked
as important anywhere in the document.

---

## 3. Readability — the DOM duplication problem

The animated headings render **two or three copies of the same text** in the
HTML: a visually-hidden accessible copy, an `aria-hidden` character-split copy
(one `<span>` per letter — 198 `line-word` spans, 71 `aria-hidden` blocks), and
separate mobile/desktop variants.

Measured occurrences in the raw HTML:

| Phrase | Copies in DOM |
|---|---|
| "AI recommends your business." | 6 |
| "At Visionary Media we make brands visible…" | 4 |
| "Marketing That Moves Markets" | 4 |
| "Make sure" / "founded in 2022" / "Ready to grow" / FAQ heading | 2 each |

**Screen readers are fine** — the sr-only span is correct and the split copy is
properly `aria-hidden`. The exposure is that `aria-hidden` is an accessibility
attribute, not a crawler directive. Text extractors that strip tags without
honouring it produce this:

```
Make sure M a k e s u r e
AI recommends A I r e c o m m e n d s
your business. y o u r b u s i n e s s .
```

Raw extraction gives 1,036 words, of which roughly half is duplicate or
character-spaced noise. True unique body copy is ~600 words — thin for a page
that has to answer every category question on its own.

### 3.1 Every image has an empty alt
9 of 9 `<img>` tags carry `alt=""`. The six case-study images are additionally
`aria-hidden="true"`. Zero image-derived signal about GAME 7, Serafina, L'HOME
or anyone else.

---

## 4. The AI layer — what exists and what is missing

**Present (homepage and /contact, identical block):**
`Organization` + `ProfessionalService` (`@id` `#organization`) with name,
description, slogan, url, logo, image, telephone, PostalAddress, and two
`sameAs` (Instagram, X). Plus `WebSite` with `publisher` @id-linked. Clean,
valid, correctly graphed.

**Missing:**

| Type | Why it matters | Source already on the page |
|---|---|---|
| `FAQPage` | Four Q&As are already written and rendered — this is the single highest-leverage add. Questions and answers currently live in **separate DOM blocks**, so nothing pairs them | Cost / timeline / verticals / audit scope |
| `Service` ×4 | Makes each offering a retrievable entity instead of anchor text | The four `[01]`–`[04]` blocks |
| `Offer` / `priceRange` | "$1,000 a month" is stated in prose but nowhere machine-readable | FAQ answer 01 |
| `foundingDate: 2022` | Stated in prose, absent from schema | About copy |
| `Person` (founders) | Section is titled "Founding Principals" and names nobody. No E-E-A-T entity exists | — |
| `areaServed`, `knowsAbout` | Ties the entity to New York and to the AI-visibility topic cluster | Title, hero |
| `CreativeWork` / `Case Study` | Six named clients, zero structured proof | Work section |
| `Review` / `AggregateRating` | No third-party validation of any kind | — |
| `ContactPage` | /contact reuses the homepage graph verbatim | — |
| `BreadcrumbList` | No hierarchy exists to describe yet | — |
| `llms.txt` | 404. Not a ranking factor; it is a cheap, explicit statement of what the business is | — |

---

## 5. Priority order

1. **Break the site into pages.** `/services/ai-search-visibility`,
   `/services/web-design`, `/services/branding`, `/services/paid-advertising`,
   `/work/<client>` ×6, `/about`, `/faq`. Put all of them in the sitemap, plus
   `/contact`. One citable URL per question a buyer asks.
2. **Ship `FAQPage` schema** and re-render the FAQ so each question is an
   `<h3>` with its answer adjacent in the DOM. Cheapest credible win available.
3. **Fix the extraction noise.** Emit the clean sentence as the only text node
   a tag-stripper can reach — render the split-letter spans client-side after
   hydration, or move the animation to CSS on a single text node.
4. **Add `Service` ×4 with `Offer`/`priceRange`,** `foundingDate`, `areaServed`,
   `knowsAbout`, and `Person` entities for the founders.
5. **Write alt text on all 9 images**; drop `aria-hidden` from the case-study
   images and caption them.
6. **Build owned case-study pages** before linking out. Keep the outbound link,
   put the story on your domain.
7. **Add `llms.txt`** once pages 1–2 exist.

---

## 6. Unknowns

- No prompt set has been run. Whether ChatGPT / AI Overviews / Gemini /
  Perplexity name Visionary Media for any category question is **unmeasured**.
- Competitor set is not defined (Stage 1 scope not signed off).
- Semrush figures below are read off a screenshot, not from a signed-off
  `01-audit/semrush.json`: AI Visibility 0, Mentions 0, Cited Pages 0 across
  ChatGPT / AI Overview / AI Mode / Gemini; Authority Score 2; Ref. Domains 49;
  Backlinks 70; Organic traffic and keywords n/a. Treat as provisional until
  captured with screenshots into the record.
