# BreachSpillover System Architecture

This document provides a technical overview of the BreachSpillover architecture, internal subsystem workflows, data structures, and operational boundaries.

---

## 1. System Overview

BreachSpillover is an open-source, local-first identity intelligence and attack surface analysis platform. It processes identifiers (email addresses, username handles, corporate domains, phone numbers, or hashes) to determine:
1. Historical exposure across corporate breaches and dark web infostealer malware logs.
2. Active online presence across developer ecosystems, social platforms, gaming registries, and corporate filings.
3. Quantified risk of lateral movement and credential spillover based on shared passwords and infrastructure proximity.

All persistent data resides in a local SQLite database running in WAL mode. Zero target data or heuristic profiles are hardcoded.

---

## 2. High-Level Architecture Diagram

```
[ User Input: Email / Handle / Query ]
                   │
                   ▼
       [ FastAPI Router: backend/main.py ]
                   │
       ┌───────────┴──────────────────────────────┐
       │                                          │
       ▼                                          ▼
[ Local Database (WAL) ]              [ OSINT Orchestrator ]
  (data/breach_spillover.db)           (backend/osint_scanner.py)
  - Leaks & Breaches                              │
  - Plaintext & Hashed Passwords                  ├─► Identity Decomposition (email/domain/parts)
  - Physical Footprints                           ├─► Holehe Account Enumeration (120+ APIs)
  - Cross-Target Associations                     ├─► WhatsMyName Engine (700+ signatures)
                                                  ├─► Git Archaeology (Commits, Repos, Authors)
                                                  ├─► Web Dork Recon (Bing, DDG, Yahoo)
                                                  ├─► Corporate Registries (KvK, Drimble)
                                                  ├─► Telecom Intel (E.164, Carrier, Type)
                                                  ├─► DNS-over-HTTPS & CT Logs (crt.sh)
                                                  │
                                                  ▼
                                     [ Hybrid Waterfall Engine ]
                                     (LinkedIn / Web Profiles)
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         │                                                 │
                         ▼                                                 ▼
               [ Tier 1: Proxy Gateway ]                     [ Tier 2: Local Browser ]
               (Scrape.do / ScraperAPI /                     (Playwright Headless Runner,
                ScrapingBee / ZenRows)                        Isolated Profile Session)
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                                 [ Identity Corroboration Gate ]
                                 (backend/linkedin_recon.py)
                                  - Surnames / Token Validation
                                  - Rejects Stranger Collisions
                                                  │
                                                  ▼
                                    [ AI Correlator & Segregator ]
                                    (backend/ai_correlator.py)
                                     - Verified vs Quarantined
                                     - Single Given-Name Guard
                                                  │
                                                  ▼
                                     [ SQLite Pipeline Ingestion ]
                                     (Pivots, Employees, Geo, Bio)
                                                  │
       ┌──────────────────────────────────────────┴────────────────────────┐
       │                                                                   │
       ▼                                                                   ▼
[ Spillover Scoring Engine ]                             [ Interactive Graph Builder ]
(backend/scoring.py)                                     (backend/graph_builder.py)
 - Credential Risk Weights                                - Vis.js Network Topology
 - Lateral Blast Radius                                   - Concentric Orbit Layout
 - Compliance Multipliers                                 - Multi-Hop In-Place Expansion
       │                                                                   │
       └──────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
                     [ Frontend Single-Page App ]
                     (frontend/static/js/app.v18.js)
```

---

## 3. Subsystem Breakdown

### 3.1. Routing and Identity Decomposition (`main.py`, `database.py`)
- Entry Points: `GET /api/search` and `GET /api/scan`.
- Query Decomposition: Incoming queries are analyzed to distinguish between email addresses, single-word handles, composite queries (e.g., `Name <email>`), phone numbers, and domain names.
- Identity Anchor Initialization: Known user anchors (`known_name`, `known_username`, `known_city`, `known_phone`) are bound to the execution context. If unseeded, name tokens are derived from the email localpart using rule-based parsing.

### 3.2. Multi-Source OSINT Pipeline (`osint_scanner.py`, `live_osint.py`)
- Holehe Module: Submits non-destructive registration and password-reset queries to cloud services (Office365, Spotify, Snapchat, Duolingo, LastPass) to establish verified account presence.
- WhatsMyName (WMN) Engine: Executes asynchronous probes across 700+ web platforms using regex response matching and status code verification.
- Git Archaeology:
  - Discovers author accounts matching email prefixes or handles.
  - Scrapes public commit logs (`author_name`, `author_email`, `timestamp`).
  - Fetches repository documents (`README.md`, `cv.html`, `index.html`, `about.html`) for personal portfolio data.
- OpenPGP Keyservers: Queries HKP servers (`keyserver.ubuntu.com`, `keys.openpgp.org`) via HTTP to retrieve public keys, expiration dates, and sub-identities.

### 3.3. Web Dorking & Snippet Disambiguation (`web_dork_recon.py`)
- Queries search engines (Bing, DuckDuckGo, Yahoo) without paid API requirements using randomized mobile and desktop user agents.
- Bing Redirect Handling: Unescapes `&amp;` parameters in `bing.com/ck/a` links and decodes base64-encoded `u_param` values to resolve target URLs.
- Snippet Disambiguation:
  - If Groq/Gemini API keys are present: Dispatches compact JSON prompts to LLM endpoints to extract verified workplace, role, and physical city from organic search snippets.
  - Fallback Mode: Deterministic regex heuristics that verify co-occurrence of both first and last name tokens before extracting corporate employers or cities.

### 3.4. Hybrid Waterfall LinkedIn Extraction Engine
Designed to scrape target LinkedIn profiles while avoiding bot detection, authwalls, and session degradation.
- Tier 1: External Proxy Gateway (`unblocker_client.py`)
  - Dispatches direct HTTP requests using `curl_cffi` with Chrome 124 TLS impersonation.
  - If blocked (HTTP 999, 403, or authwall), routes requests through configured unblocker proxy APIs (Scrape.do, ScraperAPI, ScrapingBee, or ZenRows).
- Tier 2: Local Headless Browser Runner (`browser_runner.py`)
  - If Tier 1 is unconfigured or fails (or if the profile is behind a Members-Only privacy wall), execution waterfalls to a local Playwright headless Chromium runner.
  - Persistent Session Storage: Context runs with state stored in `data/browser_session/storage_state.json`.
  - DOM Extraction: Extracts authentic full names, headlines, employer names, locations, and experience lists.
  - Avatar Safety Isolation: Selects images strictly from top-card profile containers (`.pv-top-card-profile-picture__image`, `pv-top-card__photo`) while explicitly excluding global navigation headers, banners, and investigator avatars.

### 3.5. Vanity Slug Generation & Identity Corroboration Gate (`linkedin_recon.py`)
- Candidate Slug Derivation (`derive_linkedin_candidate_slugs`):
  1. Standard LinkedIn vanity permutations: `first-last`, `firstlast`, `first_last`.
  2. Full email localparts containing name tokens (e.g., `jordinzwaan2016`, `alje.woltjer`).
  3. Initial + surname permutations: `f"{first[0]}{last}"`, `f"{first[0]}-{last}"`.
  4. Numbered variants: `f"{first}-{last}-1"`, `f"{first}-{last}-nl"`.
  5. Bare first-name vanity is appended only as a last resort when a surname is known; it is prioritized only if no surname exists.
- Multi-Token Identity Corroboration (`is_linkedin_identity_match`):
  - When candidate profiles return HTTP 200, the scraped `full_name` is compared against the target's first name and surname.
  - If the target has a distinct surname (e.g., "Zwaan") and the scraped profile does not contain that surname (e.g., "Jordin Sasha Danaram" at Caltech), the profile is rejected as an entity collision.
  - Candidate URLs are iterated (up to 5 candidates) until an authentic corroborated profile is found or all candidates are exhausted.

### 3.6. AI Multi-Token Resolution & Lead Quarantine (`ai_correlator.py`)
- Problem Addressed: Broad handle scans often return false positives (e.g., common first names like `@jordin` registered on GitHub or GitLab 15 years ago by unrelated early adopters).
- Segregation Logic:
  - VERIFIED (`PUBLIC_PROFILE`): Accounts bound by email registration, author commit signatures, or multi-token full name match.
  - SUSPECTED (`SUSPECTED_ACCOUNT`): Uncorroborated single given-name or single surname handles are quarantined in the suspected analyst drawer with confidence scores and reasoning notes. Leads are preserved without contaminating verified executive dossiers.
  - REJECTED: Obvious name discordances and conflicting entities are pruned.
- Offline Fallback: If external AI APIs are unreachable, an internal heuristic checks for multi-token name matches and enforces single-name handle collision guards.

### 3.7. Telecom Intelligence & Dummy Filtering (`telecom_recon.py`, `live_osint.py`)
- Parses raw phone numbers using `libphonenumber`.
- Extracts international formatting (E.164), carrier names, line types (mobile, landline, VOIP), and geographic regions.
- Documentation Filter: Discards fictional North American 555-exchange numbers (`+1-xxx-555-xxxx`) and sequential test numbers (`12345678`) found in repository README files or third-party collaborator documents.

### 3.8. Spillover Risk Scoring Algorithm (`scoring.py`)
Calculates an aggregate risk score (0 to 100) based on forensic attributes:
1. Credential Reuse Weight: Plaintext passwords reused across external services contribute up to 35 points.
2. Breach Recency & Volume: Darknet dumps, infostealer malware exposures, and paste appearances contribute up to 30 points.
3. Infrastructure & Identity Exposure: Discovered personal emails, phone numbers, PGP keys, and residential addresses contribute up to 20 points.
4. Corporate Target Multiplier: Targets with corporate email domains undergo elevated scrutiny (1.2x weight on unhashed credentials and executive VIP roles).

### 3.9. Attack Surface Graph Engine (`graph_builder.py`)
- Transforms relational records into a Vis.js network graph.
- Node Categories: Target Identity, Leaks, Credentials, Public Profiles, Telecom, Physical Footprints, and Relatives.
- Concentric Orbit Layout: Places the target identity at orbit 0, direct credentials at orbit 1, breach events at orbit 2, and external pivots at orbit 3.
- In-Place Dynamic Pivot Expansion: Clicking any node triggers `POST /api/graph/pivot-expand`, dynamically inserting connected relational records without reloading the page.

---

## 4. Database Schema Overview (`data/breach_spillover.db`)

The SQLite database operates with Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and enforced foreign keys (`PRAGMA foreign_keys = ON;`).

```
employees
├── id (INTEGER PRIMARY KEY)
├── full_name (TEXT)
├── corporate_email (TEXT UNIQUE)
├── job_title (TEXT)
├── department (TEXT)          # Supports dual workplaces: "Company A • Company B"
├── vip_level (TEXT)
├── avatar_seed (TEXT)
└── created_at (DATETIME)

leaks
├── id (INTEGER PRIMARY KEY)
├── leak_name (TEXT)
├── breach_date (DATE)
├── leak_type (TEXT)          # Darknet Dump, Infostealer, Paste, etc.
├── severity (TEXT)           # CRITICAL, HIGH, MEDIUM, LOW
├── records_count (INTEGER)
├── exposed_data (TEXT)
├── description (TEXT)
└── threat_actor_source (TEXT)

credentials
├── id (INTEGER PRIMARY KEY)
├── employee_id (INTEGER FK -> employees.id)
├── leak_id (INTEGER FK -> leaks.id)
├── username_used (TEXT)
├── plaintext_password (TEXT)
├── password_hash (TEXT)
├── hash_type (TEXT)          # bcrypt, sha256, md5, etc.
└── is_reused (BOOLEAN)

pivots
├── id (INTEGER PRIMARY KEY)
├── employee_id (INTEGER FK -> employees.id)
├── source_leak_id (INTEGER FK -> leaks.id, NULLABLE)
├── pivot_type (TEXT)         # PUBLIC_PROFILE, SUSPECTED_ACCOUNT, WORKPLACE,
                              # PHONE_NUMBER, AVATAR_CORRELATION, FULL_NAME
├── pivot_value (TEXT)
├── confidence_score (REAL)
└── context_note (TEXT)

physical_footprints
├── id (INTEGER PRIMARY KEY)
├── employee_id (INTEGER FK -> employees.id)
├── source_leak_id (INTEGER FK -> leaks.id, NULLABLE)
├── address_line (TEXT)
├── city (TEXT)
├── postal_code (TEXT)
├── country (TEXT)
├── latitude (REAL)
├── longitude (REAL)
└── exposure_type (TEXT)

relatives
├── id (INTEGER PRIMARY KEY)
├── employee_id (INTEGER FK -> employees.id)
├── relative_name (TEXT)
├── relationship (TEXT)
├── contact_email (TEXT)
├── contact_phone (TEXT)
└── social_engineering_risk (TEXT)
```

---

## 5. Frontend Architecture (`app.v18.js`)

- Controller Model: Single-page application without runtime compilation frameworks. Uses vanilla JavaScript with scoped state management via `let currentInvestigationData`.
- Graph Component: Vis.js Network instance bound to `<div id="vis-network"></div>` with physics stabilizing configuration and custom SVG node renderers.
- Map Component: Leaflet.js tile layer synchronized with UI theme switches (CartoDB DarkMatter for dark theme, CartoDB Positron for light theme).
- Sound System: Audio cues (`click`, `search`, `error`, `export`) throttled via Web Audio API with a global mute state stored in `localStorage`.
- Dual Reporting Modes:
  1. Full Forensic Dossier: Contains complete forensic data including credential hashes and addresses for internal security audits.
  2. Defensive Exposure Report: An allowlisted export (JSON or Markdown) that strips sensitive passwords, physical addresses, and relatives, designed for external remediation guidance.

---

## 6. Operational Principles

1. Zero Hardcoded Data: No target profiles, mock emails, or heuristic shortcuts are hardcoded in the codebase. All records are resolved dynamically through database lookups or live reconnaissance probes.
2. Data Integrity: Profiles returned by external scrapers must pass identity corroboration gates before ingestion to eliminate stranger collisions.
3. Investigator Safety: Headless browser contexts are run in isolated data directories (`data/browser_session/`) to prevent session pollution with investigators' personal browsing accounts.
4. Non-Destructive Ingestion: Uncorroborated leads are preserved under `SUSPECTED_ACCOUNT` in the analyst drawer rather than permanently discarded.
