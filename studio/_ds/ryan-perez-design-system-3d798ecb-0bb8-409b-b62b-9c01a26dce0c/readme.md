# Ryan Perez Design System (LAKA)

Design system for **Ryan Perez — Cognitive Architect & Innovation Strategist** (ryanperez.ca), founder of Bow Tie Kreative (Calgary, est. 2013). Ryan is a neurodivergent keynote speaker — autistic, ADHD, dyslexic, diagnosed at 41 — who built the Second Brain, a 240,720-node AI-powered knowledge system. Positioning: *"I build bridges between the systems we create and the humans they forget."*

Inside Bow Tie Kreative the system is operated under the name **LAKA**, governed by an MCP authority (`mcp/` in the source repo) that serves tokens, rules and validation gates to build agents.

**Products/surfaces represented:** the speaker/marketing website (home, speaking, services, media, contact), plus decks, media kit, proposals, social compositions and email/course content that reuse the same voice and visual system.

## Sources
- GitHub: **https://github.com/bowtiekreative/laka** — the LAKA library. Ground truth for this project: the bound design-system snapshot in `_ds/ryan-perez-design-system-18123911-11c5-413b-9ecf-ed45f6d994c7/` (tokens, compiled component bundle, manifest, readme), the real `brand/` and `icons/` assets, and 26 root-level `*.dc.html` "System" documents (SEO System, Icon System, Form Elements, UI Components, Messaging System, Proposal System, Social Composition System, Funnel System, Analytics Layer, Accessibility System, Deck and Ebook Layouts, Map System, and more).
- Related repos worth exploring for copy and product context: **https://github.com/bowtiekreative/ryanperez-speaker** (all bios, decks, business model, career timeline), **https://github.com/bowtiekreative/ryanperezdesignsystem**, **https://github.com/bowtiekreative/bowtiekreative-site**, **https://github.com/bowtiekreative/hustlezoneyeg** (both are live Astro reskins of this system).
- You are not assumed to have access to these; if you do, read them — the `.dc.html` systems in `laka` carry far more rule detail than can be summarised here.

## The one-sentence system
A dark, almost-monochrome canvas with one blue accent, one typeface, huge tight headlines, generous empty space, and everything fading into view on scroll. Everything else is a variation on those five moves. The "design" is ~113 tokens in `tokens/`; pages are those rules applied.

## CONTENT FUNDAMENTALS
- **Voice:** first person for Ryan ("I build bridges…"), third person in bios; direct address ("you") when speaking to the booker/audience.
- **Tone:** declarative, rhythmic, unsentimental. Short sentences used as hammer blows: "Not a metaphor." / "Not inspiration. Infrastructure." / "Raw. Funny. Devastating."
- **Signature construction:** negation-then-reframe. "Not a resilience talk. A build manual." "He fights systems, not people."
- **Numbers are the proof.** Copy leans on exact figures — 240,720 nodes, 17,336 connections, 96M impressions, $430K. Never round them off; precision is the brand.
- **Transformation arrows:** literal "→" in copy (Invisible→Visible, Pain→Projects, Margin→Center).
- **Casing:** sentence case for headings and body; ALL-CAPS reserved for micro-labels/eyebrows ("STEP 01", "LEARN MORE"). Trademark ™ on Friction Audit™.
- **Emoji:** used in source *documents* as list markers but NOT part of the visual system — never use emoji in designed UI.
- **Vibe:** studio/tech/premium, lived-experience credibility. Infrastructure, not inspiration.

## VISUAL FOUNDATIONS
- **Color — 95% neutral, 5% accent.** Canvas `#07090D` (near-black, blue-shifted), surface `#1A1D24`, raised `#23262F`, headings `#F5F7FA`, body `#C5C7CE`, muted `#8A8D96`, accent `#3F6EE9`. Blue appears on the CTA, one stat badge, link hovers — ~2% of pixels. Nothing pure black or pure white; everything nudged toward blue.
- **Type — one font, two weights.** Inter 400/600 only. H1 80px / −0.05em / 1.02; H2 56 / −0.04; H3 32 / −0.02; H4 22 / −0.01; body 16/1.7 (18px lead); micro-labels 12px uppercase +0.12em. The huge-tight vs tiny-wide tension is the whole typographic idea.
- **Layout.** 1200px container, 12 columns, 32px gutters, 128px between sections. Columns are used asymmetrically on purpose (hero 9 + proof 3; sections offset by 3, leaving a column empty). Emptiness is composed, not leftover. One strong left rail; nothing centered.
- **Depth from light, not shadows.** There are no drop shadows anywhere. Separation comes from backlight (a 7%-white radial bleeding from a section edge), hairlines (8% and 15% white), and frosted glass (header at 80% canvas + 16px blur).
- **Borders:** 1px hairlines only. `--hairline-soft` (8%) at rest, `--hairline` (15%) on hover/emphasis. In light mode they flip to dark ink at 8/16%.
- **Radius language:** **buttons are fully pill-shaped** (`--radius-btn: 999px`) — Button, IconButton, the white CTA button and pricing buttons all round completely; the icon plate in IconFeature follows and reads as a circle. Everything else keeps its size-matched curve: 8 (inputs) / 16 (cards) / 24 (panels) / 32–48 (media blocks). Rule rows and checklists use the card radius, and chips/glyph plates use `--radius-chip` (8px), so the pill token cannot leak into anything that is not a button. Small things small curves, big things big — buttons are the deliberate exception.
- **Cards** are one surface tone above the canvas, 16px radius, soft hairline that firms up on hover, no shadow, no coloured left border, no gradient.
- **Motion.** Everything fades up on entry (`--ease-out: cubic-bezier(0.16,1,0.3,1)`, 600ms, 24px rise); lists stagger 90ms; headlines reveal line by line; numbers count up; imagery drifts. Respects `prefers-reduced-motion`.
- **Hover:** links shift to accent blue; buttons lighten to `--rp-accent-hover`; cards lift hairline opacity — never gain shadows or scale. **Press:** darken to `--rp-accent-press`. No bounce, ever; nothing snaps.
- **Transparency & blur:** reserved for two jobs — the fixed frosted header, and full-screen overlays (menu, lightbox). Never decorative.
- **Imagery.** Film stills, not stock — mid-gesture, not posing; cool-toned and dark-friendly. One grade over every photo (`--grade-filter`: saturate 0.85 / contrast 0.92, cool shadow tint, 6% grain) — the grade is the brand. Heroes are cinema ratios (3:1, 2:1), never photo ratios, and crop subjects past recognizability so the photo becomes texture. No illustrations, no patterns, no gradient washes besides the white backlights and the accent `--wash-corner`.
- **Protection, not capsules.** Type over imagery is protected by gradient floods (`--flood-canvas`, `--flood-accent`, `--protect-bottom`), never by a solid capsule behind the text.
- **CINEMATIC MOTION.** The site behaves like film: media scaled ~108% drifts inside a locked `overflow:hidden` frame (the dolly); layers travel at 0.9/0.95/1.05/1.1 (multiplane parallax); reveals sequence like a shot list (100→150→200→250ms); everything that enters also exits; video is B-roll (`playsinline muted loop autoplay`, no controls — a play button breaks the spell); the blue full-bleed CTA is a cut, one saturated scene change per page, exactly where conversion happens.
- **Signature move — the masked notch.** Media blocks get a corner bitten out (bottom-right), with the blue arrow button sitting in the notch with inverted rounded corners. The system's fingerprint; see `components/surfaces/NotchMedia.jsx`.
- **Backgrounds:** flat canvas everywhere; max one surface tone above it. No section colour changes.
- **Dark is the default and stays the default.** The canvas, hairline and backlight system is authored for dark; light mode is a supported inversion, not a co-equal theme. Every component reads its colours through the semantic aliases (`--bg-page`, `--surface-card`, `--text-heading`, `--hairline`), so both modes come for free — never hard-code a hex in a component. Over-image scrims (`--protect-bottom`, `--wash-corner`, `--tint-accent`) intentionally stay dark in both modes, because they sit on photography, not on the page. The `icons/ui` set is dark-ink SVG: it inverts onto the dark canvas and is used as-is in light mode; `icons/outline` and `icons/glyph` want a paper plate on dark (see the Imported Icon Sets card).
- **Lists never use bullets.** `List` offers four markers — accent arrow (default, matching the copy's literal →), zero-padded accent number, hairline divider, or bare. A `<ul>` with disc bullets is out of system.
- **Light mode.** Set `data-theme="light"` on `<html>`/`<body>`, or wrap a section in `.rp-light`. Cool paper canvas `#EDEFF4`, white cards, dark ink `#10131A`, hairlines flip dark, accent stays `#3F6EE9` (hover darkens instead of lightening), grain drops to 4%. Dark remains the default.

## ICONOGRAPHY
- **Three real icon sets ship in `icons/`, copied from the source repo — use them, never hand-draw.**
  - `icons/ui/` (25) — a 24px UI set at ~1.5px stroke, square caps: search, close, check, plus, minus, mail, phone, globe, location, calendar, clock, folder, document, clipboard, download, settings, shield, target, user, warning, information, analytics, chart, puzzle, dot. This is the set for interface chrome.
  - `icons/outline/` (33 copied of 45) — larger illustrative outline glyphs for services and collateral (banner, billboard, business-card, certificate, letterhead, poster, flyer, packaging, notebook, office, accountant, coaching, learning, meeting, agenda, directions, id-card, bar-chart, pie-chart, graph, growth, guideline, idea, presentation, research, rocket, strategy, success, connections, branding-strategy, branding-web, book, analysis).
  - `icons/glyph/` (17) — the filled/duotone counterpart of the same vocabulary, for feature tiles and decks.
- **Arrows are the primary icon.** Unicode `→` and `↗` carry navigation, transformation and the notch button — matching the copy's literal use of →. Do not replace them with an SVG.
- **No icon font and no sprite exists.** No CDN icon library (Lucide/Heroicons) is used, and none should be introduced — the sets above are the brand's own.
- **Emoji:** never in UI.
- **Logo:** no Ryan Perez logo or mark exists in any source. Render "Ryan Perez" as plain type (Inter 600, −0.05em) wherever a mark would go. `brand/` holds the **Bow Tie Kreative** seals/shields and favicons — the parent studio's marks, not Ryan's — plus PWA icons (`icon-192`, `icon-512`, `maskable-512`, `apple-touch-icon-180`).

## Fonts
Inter is loaded from Google Fonts in `tokens/typography.css` (weights 400 and 600 only). **No font binaries were supplied** — if the brand licenses font files, drop them in and replace the `@import` with `@font-face` rules. This is a flagged substitution: Inter is the typeface the source specifies, but it is being served from a CDN rather than self-hosted.

## Index
- `styles.css` — global entry; `@import`s everything under `tokens/`.
- `tokens/` — `colors.css`, `semantic.css`, `typography.css`, `spacing.css`, `motion.css`, `textures.css` (includes the `[data-theme="light"]` scope).
- `guidelines/` — 25 specimen cards shown in the Design System tab, grouped Colors / Type / Spacing / Brand (including **Dark & Light**, the side-by-side theme comparison).
- `brand/` — Bow Tie Kreative seals, shields, favicons, PWA icons.
- `icons/ui`, `icons/outline`, `icons/glyph` — the three native icon sets.
- `github.md` — source-repo association and screen map. `SKILL.md` — portable agent skill.

### Components
| Family | Components |
| --- | --- |
| `components/core/` | **Button**, **IconButton**, **Eyebrow**, **Badge**, **Tag**, **Stat** |
| `components/forms/` | **Input**, **Textarea** |
| `components/surfaces/` | **Card**, **NotchMedia**, **Testimonial** |
| `components/icons/` | **Icon** (+ `ICON_NAMES`), **IconFeature** |
| `components/seo/` | **RuleList**, **StageFlow**, **DialTable**, **EscalationList**, **SignalStrength**, **RequirementList** |
| `components/cta/` | **CTABand**, **CTAPanel**, **CTABanner** |
| `components/sections/` | **FeatureBillboard**, **FeatureSplit**, **FeatureList**, **FeatureSteps**, **FeatureStats**, **Beacon**, **GlowHeading** |
| `components/accordions/` | **Accordion** (faq / index), **FAQSplit** |
| `components/tabs/` | **Tabs** (underline / pill / micro) |
| `components/commerce/` | **PricingGrid**, **ProductCard**, **List** (arrow / numbered / divided / bare) |
| `components/testimonials/` | **TestimonialCard**, **QuoteBillboard**, **ProcessRail** |
| `components/cinema/` | **CineBanner**, **Shelf**, **PosterCard** |
| `components/bento/` | **Bento**, **BentoCard**, **GlowStat** |
| `components/media/` | **BlogCard**, **Prose** + **P**, **ProseHeading**, **ProseQuote**, **ProseImage**, **Dropcap** |
| `components/galleries/` | **GalleryGrid** |

Starting points: **Button**, **Card**, **NotchMedia**.

#### The SEO / governance family
LAKA's `SEO System.dc.html` is a governance document, not a screen library: it states an object model, a six-stage pipeline, twenty dials, ten escalation levels, ranked signals and required/blocking checklists. Ported here are the six presentation primitives that document is built from — they are the shapes any LAKA rule system (SEO, Accessibility, Analytics, Banners and Disclosure) uses to state a rule. Two conventions travel with them: **colour is the verdict** (accent = do this, red = blocks, green = the fix, amber = risky), and **the count is always named in the heading** ("Eight things, all required"). The status colours they need now live in `tokens/semantic.css` — `--rp-good` #3FA46A, `--rp-warn` #C98A2E, `--rp-bad` #D8574F — extracted verbatim from the SEO system's logic.

### Not yet ported (source inventory remaining)
The source system defines 63 components; the 46 bundle components above are ported verbatim from the compiled bundle, plus the 6 SEO primitives extracted from `SEO System.dc.html`. Still to build, in the source's own grouping: `accordions/` (AccordionShowcase), `cinema/` (Carousel, CenteredHero, CinematicSlider, GradientHero, OfferTile, VideoTestimonial), `galleries/` (Filmstrip), `lightbox/` (Lightbox, VideoLightbox), `media/` (ArticleHeader, PodcastPanel), `navigation/` (MegaMenu, OverlayMenu), `sections/` (MeetSplit), `testimonials/` (AvatarQuote, QuoteColumns). Also unported: the remaining LAKA `.dc.html` systems in the source repo root — Analytics Layer, Accessibility System, Banners and Disclosure, Form Elements, Funnel System, Icon System, Messaging System, Proposal System, Social Composition System, Deck and Ebook Layouts, Infographics and Galleries, List System, Map System, Website Sections, and the `ui_kits/website` ryanperez.ca recreation.

## Intentional additions
- `Tag` (`components/core/`) — **not in the source system.** I verified this against the compiled bundle: there is no `Tag` export and no `function Tag`; the only match is `const Tag = href ? 'a' : 'button'`, a local variable inside `Button`. Tag was authored here for topic/keyword rows on articles and talk pages, and is deliberately given the 8px chip radius so it never reads as a pill Badge. An earlier draft of this readme wrongly described it as a port — it is an addition.
- `components/seo/` — the SEO system exists upstream as a single `.dc.html` document, not as components. The six primitives here are its repeated presentation shapes, factored out so consuming projects can state rules in the brand's own form. Names are new; values, colours and copy conventions are the document's.
- `tokens/semantic.css` — the status colours were inline literals in the SEO system's logic; promoted to tokens so every rule surface agrees.
