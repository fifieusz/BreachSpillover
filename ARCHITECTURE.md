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
       ┌───────────┴──────────────────────────────────────────┐
       │                                                      │
       ▼                                                      ▼
[ Local Database (WAL) ]                         [ OSINT Orchestrator ]
  (data/breach_spillover.db)                      (backend/osint_scanner.py)
  - Leaks & Breaches                                          │
  - Plaintext & Hashed Passwords             Stage 1: Multi-Stream Reconnaissance
  - Physical Footprints                      [ ThreadPoolExecutor (max_workers=4) ]
  - Cross-Target Associations                ├─► Deep Live OSINT (Holehe, Git, PGP) [TTL: 300s]
                                             ├─► AI Web Dork Recon (Bing, DDG, Yahoo) [TTL: 300s]
                                             ├─► Global Corporate Registries (US SEC, UK Companies House, EU/KvK) [TTL: 300s]
                                             └─► Universal Footprint & Personas (YouTube, Bluesky, Portfolios, Platforms) [TTL: 300s]
                                                              │
                                                              ▼
                                             Stage 2-4: Multi-Source Synthesis
                                             - Entity Resolution & KvK Legal Arbiter
                                             - Personal Site Extraction (og:image, metadata)
                                             - Search Snippet Disambiguation
                                                              │
                                                              ▼
                                             Stage 5: Concurrent Post-Recon Engine
                                             [ ThreadPoolExecutor (max_workers=2) ]
                                             ├─► WhatsMyName Engine (700+ signatures) [TTL: 300s]
                                             └─► Multimodal Avatar Harvesting [TTL: 300s]
                                                              │
                                                              ▼
                                             Stage 6: AI Cardinal & Lead Quarantine
                                             - Corroborated Full Name Validation
                                             - Single Given-Name Collisions Quarantined
                                                              │
                                                              ▼
                                             Stage 7: Concurrent Authenticated Browser Runner
                                             [ ThreadPoolExecutor (max_workers=2) ]
                                             ├─► LinkedIn Playwright Headless Context [TTL: 300s]
                                             └─► Facebook Playwright Headless Context [TTL: 300s]
                                                              │
                                                              ▼
                                             Stage 8: Main Thread SQLite Ingestion
                                             - Atomic database writes to WAL DB
                                             - Zero multithreading locking collisions
                                                              │
       ┌──────────────────────────────────────────────────────┴────────┐
       │                                                               │
       ▼                                                               ▼
[ Spillover Scoring Engine ]                             [ Interactive Graph Builder ]
(backend/scoring.py)                                     (backend/graph_builder.py)
 - Credential Risk Weights                                - Vis.js Network Topology
 - Lateral Blast Radius                                   - Concentric Orbit Layout
 - Compliance Multipliers                                 - Multi-Hop In-Place Expansion
       │                                                               │
       └──────────────────────────────┬────────────────────────────────┘
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

### 3.7. AI Visual Identity & Multimodal Face Arbitration (`image_recon.py`)
- Purpose: Eliminates false-positive profile pictures (such as GitHub cartoon avatars, anime icons, game renders, or generic corporate logos) and selects the authentic real human photograph of the target identity.
- Multi-Source Visual Harvesting:
  - Gravatar MD5 hashes (with HTTP verification to exclude 404 identicons).
  - GitHub developer profile images across verified candidate handles.
  - Personal website OpenGraph (`og:image`) and portfolio author photographs.
  - Public profile avatars (Pinterest, Duolingo, corporate directories).
  - Verified LinkedIn high-resolution profile headshots from Waterfall reconnaissance.
- Zero-Heavy-Dependency Perceptual Feature Extraction:
  - Lightweight analysis using Pillow (`PIL.Image`) without heavy native C++ vision runtimes.
  - Evaluates aspect ratio and dimensions (`0.65 <= aspect <= 1.4` for portrait/avatar square).
  - Performs central 60% facial crop chrominance analysis in YCbCr color space to calculate human skin tone clustering (`77 <= Cb <= 135`, `133 <= Cr <= 177`, `Y >= 50`).
  - Measures color entropy and unique gradient distribution to differentiate continuous photographic lighting from flat graphic artwork.
- LLM Visual Reasoning & Dossier Arbitration:
  - Dispatches structured perceptual features, platform provenance, and target context to the AI reasoning engine (Groq Llama 3.3 / GPT-OSS).
  - The model autonomously distinguishes authentic human portraits from stylized cartoons, logos, or artificial avatars.
  - Returns classification (`REAL_HUMAN_PORTRAIT`, `CARTOON_OR_AVATAR`, `GRAPHIC_OR_LOGO`), plausibility score, and detailed forensic reasoning.
  - Sets the winning photograph into `employees.avatar_seed` and creates a primary `AVATAR_CORRELATION` pivot (`[TIED: PRIMARY FACE]`).
  - Preserves alternative candidate images as secondary visual pivots (`[STATUS: SECONDARY AVATAR]`) for comprehensive visual intelligence.
- 1-Click Reverse Visual Pivoting:
  - Pre-formats query endpoints for Google Lens, Yandex Visual, TinEye, Bing Visual, and PimEyes for immediate investigator pivoting.

### 3.8. Facebook OSINT & Investigator Session Vault (`facebook_recon.py`, `interactive_login.py`, `session_vault.py`)
- Purpose: Navigates Meta's aggressive login authwall (HTTP 400 and mandatory authentication checkpoints) to extract verified profile pictures, cover banners, biographical details, and timeline footprints.
- Unified Multi-Tab Session Interception:
  - Launches a single desktop Chromium/Edge window with Tab 1 for LinkedIn and Tab 2 for Facebook.
  - Automatically captures session cookies (`c_user` and `xs` for Facebook; `li_at` and `JSESSIONID` for LinkedIn) directly from the browser context upon successful authentication.
  - Injects green confirmation banners directly into the DOM of authenticated tabs, updates `.env`, and writes normalized cookies to `data/browser_session/storage_state.json`.
- Candidate Derivation & Disambiguation:
  - Generates deterministic candidate Facebook URLs based on verified name permutations, discovered handles, and local email parts.
  - Corroborates public search engine snippets (`site:facebook.com "{target_name}"`) and portfolio links against target attributes.
- Authenticated Timeline & Visual Extraction:
  - When investigator session tokens are present, automates Playwright with injected cookies to harvest high-resolution profile avatars and cover photos for multimodal visual arbitration.

### 3.9. Telecom Intelligence & Dummy Filtering (`telecom_recon.py`, `live_osint.py`)
- Parses raw phone numbers using `libphonenumber`.
- Extracts international formatting (E.164), carrier names, line types (mobile, landline, VOIP), and geographic regions.
- Documentation Filter: Discards fictional North American 555-exchange numbers (`+1-xxx-555-xxxx`) and sequential test numbers (`12345678`) found in repository README files or third-party collaborator documents.

### 3.10. Spillover Risk Scoring Algorithm (`scoring.py`)
Calculates an aggregate risk score (0 to 100) based on forensic attributes:
1. Credential Reuse Weight: Plaintext passwords reused across external services contribute up to 35 points.
2. Breach Recency & Volume: Darknet dumps, infostealer malware exposures, and paste appearances contribute up to 30 points.
3. Infrastructure & Identity Exposure: Discovered personal emails, phone numbers, PGP keys, and residential addresses contribute up to 20 points.
4. Corporate Target Multiplier: Targets with corporate email domains undergo elevated scrutiny (1.2x weight on unhashed credentials and executive VIP roles).

### 3.11. Attack Surface Graph Engine (`graph_builder.py`)
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

---

## 7. Concurrency & High-Performance Caching Subsystem

To eliminate end-to-end execution bottlenecks and ensure sub-40s cold scans and sub-200ms warm lookups, the OSINT pipeline operates on an asynchronous multi-stream execution model with in-memory TTL caching.

### 7.1. Multi-Stream Concurrent Reconnaissance Pipeline

Reconnaissance operations are segmented across three dedicated concurrent stages using bounded `concurrent.futures.ThreadPoolExecutor` pools:

1. Stage 1: Primary Stream Multiplexing (`max_workers=4`)
   - Worker 1: Live OSINT (`execute_deep_live_osint`) executing Holehe account enumeration, Git archaeology across commit histories, and OpenPGP keyserver queries.
   - Worker 2: Web Dork Reconnaissance (`execute_ai_dork_recon`) extracting search snippets from Bing, DuckDuckGo, and Yahoo.
   - Worker 3: Corporate Registries (`query_corporate_registries`) querying official Chamber of Commerce (KvK) and business directories.
   - Worker 4: Esports & Gaming Registries (`query_esports_earnings`) querying competitive handles and prize payouts.
   - Result: Aggregated Stage 1 latency reduced from 40+ seconds down to 13.89 seconds.

2. Stage 5: Concurrent Post-Recon Engine (`max_workers=2`)
   - Worker 1: WhatsMyName Handle Matrix (`enumerate_handle_wmn`) probing 700+ social and developer platforms.
   - Worker 2: Multimodal Avatar Harvesting (`harvest_target_images`) downloading and extracting perceptual chrominance features across Gravatar, GitHub, and OpenGraph sources.
   - Result: Stage 5 completes in 1.92 seconds.

3. Stage 7: Concurrent Authenticated Browser Runner (`max_workers=2`)
   - Worker 1: LinkedIn Playwright Runner (`auto_enrich_linkedin_profile`) with proxy waterfall and isolated headless browser execution.
   - Worker 2: Facebook Playwright Runner (`harvest_facebook_profile`) with authenticated session token injection.
   - Isolation Model: Both browser automation streams run isolated browser contexts (`browser.new_context(storage_state=...)`) without directory lock contention.
   - Result: Browser scraping duration reduced from ~13.5 seconds down to 6.78 seconds.

### 7.2. Thread-Safe SQLite Concurrency Model

SQLite databases operating in Write-Ahead Logging (WAL) mode enforce single-writer locking semantics. To prevent `sqlite3.OperationalError: database is locked` or cross-thread connection misuse:
- Background worker threads are restricted exclusively to network I/O, HTML/DOM parsing, and regex token normalization.
- Worker threads return structured findings payloads to the main orchestrator thread.
- All database write operations (`employees`, `pivots`, `credentials`, `physical_footprints`) execute synchronously on the main thread upon `future.result()` resolution.
- WAL checkpoints and transactional integrity are preserved without concurrency locks or race conditions.

### 7.3. Multi-Tier In-Memory TTL Caching Subsystem

All network-intensive reconnaissance modules integrate in-memory dictionary caches with a 300-second Time-To-Live (TTL):
- `backend/live_osint.py`: `_DEEP_OSINT_CACHE` caches Holehe, Git, and PGP results keyed by normalized email and handles.
- `backend/web_dork_recon.py`: `_SNIPPET_CACHE` caches organic search snippets with early-exit disambiguation when high-confidence corporate entities are corroborated.
- `backend/wmn_engine.py`: `_WMN_RESULT_CACHE` caches verified handle registrations across 700+ platforms.
- `backend/image_recon.py`: `_IMAGE_HARVEST_CACHE` caches harvested image candidates and perceptual skin tone vectors.
- `backend/browser_runner.py`: `_LINKEDIN_SCRAPE_CACHE` caches scraped profile dossiers keyed by candidate URLs.
- `backend/facebook_recon.py`: `_FB_SCRAPE_CACHE` caches authenticated Facebook timeline snapshots.

Defensive Immutability: Every cache read and write operation utilizes `copy.deepcopy()` to prevent in-place mutation side-effects across parallel or subsequent requests.

### 7.4. Headless Traversal Pruning & Timeout Hardening

- LinkedIn candidate traversal is capped to top 1 candidate (`[:1]`), eliminating redundant 4.5-second navigation timeouts on non-existent vanity slugs.
- Search snippet parsing incorporates entity early-exit short-circuiting: once an authentic employer and city are corroborated from top search snippets, redundant query permutations are bypassed.

### 7.5. Performance Benchmark Summary

| Query Phase | Baseline Latency | Optimized Cold Scan | Optimized Warm Scan (TTL) | Database Cached Lookup |
| :--- | :--- | :--- | :--- | :--- |
| Stage 1 (Live OSINT + Dorks + KvK + Esports) | ~42.0s | 13.89s | 0.001s (Cache Hit) | N/A |
| Stage 2-4 (AI Synthesis & Legal Arbiter) | ~18.5s | 10.22s | 10.15s | N/A |
| Stage 5 (WMN 700+ & Avatar Harvesting) | ~14.2s | 1.92s | 0.001s (Cache Hit) | N/A |
| Stage 6 (AI Cardinal Correlation) | ~2.5s | 1.54s | 1.48s | N/A |
| Stage 7 (Parallel Playwright LinkedIn + FB) | ~13.5s | 6.78s | 0.001s (Cache Hit) | N/A |
| Total End-to-End Execution | **110 - 130s** | **37.74s** | **18.05s** | **0.1589s** |
| Acceleration Factor | 1.0x | ~3.2x faster | ~6.5x faster | ~750x faster |
| Test Suite Stability | 59/59 Passing | 59/59 Passing | 59/59 Passing | 59/59 Passing |

