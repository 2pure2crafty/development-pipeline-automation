# Ideas Backlog -- Pre-Pipeline Archive

**Source:** Imported from staging docs (hds-ideas.md) on 2026-08-20
**Status:** RAW -- none of these ideas have been through the planning agent.

Before any idea here enters the pipeline it must:
1. Be reviewed by the ideas agent (you)
2. Be passed to the planning agent for commercial/strategic validation
3. Be approved by Patch before entering the build queue

Do not treat anything in this file as approved or ready to spec.

---

# HDS Ideas Backlog

Product ideas that need code to implement. Not specced yet — these are directions, not phases. When an idea gets built, move it to BUILD-PROGRESS.md and link the phase.

This file is a context-preservation mechanism. Ideas discussed in past conversations live here so they are never lost to a context window reset. If something was talked about but is not in a build phase yet, it belongs here.

---

## Idea 01 — Lokalbo-kortet: Automated Resident Discount System

User type (Lokalbo/Turist) is built. Discounts are configurable per entity. What is missing is the glue:
- Checkout automatically queries the booker's user type and applies matching discount rules without manual input
- A "Mina rabatter" section in /mina-sidor/ that lists every Lokalbo discount the user is currently eligible for across all entities on the platform
- A public-facing "Lokalbo-erbjudanden" browse page — filterable by category — so residents can discover what discounts exist
- Admin tool to bulk-enrol entities into a municipality-wide Lokalbo campaign with a shared discount percentage and label

---

## Idea 02 — Foreningslyftet: Claiming Sprint Campaign Mode

A structured 6-week push to get associations onto the platform. Needs:
- Campaign object in the DB: name, start date, end date, target entity type, reward (featured duration)
- Admin UI to create a campaign, assign a batch of unclaimed entities to it, and track progress
- Automated email sequence tied to the campaign (invite → day-7 nudge → day-14 nudge → "you made it" confirmation)
- Campaign progress dashboard for the commune coordinator: invited / claimed / still pending, with a visual bar
- On claim completion during an active campaign: auto-set featured badge for the promised duration

---

## Idea 03 — Bokningspool: Public Venue Availability Calendar

The booking system exists for individual entities. What is missing for a communal venue pool:
- A "Lediga lokaler" (available spaces) browse page — shows all entities that have open booking slots in the next 30 days
- Filter by date, capacity, category (meeting room / sports hall / rehearsal space / outdoor)
- Availability shown as a simple calendar grid per venue without requiring login to browse
- "Boka" button triggers the standard booking flow
- Optionally: iCal export of a venue's availability for integration with external calendars

---

## Idea 04 — Evenemangskalendern: Canonical Event Feed

Replace the fragmented multi-channel event landscape with one source of truth:
- Embeddable event widget (iframe or JS snippet) that any external site can drop in — shows upcoming events filtered by category/area/entity
- iCal feed endpoint per entity and per municipality so events sync to Google Calendar, Apple Calendar, Outlook
- Scraped event import: admin pastes a URL (Facebook event page, entity website) and the system extracts date/title/description via Claude API
- "Spara evenemang" button for logged-in users that adds an event to their personal calendar and sends a reminder email 24h before

---

## Idea 05 — Hitta Hem: New Resident Onboarding Sequence

Mechanism to convert new residents at their highest moment of openness:
- Trigger: new account registered with Lokalbo type AND address in the municipality
- Automated 3-email welcome sequence (day 1, day 7, day 30): discover associations → upcoming events this week → "have you joined anything yet?"
- A municipality-configurable welcome page at /valkomnande/ or /ny-i-[commune]/ with curated "start here" content
- API endpoint the municipality can call from their own CRM/moving-in workflow to pre-register a resident and trigger the sequence
- Optional: integration hook so the municipality's moving-in form creates an HDS account automatically

---

## Idea 06 — Sommarkampanjen: Seasonal Campaign Landing Pages

The platform currently has static category pages. Campaigns need dynamic, time-bounded landing pages:
- Campaign page builder in admin: headline, subtitle, featured entities (manually picked or by tag), date range
- Auto-generated shareable URL (e.g. /sommar/ or /vinter/) that resolves to the active campaign for that season
- Campaign pages are indexable and include Open Graph metadata for social sharing
- Entities can opt in to a campaign from their konto — signals to the algorithm to feature them on that page
- After campaign ends: page shows "next season" placeholder with email signup for updates

---

## Idea 07 — Ungdomskortet: Youth Opportunity Board

Associations and municipality services post volunteer roles, youth programs, and apprenticeship slots:
- New entity content type: "Mojlighet" (opportunity) — title, description, age range, time commitment, contact
- Browse page at /for-unga/ with filter by type and area
- School integration: generated shareable pack (PDF + QR code) the municipality sends to schools each term listing all current opportunities
- Optional: youth-facing simplified registration flow that emphasises discovery over account management

---

## Idea 08 — Kulturomraden Itinerary Builder

Turn the cultural area taxonomy into shareable curated trips:
- Itinerary content type: name, cultural area, day-by-day schedule of entity visits, map of the route
- Admin/coordinator builds itineraries by dragging entity cards into a day planner
- Public itinerary page at /rutter/[slug]/ with a map showing the full route, entity cards with opening hours, and a "Spara resa" button
- Shareable link that pre-filters the map to show only entities on the itinerary
- Printable PDF version for offline use / tourist bureau handout

---

## Idea 09 — Foreningsbidrag 2.0: Activity Report Generator

Replace manual grant application forms with platform-generated activity evidence:
- "Generera arsrapport" button in entity konto — produces a PDF or structured export covering a chosen date range
- Report includes: events held (count + attendance), new members, bookings processed, profile views, documents uploaded
- Commune coordinator dashboard view: all associations side-by-side with their key metrics for a given grant period
- Configurable grant criteria in admin: the commune sets which metrics matter and at what thresholds
- Optional: digital submission flow — association generates report, clicks "Skicka till kommunen," coordinator receives and can approve/note in the platform

---

## Idea 10 — Besoksdata: Aggregate Analytics and Gap Dashboard

Currently analytics are per-entity. Municipality needs the aggregate view:
- Platform-wide search query log: what people searched for, which searches returned zero results (the gaps)
- Aggregate heatmap: which areas of the map get the most interaction, overlaid on entity density
- "Saknas pa plattformen" report: categories with high search volume but few or no matching entities — actionable list for the coordinator to fill gaps
- Monthly analytics email to commune coordinator: top searches, most viewed entities, new registrations, events with most saves
- Export: CSV/Excel of all aggregate data for use in destination marketing reports and regional funding applications

---

## Idea 11 — Digitala Informationstavlor: QR-Linked Local Area Dashboards

**The physical-digital bridge.**

Sweden has a network of brown ℹ tourist information signs and community noticeboards along roads and in town centres. People stop at them. They read them. The idea: attach a QR code to each sign that opens a digital version of that information point — a live, location-aware dashboard showing what is happening right now in that local area.

### What the landing page shows
- A map centred on the sign's location with a "Du ar har" (You are here) pin
- Nearby entities within a configurable radius (e.g. 2 km), sorted by distance
- Events happening today and this week in the local area
- Current weather (optional, via open API)
- The cultural area this location sits within (e.g. "Du ar i Norrfjarden")
- Links to relevant category pages (Aktiviteter, Mat, Boende) pre-filtered to the area

### URL structure
Each sign gets a unique URL encoding its location and a human-readable area slug:
`/info/?lat=65.312&lon=21.489&area=norrfjarden&label=Norrfjarden+badplats`

Or a short named alias managed in admin:
`/i/norrfjarden-badplats`

### QR code generation
Admin tool: enter a sign location (click map or enter coordinates), name it, choose radius and entity filters, generate a printable QR code at the right resolution for outdoor signs (weatherproof print spec).

### "You are here" map behaviour
The URL parameters pre-centre and pre-zoom the map. A distinct marker (not the standard entity pin) marks the physical sign location. Nearby entities appear as pins around it. No GPS permission required — location comes from the URL, not the device.

### Offline consideration
Tourists in rural areas may have poor signal. The page should be optimised for slow connections: no heavy assets, entities loaded progressively, map tiles cached where possible.

### Physical integration path
1. Municipality identifies existing sign locations (council already has these mapped for maintenance)
2. Platform admin generates QR codes for each location as a batch
3. Weatherproof QR code stickers produced (standard print spec, cheap)
4. Affixed to existing signs — no new infrastructure required
5. Signs update themselves: as entities open, close, or add events, the dashboard updates automatically

### Why this matters
A tourist standing at the Norrfjarden information sign is at maximum intent — they are physically in the area, they have already stopped, they want to know what is nearby. The existing sign gives them a static map that is 3 years old. A QR code gives them live data. The conversion from "stopped at sign" to "visited a local business" goes up substantially.

---

## Idea 12 — Full Discount System Buildout

The current implementation is a foundation: member discount %, platform courtesy discount %, and a basic `discount_rules` array (type, demographic target, percentage, label). What is not yet built is the logic that makes it genuinely useful at scale.

### Missing pieces

**Stacking and priority rules**
Multiple rules can match a single booking (Lokalbo + member + first booking). No defined behaviour exists for this yet. Needs: a stacking strategy (additive up to a cap? best-match only? explicit priority order?), and a checkout display that lists each applied rule as a named line item.

**Time-bounded discounts**
Happy hour, seasonal rates, launch offers. Needs: optional `valid_from` / `valid_until` date fields on each rule. Checkout ignores rules outside their window. Admin sees expired rules greyed out but not deleted (audit trail).

**Minimum spend / minimum duration thresholds**
Some discounts only apply for bookings of 2+ hours or 500+ kr. Needs: optional `min_spend` and `min_duration_hours` fields. Checkout shows the threshold as an inline note when the booking is below it.

**Promo codes**
Entity owners or platform admin generate single-use or multi-use codes. User enters at checkout step 1; matching rule fires regardless of user type. Needs: `promo_codes` table (code, entity_id, rule_id, max_uses, used_count, expires_at), input field in booking flow, redemption log.

**Group size discounts**
10% off for groups of 8+. Needs: optional `min_group_size` field on rules. Group size is already collected in booking step 1 — just needs to feed into rule-matching.

**Loyalty discounts**
Every 5th booking at this entity is discounted. Needs: booking-count-per-user-per-entity query, and a loyalty rule type in the schema.

**Public profile discount badges**
Discounts are currently invisible until checkout. Entity profiles should optionally show "Lokalborabatt: 15%" and "Medlemspris tillgangligt" as visible chips, so users know before clicking Book. Opt-in per entity.

**Commune-level campaign discounts**
Municipality runs a "Julmarknad" week where all opted-in entities automatically offer 10% off. Needs: a campaign object at commune level that injects a temporary rule into opted-in entities without each entity configuring it manually.

### Data model sketch
```
discount_rules: [
  {
    id: uuid,
    type: 'member' | 'platform' | 'demographic' | 'first_time' | 'loyalty' | 'group' | 'promo' | 'campaign' | 'custom',
    demographic: 'all' | 'lokalbo' | 'turist',
    pct: 15,
    label: 'Lokalrabatt',
    min_spend: null,
    min_duration_hours: null,
    min_group_size: null,
    nth_booking: null,
    valid_from: null,
    valid_until: null,
    promo_code: null,
    max_uses: null,
    used_count: 0,
    priority: 10,
    stack_cap_pct: 30
  }
]
```

### Checkout display target
```
Grundpris:           400 kr
Lokalrabatt (15%):   -60 kr
Medlemspris (10%):   -34 kr
Stackningstak (30%): max applicerat
Att betala:          306 kr
```

---

*Add new ideas below this line. When an idea is built, add a note: "Built in Phase N — [date]" and move the full spec to hdp-build-phases.md.*

## Idea 13 — On-Platform Payments (Stripe Connect + Swish)

*Captured July 2026 from FUTURE-IDEAS.md. Full analysis preserved here.*

### The question
Should HDS take payments on-platform for bookings and route money to individual providers?

### Conclusion
**Yes, via Stripe Connect for verified entities.** Swish stays as a parallel trust-based option (not replaceable by Stripe — Swish is not a Stripe payment method). The two coexist: Stripe for card/Klarna with full confirmation loop; Swish for frictionless local payment without API.

### Why Stripe Connect specifically
Stripe Connect is purpose-built for "platform collects payment, routes to providers." Stripe holds and disburses under its own license — HDS never touches the money and does not become a regulated payment handler under PSD2 / lagen om betaltjänster. Providers onboard via Stripe's hosted KYC flow. HDS optionally takes a small platform fee on transactions.

### The money-handler risk (important)
Receiving money and forwarding it to a third party is a regulated payment service in Sweden (Finansinspektionen). Swish Handel (with API confirmation) would require HDS to act as the central collector and forwarder — making us the regulated entity. Stripe Connect avoids this entirely. This is not a technicality; it is the core reason to use Connect over central Swish.

### Category split (recommended)
- **Accommodation (cabins, rent-your-place):** leave to Airbnb/Booking or facilitate with links + trust-based Swish. Highest consumer-law weight, highest refund risk. Not first payment exposure.
- **Experiences / small bookables (sauna, guided tour, workshops, venue hire):** the right category for on-platform Stripe. Lower amounts, lower refund risk, real platform differentiation.

### Provider gate
F-skatt registration (for businesses) or org-nr (for foreningar). This is how The Great Wagon handles it. Provider owns their tax obligations; HDS stays out of the money-handler role.

### Swish confirmation gap (middle ground, buildable anytime)
Personal/forening Swish has no API — no programmatic confirmation is possible. Pragmatic solution: move confirmation from customer to provider. The forening sees payment in their Swish app and marks the booking "betalning mottagen" in their konto. Reference number (e.g. KIF-2026-001) in the Swish message makes matching instant. Real human confirmation loop, zero dependencies on Swish API.

### What needs to be built
- Stripe Connect onboarding flow for entity owners in konto
- Payment step in booking flow: Stripe card/Klarna for Connect-enrolled entities; Swish trust-based for all others
- Booking status webhook handler (Stripe PAID → booking confirmed automatically)
- Platform fee configuration in admin (per-entity or global %)
- Payout tracking and entity-facing earnings summary in konto
- Provider gate check: only entities with valid org-nr/F-skatt can enrol in Connect

---

## Idea 14 — Reciprocal Member Discounts ("Community Beyond the Communities")

*Captured July 2026. No payments infrastructure needed — purely a pricing rule.*

Full member price at your own forening. A smaller courtesy discount (e.g. 5–10%) if you are a member of ANY forening on the platform.

This gives every association a reason to want other associations on the platform — their members get a small benefit everywhere, which becomes a membership retention argument. Strong network effect incentive.

What needs to be built: a query at checkout that checks if the booker is an active member of any entity on the platform (not just the entity being booked), and applies a "platform membership courtesy" discount rule if so. The discount rate is set globally in admin. This stacks with the existing discount_rules system (Idea 12) at a lower priority than entity-specific rules.

---

## Idea 15 — Super Admin CRM: Commune Sales Pipeline

A lightweight CRM built into the super admin panel (`/admin/`) for tracking where each of Sweden's 290 communes sits in the sales process. Not a full CRM — just enough to answer "who do I contact next and what do I say?"

**The problem it solves:** As the commune list grows, it becomes impossible to remember who was emailed last week, which communes are warm, which went cold after a demo, and which are worth following up this month. The `/admin/region/` dashboard shows live communes, but has no visibility into the pipeline for communes not yet contracted.

**Suggested pipeline stages:**
- `Ej kontaktad` — on the radar but no outreach yet
- `Kontaktad` — email or call made, awaiting response
- `Demo bokad` — meeting/demo scheduled
- `Demo genomförd` — demo done, in evaluation
- `Förhandling` — active negotiation
- `Avtal signerat` — contracted, onboarding in progress
- `Live` — live on platform (auto-set when commune_id exists in `entity_commune`)
- `Avböjt` — declined, reason noted

**What to show:**
- Stats bar at top: total communes tracked, contacted this month, demos booked, live
- A kanban-style list or filterable table with one row per commune
- Each row: commune name, population, county (Län), current stage, last contact date, next action note, contact person name
- Quick inline stage-update (dropdown or drag between columns)
- "Next actions" view: filter to communes with no activity in X days

**Data model (new table `commune_pipeline`):**
```sql
CREATE TABLE commune_pipeline (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  commune_name  VARCHAR(200) NOT NULL,
  kom_code      VARCHAR(10),
  lan_name      VARCHAR(100),
  population    INT,
  stage         ENUM('ej_kontaktad','kontaktad','demo_bokad','demo_genomförd',
                      'förhandling','avtal_signerat','live','avböjt') DEFAULT 'ej_kontaktad',
  contact_name  VARCHAR(200),
  contact_email VARCHAR(200),
  contact_role  VARCHAR(200),
  last_contact  DATE,
  next_action   TEXT,
  notes         TEXT,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Seed data:** Pre-populate with all 290 Swedish communes (name, kom_code, population, Län) from a public register. This gives a complete picture of the addressable market from day one — every row starts at `ej_kontaktad` and the goal is to move them right.

**Integration with the live platform:** Communes that are live on the platform (i.e., have a `commune_id` in `entity_commune`) should auto-highlight or auto-set to `live` stage. The CRM is the sales view; the platform is the operational view. They complement each other.

**Scope when ready to build:** A new tab in `/admin/` ("Pipeline") is the simplest path. No external CRM dependency — everything lives in the HDS database. Super admin only.

---

## Idea 16 — Admin Hierarchy: Splitting the Five Levels

The platform has five distinct admin levels but currently collapses them into two dashboards (`/admin/` for super admin, `/konto/` for everything else). As the platform scales across multiple communes and regions, these need to be separated.

**The five levels, bottom to top:**

1. **Village admin** (`village_admin`) — edits one village's profile page, gallery, history. Scoped to a single `village_id`. Already built in `/konto/`.
2. **Commune admin** (`commune_coordinator`) — manages all entities in one commune, sends invitations, approves submissions. Scoped to a single `commune_id`. Already built in `/konto/`.
3. **Regional admin** — oversees all communes within a Län (county). Sees aggregate stats per commune, identifies weak spots, coordinates field agents across the region. `/admin/region/` exists but currently only Piteå is seeded. Intended role: a person employed or contracted at county/Länsstyrelse level.
4. **National admin** — Sweden-wide view. All regions, all communes, cross-region trends, data licensing oversight, platform health. Not yet separated from super admin.
5. **Super admin** (Patch) — full platform access, billing, account creation, CRM pipeline, configuration. Currently `/admin/`.

**What this idea proposes:**
- Split `/admin/` into a super admin view and a national admin view once a national admin account is needed
- Build out `/admin/region/` to be role-gated (regional admin role gets in, sees only their Län)
- Add a `lan_id` scope to regional admin accounts (similar to how `commune_coordinator` has `entity_id = commune_id`)
- The commune coordinator dashboard in `/konto/` may eventually graduate to `/admin/kommun/` as a full-featured tool

**What drives the timing:** This separation only matters when there is more than one region live and a real person is employed at regional or national level to manage it. Until then, super admin covers all of it. Build when the second region comes online.

**Current dashboard content by level (as of Phase 127):**
- Village admin: village profile editor (Om byn, Historia, Galleri tabs)
- Commune coordinator: entity list, invite management, claim progress, upcoming events, top viewed
- Tourism board: visitor-focused entity list, upcoming events, top profiles
- Rural dev: activation stats, entity queue filtered by invite status
- Field agent: work queue of unclaimed entities with edit links
- Regional admin: per-commune stat cards, activation rates, cross-commune event list
- Super admin: full entity table, submissions, permissions, analytics, billing, account creation, incident management

---

## Idea 17 — Tourist vs. Resident Segmentation Pop-up

Change the initial segmentation pop-up from generic "Are you a tourist, or do you live here?" to "Are you a tourist, or do you live in Sweden?" This enables conditional content filtering: residents see member and club discounts; tourists do not. The segmentation also allows different onboarding and conversion messaging for each cohort.

---

## Idea 18 — Granular User Type Selection in Account Setup

When users create an account, present a more detailed questionnaire to capture nuance beyond the binary tourist/resident split. Options: "I'm a tourist for a short visit", "I'm a tourist for a long visit", "I'm looking to move", "I'm planning to stay temporarily". This finer-grained data allows personalized recommendations, content weighting, and feature prioritization per user type.

---

## Idea 19 — People Also Search For Widget

Add a discovery widget to profile pages (positioned above the footer) showing related searches or content suggestions. Standard SEO and engagement play that helps users explore adjacent interests and increases session depth.

---

## Idea 20 — Partnership Companies Linking

Allow businesses to declare formal working relationships on their profiles (e.g., farmer and supermarket, farmer and restaurant, wedding planner and venue). Creates a graph of cross-business connections visible on profiles. This works across all verticals and sets up infrastructure for Idea 21.

The visibility chain is the real value here. A producer like Lillbäcken (sausages, Lillpite) declares a partnership with ICA Lillpite — visitors to either profile see the connection. A restaurant that sources from Lillbäcken adds it as a partner — now a customer finding the restaurant discovers the farm, and a customer finding the farm discovers which restaurants serve their products. A second restaurant sees the chain and wants in, creating a "fork to farm" trail that benefits everyone in it. Discovery propagates in both directions without anyone having to manage it centrally. The more connections are declared, the more the platform resembles a living map of how the local economy actually works.

---

## Idea 21 — Wedding Vertical

A dedicated vertical for wedding-related services and vendors. Wedding has distinct needs (venues, planners, caterers, florists, photographers, etc.) and high cross-selling potential between service categories. Scope: assess whether this should be a standalone section or a full product tier.

The Partnership Companies infrastructure (Idea 20) makes the wedding vertical interesting for a specific reason: exclusivity dynamics. A wedding planner wants to appear on as many venue profiles as possible — maximum visibility, maximum leads. A venue may want to feature only one or two preferred planners, not a full open list, because exclusivity is a selling point for both parties ("we work exclusively with X"). This creates a competitive dynamic where planners actively court venues to become the featured or exclusive partner. A planner who achieves preferred status at multiple venues has a material advantage, which drives ongoing engagement with the platform and potentially creates a premium tier: pay to be a featured partner on venue profiles. Venues gain something to offer planners; planners gain visibility they will compete to maintain.

---

## Idea 22 — Extended Claiming Lifecycle

**Tags:** `admin-tool` · `go-live`

The current nudge crons stop at Day 14. For a full rollout the unclaimed entity lifecycle needs to run much longer without becoming intrusive. Proposed schedule: weekly reminders for the first month (Days 7, 14, 21, 28), then monthly for months 2-6, then quarterly for entities still unclaimed past the 6-month mark. This matches how small business owners actually behave — the ones who miss the first two nudges are not ignoring the platform, they just have not had a moment. The coordinator dashboard already surfaces unclaimed entities; the extended crons close the loop automatically without coordinator intervention across the full first year.

---

## Idea 23 — Self-Serve Claim Page

**Tags:** `product-feature` · `go-live`

A public-facing page where a business owner can enter their email address and trigger a claim email themselves, without needing a coordinator invite first. Flow: enter business email → system finds matching unclaimed entity → generates claim token → sends standard claim email. Communes share the URL to this page in their social media launch posts: "Click here to claim your free listing." This creates a permanent, shareable entry point for self-driven claiming and removes the coordinator as a bottleneck for late adopters or businesses who missed the initial invite wave. Distinct from the existing `/ansprak/` token flow, which requires a prior invite to exist.

---

## Idea 24 — Commune Handover Media Pack

**Tags:** `admin-tool` · `growth`

A resource pack handed to the commune coordinator during onboarding, giving them everything they need to run their side of the launch without waiting for HDS to prepare materials each time. Contents: pre-written social media post templates with the self-serve claim URL (Idea 23) pre-filled, seasonal content variants (summer push, winter/Christmas push, spring activation), a suggested posting calendar for the first year, and brief notes on what to communicate at each stage. Produced manually per commune initially; longer term it should be auto-generated from the coordinator dashboard with commune-specific URLs and branding filled in. Removes the manual prep step from the HDS onboarding workload and gives commune staff something concrete to act on from day one.

---

## Idea 25 — Careers Vertical (Jobs on the Map)

**Tags:** `product-feature` · `growth`

A map-based job discovery layer integrated into commune portals, aimed primarily at people considering moving to the area but useful for anyone job-hunting locally. Pulls listings from Arbetsförmedlingen's Platsbanken API, geo-locates them using employer addresses, and plots them as a map layer — so a prospective mover can see "here are 40 open positions within 50 km of Piteå" alongside housing, services, and leisure. Remote and hybrid roles are shown separately (listed but not plotted geographically). Where an employer already has an entity profile in HDS, the job listing links back to it, reinforcing the directory. The total number of live job listings can surface as a stat on the commune homepage — a concrete signal of economic activity for anyone evaluating a move.

The wider opportunity is the same data licensing model as the camping and route map: a structured, location-tagged jobs layer covering multiple Swedish communes is a data asset that can be sold to recruitment platforms and job boards. The commune-level framing also gives this a distinct angle that Arbetsförmedlingen's own Platsbanken does not: less "search for a job title" and more "explore what kind of economy this place has."

Relevant context: the gap this fills is visible on pitea.se, where the "looking for a job" page under "Move to Piteå" is a plain list of links to external job sites with no local context, no map, and no connection to the businesses already on the platform. See also Idea 05 (Hitta Hem) and Idea 26 — the careers layer is one component of the broader "move to" vertical.

---

## Idea 26 — "Flytta Hit" Move to [Commune] Vertical

**Tags:** `product-feature` · `growth`

A dedicated journey for people who are actively considering relocating to a commune — distinct from the tourist view and richer than the generic Lokalbo onboarding. The core insight is that someone evaluating a move has a specific set of questions: Is there work here? Can I find housing? What will my daily life look like? What is the community like? The platform already has or can acquire answers to all of these, but they currently live in separate places.

The defining feature is a combined map layer: housing listings and job listings overlaid on the same view. A prospective mover can see "there are 12 houses for sale within 10 km of the town centre and 35 open positions within 20 km" in a single glance. This is not something pitea.se, Hemnet, or Platsbanken currently offers individually — the combination is new.

Housing data source: Hemnet (Sweden's dominant property listing site). Hemnet does not offer a public API — their developer documentation returns a 403 and their GitHub has nothing relevant. Practical options, in order of effort: (1) deep-link to a Hemnet search pre-filtered to the commune's area — no API needed, adds immediate value, and is something pitea.se does not even do currently; (2) integrate Booli (Schibsted property portal, more developer-friendly, has had partner API arrangements); (3) pursue a commercial data agreement with Hemnet directly once HDS has multiple communes and negotiating leverage. Start with option 1.

Jobs data source: Arbetsförmedlingen Platsbanken (see Idea 25).

Additional layers in the vertical:
- Editorial content for prospective movers: cost of living, schools, transport, what the community is like in practice — maintained by the commune coordinator
- Links to föreningar and community groups relevant to integration (sports clubs, cultural associations, etc.)
- User segmentation: moving from abroad vs. moving within Sweden. Foreign movers may need English-language content throughout; Swedish movers less so. The existing user type system (Lokalbo / Turist) does not capture this distinction — a "Ny invånare" (new resident) type may be warranted.
- Language dimension: an incoming international mover is a different user from a Swedish person relocating from Stockholm. The platform already supports English throughout; the vertical makes this more deliberate.

At scale, the "Flytta Hit" vertical is the same framework across every commune — the content changes, the map changes, but the structure is identical. This is a strong differentiator in sales conversations with communes that are actively competing for residents, which in a depopulation context is most rural Swedish communes.

---

## Idea 27 — Children and Young People Vertical

**Tags:** `product-feature` · `growth`

A dedicated section for youth-facing content: sports clubs, youth associations, summer camps, after-school activities, scouting, cultural programmes for young people. Piteå Kommun's website lists "children and young people" as one of its five top-level audience categories, which signals that communes consider this a priority — and it is an area where the current commune website approach (static pages, centrally maintained) fails most visibly, since youth activity schedules change constantly. The HDS model — entities maintaining their own profiles, events self-published, calendar auto-updated — is a better fit for this content type than any static page can be. Connects directly to the föreningar infrastructure already in the platform (sports clubs and youth organisations are föreningar) and to Idea 07 (Ungdomskortet — youth opportunity board), which should be reviewed for overlap before this is built.

---

## Idea 28 — Demo and Sales Video Assets (Koler as the Example)

**Tags:** `commercial` · `growth`

A library of short screen-recording demos using The Old Skoler (Koler, Piteå) as the example entity throughout. The dual purpose is deliberate: the videos demonstrate the platform for sales conversations and prospective commune sign-ups, and simultaneously advertise The Old Skoler to every person who watches them. Every "how do I add a booking discount?" example shows The Old Skoler's profile. Every "how does claiming work?" walkthrough uses a Koler entity. Every FAQ video in the help centre (/hjalp/) is an ad for the village and the business — embedded, permanent, reaching anyone who evaluates the platform. This is not incidental: it is the most efficient advertising available, and it is free.

Suggested demo set: (1) coordinator view — claiming dashboard, sending invites, reading the monthly report; (2) entity owner flow — claiming a profile, adding photos, setting opening hours, configuring a member discount; (3) public visitor view — finding something on the map, booking a space, applying a discount at checkout; (4) the "30 days after launch" view — what the dashboard looks like when claiming is at 40%. Host on /hjalp/ and use in all sales materials.

---

## Idea 29 — Housing Listings Vertical

**Tags:** `product-feature` · `growth`

A property listings layer that allows estate agents to publish their current listings directly on the HDS platform, appearing as pins on the commune map alongside businesses, routes, and services. The goal is not to replace Hemnet — agents keep their Hemnet listing — but to offer what Hemnet does not: rural community context, a free additional channel, and a widget agents can embed on their own website.

**The core pitch to agents:** free to list, zero friction. Agents are already paying Hemnet approximately SEK 9,000 per listing for national exposure. HDS offers a targeted rural audience and a set of tools Hemnet does not provide, at no cost initially. The incentive to upload listings is the agent map widget (below) and the click-through analytics showing how many people came from HDS to their listing — proof of value they can see in a dashboard before any pricing conversation happens.

**What makes this different from Hemnet:**

- Properties shown in context, not isolation. A buyer sees the house on the same map as the nearest sauna, the ICA, the cycling routes, the village association. Hemnet shows a house. HDS shows a place to live.
- Rural focus where Hemnet's traffic is thin. For a cabin in Markbygden or a farmhouse outside Piteå, Hemnet has the listing but almost no targeted audience. HDS is the more relevant channel for buyers actively looking at rural areas.
- The agent portfolio widget. Agents upload their listings to HDS and receive in return an embeddable map widget showing all their current live listings — automatically updated as listings go live or sell. Hemnet gives agents nothing like this; their own websites have individual Google Maps pins per property, not a live portfolio map. This widget is buildable now — the commune widget infrastructure already exists.
- Click analytics. The platform already tracks entity page views. Property listings get the same: how many people viewed the listing on HDS, how many clicked through to the agent's own site or Hemnet listing.

**What needs to be built (not currently in the platform):**

- A listings data model: property type (apartment, house, plot, farm), price, size in sqm, number of rooms, address, photos, status (active/sold). Listings are temporal — they expire when sold, unlike business profiles which are permanent.
- Individual listing pages with the relevant fields displayed.
- Property-specific map filtering: price range, property type, number of rooms, distance radius.
- Agent profile as a listing owner — an estate agent is an entity on the platform; their listings belong to their profile.
- The agent portfolio widget (generates an embeddable map of all their live listings).

**What to skip entirely:** price history statistics, area comparables, mortgage tools, bidding process infrastructure, legal/compliance tooling. That is Hemnet's complexity. HDS is a discovery and distribution layer, not a transaction platform for property sales.

**Monetisation path:** launch free to agents to build supply. Once agents can see their click-through analytics, introduce optional premium placement (featured listing on the commune homepage, boosted pin on the map). Longer term, a subscription per agent gives predictable revenue. The widget could also be a paid feature for agents who want to embed it on their own site. No per-listing fee model — that is Hemnet's approach and it creates friction; the subscription or premium placement model fits the HDS pattern better.

**Hemnet API note:** Hemnet has no public API (confirmed — their developer docs return 403). This vertical is built from listings that agents enter directly into HDS, not scraped or imported from Hemnet. Agents control their own data on HDS independently of their Hemnet listings.

---

## Idea 30 — North Cape 4000 Route Vertical

**Tags:** `product-feature` · `growth`

A dedicated section — initially a set of pages, eventually a subdomain — for the North Cape 4000 (NC4000), the long-distance cycling challenge from southern Europe to Nordkapp in northern Norway. The route passes through Sweden and through Norrbotten, bringing a steady stream of international and domestic cyclists who need accommodation, services, and local information along the way. Patch has NC4000 cyclists staying at The Old Skoler in Koler — this is the anchor use case.

**The current user journey and where it breaks**

This is the actual flow NC4000 cyclists use right now, observed from speaking with guests at The Old Skoler:

1. Cyclist finds the route on the NC4000 main website
2. Loads the route into Komoot — which already has the NC4000 route and shows nearby POIs
3. Uses Komoot to identify places to sleep along the route
4. Leaves Komoot, goes to Booking.com or Airbnb to actually book

The journey fractures at step 4. Komoot handles route + discovery well, but it drops the user at the booking step. The cyclist has to switch platforms, loses the route context, and the accommodation provider has no direct connection to the person who found them on a route map. There is no thread between "I see this place on the route" and "I can engage with it here."

**What HDS adds**

HDS closes the loop. The route is on the map. The entities alongside it are claimed, maintained by the businesses themselves, and have direct booking links or contact points built into their profiles. A cyclist on the HDS route map sees accommodation, clicks through, and either books within the platform or goes directly to the venue's own site — without bouncing to a third-party aggregator that takes the commission and loses the local context.

This is not competing with Komoot. Komoot is a navigation tool — it gets people on the road. HDS is the local discovery and booking layer — it connects people to the places Komoot puts them near. The relationship is complementary, and eventually the right move is a data-sharing arrangement so that HDS entity profiles surface directly inside Komoot as verified, managed POIs.

The entity model is what makes this work. Komoot's POI data is crowdsourced and generic. An HDS entity is claimed by the actual business, has current opening hours, a photo, a booking link, and a direct contact. That difference — managed vs. crowdsourced — is what makes a cyclist choose to book through the route platform rather than going elsewhere.

**The concept**

Map the route's Swedish section (or the Norrbotten corridor specifically) and surface every hotel, guesthouse, hostel, camping spot, bike shop, and service point along or near the route. Accommodation providers sign up for free, get a listing on the route map and a widget they can embed on their own website — the same model as the Housing Listings vertical. The initial outreach to accommodation along the route is direct and targeted: "You're on the NC4000 path. Here is a free tool to get found by the cyclists who will pass your door this summer."

The audience is international. NC4000 riders come from across Europe. English-language content is the default. The route also connects to EuroVelo — the European long-distance cycling network — which has its own community, apps, and planning tools. A partnership or data sharing arrangement with EuroVelo would give the vertical significant reach beyond what HDS can build directly.

**Funding angle:** any tourist board along the route — Norrbotten, Sweden Tourism, Cycle Tourism Norway — has a reason to fund a resource that attracts and serves NC4000 cyclists. The route is a ready-made marketing asset for the entire region. This is a vertical that can be pitched to multiple funders simultaneously because the beneficiaries are geographically distributed.

**Timing:** next year. The cycling season for NC4000 is May–August. A spring 2027 launch gives time to build the route data, contact accommodation providers, and get the page indexed before the 2027 season. Feeds directly into the Cycling vertical infrastructure — any route content built here strengthens the Cycling vertical and vice versa.

---

## Idea 31 — Weekly Lunch Menus

**Tags:** `product-feature` · `growth`

Restaurants on HDS can publish their weekly lunch menu — the same thing they're already doing on matochmat.se — directly from their entity dashboard. Visitors can browse today's (or any day's) lunch options across the commune without leaving the platform. The behaviour already exists in the market; HDS gives restaurants a reason to do it here instead, because the lunch menu is one feature of a richer profile rather than the whole product.

**V1 — Menu data and browse view**

- New `menu_items` table: entity FK, day of week, dish name, price (SEK), dietary tags (vegan, vegetarian, gluten-free, lactose-free), optional description
- Restaurant dashboard UI: add/edit/delete items per day, "copy from last week" shortcut (menus repeat)
- Public "Veckans lunch" browse view: filterable by day, dietary tag, and location — cards showing restaurant name, today's dishes, prices
- Dietary tag badges displayed on entity profile cards

**V2 — Map and date integration**

- When the map is date-filtered (see Idea 33), clicking a restaurant pin shows that day's lunch in the popup card
- "Lunch nearby" as a toggleable map layer
- Embeddable widget: a restaurant can embed their live lunch menu on their own website with one line of code

**The pitch to restaurants:** "You're already maintaining a lunch menu somewhere. Do it here and it appears on your profile, on the commune map, and on a widget you can put on your own website."

**The sharper pitch -- single source of truth:**

The real pain is not that restaurants lack a place to post their menu. It is that they have too many places. A restaurant like Hotell Storforsen currently maintains:
- Their own website (storforsen.se/lunchbuffe/)
- matochmat.se (a third-party lunch aggregator)
- Possibly social media posts, a printed board, internal staff comms

Each one is updated separately. Menus drift apart. Errors appear. It is a data entry tax that falls on whoever handles it -- the chef, the front desk, the owner.

HDS collapses this. Update once on HDS. The embeddable widget feeds the restaurant's own website automatically. No second login, no copy-paste, no inconsistencies. The chef changes a dish -- it appears on the HDS profile, on the commune map, and on their own website simultaneously.

**The aggregator angle:**

matochmat.se and similar aggregators pull data they then display. Right now they require restaurants to enter data directly into their systems. The data licensing play (HDS Milestone 8) inverts this: aggregators pull from the HDS API instead. Restaurants enter data once; every aggregator that wants it pays HDS for a feed rather than taxing the restaurant with another login.

**Chef workflow research (August 2026 observation):**

Before building the UI, understand how menus are actually managed today:
- Who owns the update? (Chef, front desk, owner, admin?)
- What format do they start from? (Word doc, spreadsheet, whiteboard, email chain?)
- How far ahead are menus planned? (Tuesday for next week? Day-of?)
- What would make them update HDS instead of their current system, not in addition to it?

The answer shapes the UI. If they plan weekly in a document, the HDS form should feel like that document. If they update day-of in a rush on mobile, it needs to be three taps. The goal is to replace their current workflow, not add to it.


---

## Idea 32 — Events on the Map

**Tags:** `product-feature` · `growth`

Events currently exist in the calendar but have no map presence. They should appear as pins so a visitor browsing the map can see not just what businesses and places exist, but what is happening and when. The map becomes a view of a place in time, not just a directory.

**V1 — Events as map pins**

Tiered pin placement, in priority order:

1. **Venue entity** — if the event is hosted at a known HDS entity (restaurant, sports hall, community centre), the event pin inherits that entity's coordinates
2. **Point of interest entity** — if the event is at a park, beach, or public space that exists as a POI entity on the map, pin it there
3. **Address fallback** — every event has an address; if neither of the above applies, geocode the address and drop a pin there

Event pins are visually distinct from entity pins (different icon/colour). Clicking an event pin opens an event card: name, date/time, description, organiser entity link, ticket/booking link if applicable.

**V2 — Filtering and clustering**

- Filter events by type (music, sport, market, family, etc.)
- Cluster pins in dense areas — a summer market week with 20 events at the same venue doesn't flood the map
- Toggle events layer on/off independently of entity layer

**Connection to date filter (Idea 33):** the event layer is what makes date filtering most immediately useful. Filter to a Saturday in July and the map shows you exactly what is on.

---

## Idea 33 — Date-Filterable Map

**Tags:** `product-feature` · `growth`

A date picker on the map that adds a time dimension to the spatial view. The core use case: "I'll be in Piteå on Thursday — show me Thursday." Events, lunch menus, opening hours, and eventually booking availability all respond to the selected date. Each stage below is independently buildable.

**V1 — Events and lunch**

- Date picker UI on the map (single date or range)
- When a date is selected: only events on that date appear in the events layer
- When a restaurant pin is clicked: the popup card shows that day's lunch menu if one exists (connects to Idea 31 V2)
- No change to which entity pins are shown — the filter only affects the event layer and popup card content

**V2 — Date range mode**

- Date picker supports a range (e.g., "8–14 August")
- Event layer shows all events within the range
- Entities with any opening hours within the range remain visible; this is useful for "I'm here for a week, what's available?"
- Useful for trip planning — see everything across a stay, not just a single day

**V3 — Opening hours integration**

- Entities whose published opening hours confirm they are closed on the selected date are visually dimmed or hidden (toggle)
- Requires opening hours data to be reasonably complete across entities — this is a data quality dependency, not just a build dependency

**V4 — Booking availability overlay**

- Accommodation and bookable services (saunas, activity slots) show availability within the date range directly on the map
- Green/amber/red availability indicator on the pin before the user even clicks
- Connects to the HDS native booking system; Booking.com affiliate links for entities not on native booking
- This is the version that makes HDS genuinely competitive with a trip-planning platform for rural Sweden

**Note on trip planning:** a "save to my day" / itinerary builder sits naturally on top of this infrastructure. That connects to trip planning work that has been considered previously — it is not a new standalone idea, it is the next logical layer once date filtering and availability are live.

---


---

## Idea 34 — Entity Badge: "Find Us on Hitta Ditt Sverige"

**Tags:** `growth` · `seo` · `phase-2`

Every entity that claims their profile should be able to put a small badge on their own website linking back to their HDS profile. Similar to how businesses display TripAdvisor, Google Reviews, or Facebook badges in their footer or contact page.

**Why this matters -- it is a growth mechanism, not just a feature:**
- Every badge placed on an entity website generates a backlink to hittadittsverige.se
- Backlinks are a primary SEO ranking signal -- 300 local businesses linking to HDS is 300 contextually relevant, geographically targeted backlinks
- Brand visibility: visitors to those business websites see the HDS brand
- Entity buy-in: a business that has put HDS on their own website has made a commitment to the platform
- Social proof for the commune: "our businesses are listed on Hitta Ditt Sverige" becomes visible to residents and visitors

**Implementation:**

V1 -- Static badge
- In the entity konto dashboard, a "Dela din profil" section with a pre-formatted HTML snippet the entity copies and pastes onto their own site
- Two or three badge sizes (small footer badge, medium card, square icon)
- Badge links directly to /foretag/[entity-id]/ with a UTM parameter so HDS analytics can track badge-driven traffic
- Badge is a static image hosted on HDS CDN plus a one-line anchor tag -- no JavaScript required, no security concern for the entity

V2 -- Dynamic badge
- An embeddable widget (one script tag) that shows live data from the entity's HDS profile: star rating if implemented, current opening status, review count
- Updates automatically as the entity's profile is updated -- gives the entity an incentive to keep HDS data current because it reflects live on their own site

**Backlink value:**
Each entity website that displays the badge links back to hittadittsverige.se. For a commune with 200 active entities, this is 200 legitimate local backlinks. These are high-quality links in Google's view: real businesses, real Swedish locations, contextually relevant to the HDS domain. This compounds as more communes are added.

**Connection to Idea 31 (lunch menus):** A restaurant with a lunch menu on HDS has a V2 dynamic badge showing their daily menu on their own website. This is a strong pull for restaurants to maintain their HDS data -- their own website gets live content for free.

---

## Idea 35 — SEO as a Structural Growth Strategy

**Tags:** `growth` · `seo` · `strategic`

The SEO power of HDS is underexplored as a selling point and as a growth mechanism. This idea documents the strategic logic, not a single feature.

**The "Find in Sweden" angle:**
hittadittsverige.se translates directly to "find your Sweden." The domain itself has inherent keyword relevance for anyone searching for something in Sweden -- in Swedish ("hitta," "Sverige") and for English-speaking visitors searching "find in Sweden [thing]." A tourist typing "find in Sweden camping" or "find in Sweden lunch Norrbotten" can land on HDS entity pages.

This is not a paid search play. It is a structural advantage baked into the domain name.

**Long-tail entity page SEO:**
With per-entity SEO (Phase 270 -- individual title and meta description per entity page), each entity page on HDS can rank independently for its own search terms. A specific restaurant page can rank for "lunch Koler," "mat nära Markbygden," "restaurant Piteå landsbygd." These are micro-searches that no single entity could rank for on their own but which collectively make HDS a deep, indexed source for Swedish rural discovery.

As the platform grows to thousands of entities across multiple communes, HDS becomes a large, well-structured directory that search engines index deeply. This is the same mechanism that makes TripAdvisor, AllTrails, and Yelp dominant in search: not from one page, but from millions of entity pages each capturing their own long-tail queries.

**The backlink flywheel:**
- Entity claims profile → gets SEO value from being indexed
- Entity puts badge on own website (Idea 34) → generates backlink to HDS
- HDS domain authority increases → all entity pages rank higher
- Higher ranking pages → more organic visitors to entity profiles
- More organic visitors → entity sees value → maintains profile → data quality improves

This is a self-reinforcing cycle. It does not require paid marketing. It grows as data grows.

**What to do with this:**
- Highlight the SEO value explicitly in the entity onboarding flow: "Your profile will be indexed by Google. Keep it complete to rank higher."
- Add the badge feature (Idea 34) to make the backlink cycle easy to close
- Include the SEO angle in the Piteå pitch: entities get Google visibility they would not get from a commune website listing
- Track domain authority and organic search traffic as a platform health metric alongside entity counts and booking volume


---

## Idea 36 — Snowmobile Trails Vertical

**Tags:** `vertical` · `routes` · `growth` · `safety`

Snowmobile trails are actively used in Norrbotten. Community-maintained maps already exist -- skoterleder.org and OSM-based renders at josm.openstreetmap.de/mapsview -- but the data is stale. Comments on skoterleder.org are 3 years old. Ice conditions in Norrbotten change seasonally. 3-year-old data on a snowmobile trail map is not just unhelpful -- it is potentially dangerous.

**The problem with existing platforms:**
- skoterleder.org: community-contributed, OSM-based, user comments are years old, no clear ownership or update responsibility
- Multiple sites reuse the same OSM data but strip out the community commentary layer
- Service points (fuel, shelter, food) exist as map pins but are not linked to real entities with verified opening hours or contact details
- No date-stamped warnings: a trail marked "skoterled upphör -- återvändsgränd vid vindskyddet" was written 6 months ago. The ice situation today is unknown.

**What HDS offers:**
- Trail data with update timestamps -- visitors know how recently conditions were verified
- Service points linked to real HDS entity profiles: the fuel stop has opening hours, a phone number, and a live status
- Safety warnings as dated posts from the entity or club responsible for that section of trail
- Club-managed routes: a snowmobile club is a förening on HDS; they can own and update their local trail data through their entity dashboard
- Cross-vertical discovery: a visitor already on HDS browsing camping sites or cycling routes finds the snowmobile trails without needing to know skoterleder.org exists

**The club incentive:**
Snowmobile clubs have a direct safety interest in accurate trail data. Their members use this data. Stale information creates liability and reputation risk. A club with an HDS profile and trail management tools has a specific, non-commercial reason to keep their route data current.

**The casual visitor angle:**
Someone on HDS looking for what to do in Piteå in winter discovers the snowmobile trails as part of the broader map -- not because they searched for "skoterled" but because the map showed them the area. This is the multi-vertical discovery advantage.

**Data starting point:**
OSM already contains Swedish snowmobile trail data. This can be imported as a baseline. Local clubs then verify, correct, and extend it through field work -- exactly the field work program funded through Leader Spira Mare. The snowmobile vertical is a direct use case for the field work funding argument.

**Community editing model -- club caretakers:**

The same data that exists in OSM (snowmobile trail polylines) can be imported as a starting layer. The proprietary HDS asset is not the raw geometry -- it is what gets layered on top: field-verified conditions, service point links, safety warnings with timestamps, and club ownership.

Governance model:
- A snowmobile club is a forening entity on HDS
- They are assigned as caretakers of specific trail segments in their geographic area (assigned by the commune coordinator or claimed by the club)
- Club admins can edit and publish changes to their segments directly
- Club members can propose edits; the club admin approves before changes go live
- Any user can flag a hazard (trail closed, dangerous ice) -- this appears as an unverified warning until the caretaker club confirms or corrects it
- Non-caretaker users cannot modify trail data -- they can only flag

This creates: club accountability for data accuracy, a clear trust hierarchy, and a direct incentive for clubs to stay active on HDS because their members' safety depends on the data being current.

**OSM licensing note (important before any data licensing to third parties):**

OSM data is licensed under ODbL (Open Database License), which includes a share-alike provision: derivative databases must also be released under ODbL. In practice, HDS can use OSM trail geometry as a base layer with attribution, and the proprietary asset is the entity data -- service points, safety conditions, club ownership metadata, field-verified additions. The trail polylines stay OSM-attributed. The value HDS licenses to Komoot or others is the verified entity and condition layer, not the raw trail geometry. This distinction needs a legal opinion before any data licensing deals are structured around snowmobile trail data specifically.

**Connection to NC4000:** International cyclists arriving in Norrbotten in May--August and snowmobile riders there November--April are opposite seasons, same geography, same infrastructure. HDS serves both.


---

## Idea 37 — Reception Check-In Interface for Bookings

**Tags:** `product-feature` · `ux` · `restaurants`

When a guest books a lunch buffet (or any timed booking) through HDS and arrives at the venue, reception staff need a way to find the booking and mark the guest as arrived. This is a simple operational interface but it changes the nature of the guest-reception interaction significantly.

**The problem it solves:**

Without a booking system, a guest arrives and the interaction is:
- Guest asks what is on the menu (receptionist states facts)
- Guest decides to stay, pays, receives a ticket or stamp
- Guest goes to the buffet

With HDS booking (without a check-in interface):
- Guest arrives saying they have a booking
- Receptionist has no way to find or confirm it quickly -- creates friction

With HDS booking plus check-in interface:
- Guest arrives: "Hi, I booked under [Name]"
- Receptionist finds the booking in 5 seconds, confirms, marks arrived
- Guest already knows the menu because they saw it when they booked
- The conversation is about anticipation, not information transfer
- Receptionist's role shifts from fact-provider to relationship-builder

**What the interface needs:**

V1 -- Today's booking list
- A "Today" tab in the entity konto dashboard showing all bookings for the current day
- List view: guest name, booking reference, time slot, number of guests, discount status, any notes
- One tap to mark as "Arrived"
- Search by name or booking reference for walk-up confirmation
- Works on tablet or phone (reception desk scenario)

V2 -- Arrival flow
- Optional: guest can show a QR code from their booking confirmation email; receptionist scans to confirm instantly
- Shows the applied discount so there is no ambiguity at the desk about what the guest paid or owes
- Integrates with the existing booking status system (pending / confirmed / arrived / no-show)

**The pitch framing:**

"Your receptionist currently spends time telling guests what is on the lunch menu. With HDS bookings, guests already know before they walk in. The receptionist's job becomes welcoming rather than informing. The interaction is faster and warmer for both sides."

This is a concrete operational improvement that a restaurant manager or hotel front desk manager will recognise immediately from their own experience.

## Idea 38 -- Paid Entity Activation Day

**Tags:** `commercial` · `growth` · `user-research`

A direct, paid service offering to individual entities: Patch spends one day on-site, building out the entity's full HDS profile, taking photos, and running a live user research session on the claiming flow.

**The format:**

~8,000 SEK per day. On-site. What is included:
- On-site photography -- the single biggest barrier to a complete entity profile
- Light consultancy on their existing website (not a rebuild, a review and fixes)
- Full HDS profile built out: categories, description, opening hours, map placement, photos, booking setup if applicable
- Live claiming flow walkthrough: the entity owner goes through the invite email, account creation, and claim steps with Patch watching

**Why this is product research, not just a service:**

The claiming flow is the most critical UX in the platform. When a commune coordinator sends 200 invite emails, most entity owners will go through this alone, on a phone, with no support. Watching one real person go through it from first email open to completed profile is worth more than any automated test.

The right way to run this: send the entity the standard coordinator invite email. Then sit with them from the moment they open it. Note every point of confusion, every hesitation, every moment they look up from the screen. This is QA as it was actually meant to work -- a real person, a real task, real conditions.

**First target: Norrskensgården, Långträsk**

A respondent wrote the most detailed response in the Markbygden community survey, named her business, and called for exactly the collaboration HDS facilitates. She is the natural first candidate. A successful Norrskensgården activation day produces:
1. Revenue (8,000 SEK)
2. A flagship demo entity with real photos and a complete profile
3. Documented user research from the claiming flow
4. A community advocate who has been through the process herself

**Scaling this:**

The one-day activation is not a scalable core business model -- it is an early-stage tool. Its value is threefold: direct revenue, demo-quality flagship entities, and product research that makes the self-serve flow better for the thousands of entities that will never have anyone sitting with them. Once the claiming flow is well-tested and frictionless, the activation day becomes optional rather than remedial.

The paid format also sets a precedent: HDS is a professional service, not a free directory. Entities that pay for onboarding help are more invested in the outcome.

---

## Idea 39 -- Multi-Commune Aggregation Account

**Tags:** `product` · `commercial` · `new-account-type`

A new account type sitting above commune level. Any organisation -- official region, tourism board, development agency, employment office -- can hold one. "Regional account" is just one instance of this type. The account is scoped to a defined list of communes; the per-commune count in that list determines the price.

### Permissions model
- Read everything within scoped communes: yes
- Edit other people's content: no
- Write content that flows downward: yes -- cross-boundary routes (appear in all scoped communes), region-wide notices (flow into each scoped commune's notice board)
- Cannot do: edit content uploaded by communes, entities, or residents
- May need a distinct "regional content" object type separate from commune-owned content

### Ownership ambiguity (needs a flowchart before building)
Who owns uploaded content depends on context:
- POI uploaded by a resident or visitor: they are making an offering to the village. Village owns it after upload. Uploader retains deletion rights only.
- Entity profile uploaded by the entity owner: uploader is the owner. Approval by another role does not transfer ownership.
- Content uploaded by a field agent on behalf of an entity or village: ownership unclear; needs explicit assignment at upload time.
The flowchart needs to cover: who uploaded, in what role, on whose behalf, and whether approval was required.

### Degressive pricing
- First commune in the account: 10,000 SEK/year
- Each subsequent commune: 10% less than the previous, down to a floor of 5,000 SEK/year
- Example: 10k + 9k + 8.1k + 7.3k + 6.6k + 5.9k + 5.3k + 5k (floor) + 5k...
- Also consider: pricing by commune size rather than flat degressive rate, or a combination
- Setup fee is separate
- Minimum commune count: probably 4-5; below that, price higher to reflect overhead

### Setup fee and custom views
- Setup fee covers account creation plus a scoping session to define what the account holder needs
- Output: a custom dashboard configured for their use case -- not a one-size product
- Examples: tourist board wants trail usage by season and entity density; development agency wants employment distribution and operating patterns; social welfare wants geographically scoped survey tools
- The configured view is the selling point: underlying platform is identical but the output is purpose-built
- Natural retention: the configured view has switching cost

### Data permissions and consent
- Communes opt in or opt out of feeding data into a given aggregation account
- Default: opt-in when the region is the buyer of the commune subscriptions; explicit opt-in otherwise
- Consent explanation must state purpose: to help oversight bodies understand economic and social activity, supporting better fund distribution and resource allocation
- GDPR: likely legitimate interest for public bodies; needs legal review

---

## Idea 40 -- Social Welfare, Surveys, and Regional Development

**Tags:** `product` · `commercial` · `verticals`

The aggregation account (Idea 39) becomes substantially more valuable if entity profiles capture more structured data beyond what tourists need. Fields like number of employees, employment type (seasonal/permanent), operating months, and capacity would make the platform useful to regional employment offices, rural investment funds, social welfare departments, and EU/national rural development programmes.

### Survey capability
- HDS knows which users are in which area (commune, village, or entity affiliation)
- Surveys can be targeted geographically and sent to already-authenticated users
- Users log in with their existing HDS account to respond: no new registration friction
- The platform newsletter becomes a legitimate survey distribution channel for aggregation account holders
- The Markbygden survey (external validation exercise) is the template for what a native platform survey looks like
- Social welfare bodies could run periodic census-style checks on rural economic activity without building their own infrastructure
- The combination of existing accounts, geographic awareness, and BankID authentication makes this more credible than a generic survey tool

### BankID and the public-infrastructure angle
BankID is a private company in Sweden but functions as near-public infrastructure: used for bank login, social welfare access, and government services. HDS already uses BankID for login, placing it in the same authentication layer as public services. The long-term direction is for HDS to occupy a similar position: private company, public utility character, embedded in the fabric of rural Swedish life and administration. This framing is worth bearing in mind when positioning to regional bodies and national programmes.
