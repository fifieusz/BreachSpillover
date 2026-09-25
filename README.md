# BreachSpillover

Identity Threat Exposure, Credential Spillover Analysis, and Attack Surface Correlation Platform.

BreachSpillover is a local-first security intelligence platform designed for security analysts, threat hunters, and security teams. It aggregates dark web database dumps, infostealer malware logs, live OSINT probes, public account registrations, passive infrastructure records, and web reconnaissance footprints to map an identity's attack surface and evaluate lateral credential spillover risks.

---

## Core Capabilities

### 1. Breach and Infostealer Intelligence
- Indexed local SQLite database running in WAL (Write-Ahead Logging) mode for sub-millisecond querying over breach collections.
- Tracking of public breach corpora alongside active infostealer C2 logs (RedLine, Vidar, Lumma, Meta).
- Automated credential classification separating plaintext passwords from hash algorithms (bcrypt, Argon2, SHA-512 crypt, SHA-256, SHA-1, MD5, and MySQL).
- Hash resolution via public rainbow tables and reverse hash lookup endpoints.
- Cross-identity credential matching to detect corporate password reuse across consumer services.

### 2. Multi-Source OSINT and Account Enumeration
- Holehe Engine: Non-intrusive password-reset and registration API probes across 120+ web and cloud service endpoints (Microsoft 365, Spotify, Snapchat, LastPass, Duolingo, etc.).
- WhatsMyName (WMN) Integration: Multi-threaded probes across 700+ platform signatures to discover public profiles by username handle.
- Git Archaeology: Scrapes commit histories, author metadata, and repository documents to discover verified real names, secondary email addresses, and portfolio links.
- OpenPGP Keyserver Indexing: Queries Ubuntu HKP (`keyserver.ubuntu.com`), `keys.openpgp.org`, and MIT keyservers for verified PGP keys, key IDs, and secondary email identities.
- Gravatar Profile v2: Parses Gravatar profile data, avatars, bios, and linked social media accounts.

### 3. Hybrid Waterfall Web and LinkedIn Reconnaissance
- Tier 1 Unblocker Gateway: Optional routing through external proxy unblockers (Scrape.do, ScraperAPI, ScrapingBee, ZenRows) to bypass anti-bot and rate-limiting barriers.
- Tier 2 Local Headless Browser: Integrated Playwright headless runner that leverages authenticated investigator sessions to extract deep profile timelines, headlines, employers, and avatars without triggering authwalls.
- Dynamic Vanity Slug Derivation: Generates high-entropy candidate slugs (`first-last`, `firstlast`, initial+last, email stems) while demoting ambiguous single-name vanities.
- Multi-Token Identity Corroboration Gate: Scraped profiles are strictly validated against target surnames and identity tokens before ingestion, rejecting stranger entity collisions.
- Dual Workplace Resolution: Preserves multi-employer affiliations (such as concurrent corporate roles, educational institutions, or holding entities) directly in employee records.

### 4. AI-Driven Identity Corroboration and Lead Quarantine
- Multi-Category Segregation: Discovered accounts and candidate profiles are categorized into:
  - VERIFIED (PUBLIC_PROFILE): Conclusively corroborated accounts (email-bound registrations, matching author commits, full name corroborated).
  - SUSPECTED (SUSPECTED_ACCOUNT): Plausible candidate handles (such as single given-name or single surname handles) quarantined in the analyst drawer with confidence scores and reasoning notes, preserving investigative leads without contaminating verified data.
  - REJECTED: Entity collisions and conflicting stranger identities pruned from target dossiers.
- Single Given-Name Collision Protection: Handles matching common first names (`@jordin`, `@david`, `@alex`) on global developer registries are never auto-verified by length alone.

### 5. Live Web Dorking and Corporate Registry Intel
- Multi-Engine Organic Scraping: Queries Bing, DuckDuckGo, and Yahoo for target names, corporate affiliations, and email mentions.
- Corporate Registry Validation: Integrates Chamber of Commerce (KvK, Drimble) data to discover registered corporate headquarters, legal entity registrations, and business co-partners.
- Portfolio and Personal Site Analysis: Analyzes personal portfolios (`.github.io`, `.wixsite.com`, custom domains) to extract verified biographic narratives and locations.

### 6. Passive Infrastructure and DNS Reconnaissance
- DNS-over-HTTPS (DoH): Passive DNS queries through Cloudflare and Google DoH for A, AAAA, MX, TXT, NS, SOA, and CAA records.
- Certificate Transparency (CT) Logs: Subdomain discovery via `crt.sh` to map organizational infrastructure and exposed endpoints (VPNs, SSO, mail gateways).
- Email Security Posture: Evaluates SPF, DMARC, and DKIM policies (`p=reject`, `p=quarantine`, `p=none`) and identifies mail exchangers (Google Workspace, Microsoft 365, Proofpoint, Mimecast).

### 7. Threat Dump and Paste Scraping
- Searches active paste services and dump sites (Pastebin, JustPaste.it, Rentry) for target email mentions and leaked credentials.
- Heuristic regex analysis detecting exposed API keys, bearer tokens, private keys, and credential formats.
- Severity classification (Critical, High, Medium, Low) based on matched sensitive patterns.

### 8. Interactive Attack Surface Graph
- Interactive visualization powered by Vis.js with physics simulation.
- Provenance Hubs: Breaches, Git Repositories, Public Accounts, Telecom, and Geospatial records.
- Concentric Orbit Mode (`[TIDY ORBITS]`): Organizes the graph into concentric geometric rings centered around the target identity to declutter complex graphs.
- In-Place Multi-Hop Pivot Expansion: Traverses connected entities (breaches, credentials, domains, handles) directly on the active canvas.
- Telemetry Inspector: Slide-in inspector detailing node metadata, raw hashes, and pivot triggers.

### 9. Telecom Intelligence
- International phone number normalization and formatting (E.164 standard) via `libphonenumber`.
- Carrier identification, line type validation (mobile, fixed-line, VOIP), and country-level routing telemetry.
- Documentation Dummy Filter: Automatically filters out North American fictional 555-exchange numbers and sample documentation numbers from repository documents.

### 10. Pluggable AI Narrative Engine and Copilot
- Automated synthesis of executive threat intelligence briefings using external LLM providers.
- Direct integration with Groq Cloud (Meta Llama 3.3 70B) and Google Gemini (Gemini 1.5 Flash).
- Interactive Copilot panel supporting ad-hoc investigative questions, attack blast radius analysis, and remediation checklists.

### 11. Forensic Reporting and Exports
- CSV Export: Flat spreadsheet ledger of breaches, stolen credentials, verified handles, and geospatial footprints with UTF-8 BOM encoding for Excel compatibility.
- Microsoft Word (.doc) Export: Executive incident report with summary tables, risk classifications, and confidentiality disclaimers.
- Defensive Exposure Report: Sanitized JSON and Markdown exports that allowlist non-sensitive exposure metrics for defensive remediation without exposing raw passwords or residential addresses.
- Full JSON & PDF Exports: Machine-readable forensic payload for SIEM/SOAR pipelines and single-click executive brief rendering.

---

## Architecture Overview

```
BreachSpillover/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint and API routers
│   ├── database.py              # SQLite schema, WAL configuration, and query execution
│   ├── osint_scanner.py         # Multi-source intelligence orchestrator
│   ├── ai_correlator.py         # Multi-token identity resolution and quarantine engine
│   ├── linkedin_recon.py        # Candidate vanity slug generator and identity verification gate
│   ├── browser_runner.py        # Playwright headless browser runner for authenticated scraping
│   ├── browser_bridge.py        # Local browser session detection and Google SSO bridge
│   ├── unblocker_client.py      # Tier 1 proxy unblocker client with headless fallback
│   ├── session_vault.py         # Persistent session management for authenticated browser contexts
│   ├── live_osint.py            # Holehe, Gravatar, OpenPGP, and Git scraping modules
│   ├── web_dork_recon.py        # Multi-engine search dorking, snippet analysis, and LLM disambiguation
│   ├── corporate_recon.py       # Chamber of Commerce and business registry intelligence
│   ├── image_recon.py           # Visual identity and avatar correlation engine
│   ├── email_verifier.py        # RFC format, DNS, MX, and disposable email validation
│   ├── wmn_engine.py            # WhatsMyName 700+ signature probe engine
│   ├── dns_recon.py             # DoH DNS lookups, Certificate Transparency logs, and mail posture
│   ├── paste_recon.py           # Paste site search and heuristic regex secret detector
│   ├── telecom_recon.py         # E.164 phone normalization, carrier lookup, and dummy filtering
│   ├── graph_builder.py         # Vis.js graph transformer and multi-hop pivot logic
│   ├── scoring.py               # Spillover risk calculation and severity engine
│   ├── hash_resolver.py         # Rainbow table lookup and hash algorithm detector
│   ├── ai_engine.py             # Groq and Gemini AI dossier generation and copilot chat
│   ├── masking.py               # PII masking utilities for audit mode
│   ├── models.py                # Pydantic request and response schemas
│   └── data/
│       ├── wmn-data.json        # WhatsMyName signature definitions
│       └── hibp_breaches_catalog.json # Metadata catalog of verified breaches
├── frontend/
│   ├── index.html               # Single-page dashboard interface
│   └── static/
│       ├── css/style.css        # Responsive styling and dual-theme variables
│       └── js/app.v18.js        # UI controller, Vis.js graph, audio engine, exports
├── data/
│   └── breach_spillover.db      # Local SQLite breach and intelligence store
├── tests/
│   ├── test_spillover.py        # Core integration and regression test suites
│   ├── test_ai_engine.py        # AI engine unit tests
│   ├── test_telecom_recon.py    # Telecom parser tests
│   ├── test_linkedin_safety.py  # Vanity slug and identity verification tests
│   ├── test_linkedin_bridge.py  # Browser bridge and session tests
│   ├── test_unblocker.py        # Unblocker gateway tests
│   └── test_session_vault.py    # Session storage and cookie tests
├── import_breach.py             # High-throughput CLI leak dump and combolist importer
├── run.py                       # Startup script and server launcher
└── requirements.txt             # Python package dependencies
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git
- Microsoft Edge, Google Chrome, or Chromium (for local browser scraping features)

### 1. Clone the Repository
```bash
git clone https://github.com/fifieusz/BreachSpillover.git
cd BreachSpillover
```

### 2. Set Up a Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Environment Variables (Optional)
Copy the template configuration file:
```bash
cp .env.example .env
```

Edit `.env` to configure optional API keys and proxy settings:
```ini
# AI Analysis (free key from https://console.groq.com/keys)
GROQ_API_KEY=your_groq_api_key_here

# Alternative AI Provider (free key from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Proxy Unblocker API Key (Scrape.do, ScraperAPI, ScrapingBee, or ZenRows)
SCRAPER_API_KEY=
SCRAPER_PROVIDER=scrapedo

# Optional: Dedicated LinkedIn Session Cookie (if not using local browser bridge)
LINKEDIN_LI_AT=
```

---

## Running the Application

Start the local server using the launch script:
```bash
python run.py
```

The script initializes the local SQLite database if not present, verifies dependency requirements, and starts the FastAPI server at:
```
http://127.0.0.1:8000
```

Open `http://127.0.0.1:8000` in any modern web browser to access the interface.

---

## Ingesting Custom Breaches and Combolists

BreachSpillover includes a high-throughput CLI tool (`import_breach.py`) for importing custom leak dumps, combolists, and CSV breach data directly into the local database.

### Features
- Delimiter detection (colon, semicolon, comma, pipe, tab).
- Format parsing (`email:pass`, `user:email:pass`, `email:hash:salt`, etc.).
- Automated hash classification (bcrypt, Argon2, SHA-512, SHA-256, SHA-1, MD5).
- Batch inserts using transactional batches of 5,000 to 20,000 records.

### Usage Examples
```bash
# Basic combolist import (colon-delimited)
python import_breach.py path/to/combo.txt --name "Exploit_Dump_2024"

# Custom delimiter and breach metadata
python import_breach.py leaks.csv --delimiter "," --name "Internal_Corporate_Leak" --date "2024-06-15" --severity CRITICAL

# Dry-run mode to validate parsing without writing to the database
python import_breach.py dump.txt --name "Test_Dump" --dry-run
```

Combolists can also be imported directly from the web interface using the **`[INGEST COMBOLIST]`** button in the top navigation bar.

---

## API Reference

The backend exposes a REST API running on port 8000. Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Primary Endpoints

#### `GET /api/search` (or `/api/scan`)
Runs an identity investigation across local breaches and live OSINT sources.
- **Parameters**:
  - `email` (string, required): Target email address or identifier.
  - `audit_mode` (boolean, optional, default: `true`): Returns unmasked forensic data.
  - `refresh` (boolean, optional, default: `false`): Forces fresh reconnaissance bypassing cached records.
  - `known_name` (string, optional): Target real name to anchor OSINT correlation.
  - `known_username` (string, optional): Target handle or alias.
  - `known_phone` (string, optional): Target phone number.
  - `known_city` (string, optional): Target city of residence or operation.
- **Response**: Identity record, risk score, leak list, credentials, OSINT pivots, footprints, and Vis.js graph structure.

#### `POST /api/graph/pivot-expand`
Expands the attack graph in-place from any selected node.
- **Request Body**:
  ```json
  {
    "node_id": "leak_14",
    "pivot_type": "BREACH",
    "pivot_value": "Adobe Systems",
    "employee_id": 1
  }
  ```
- **Response**: New nodes and edges to merge into the active canvas.

#### `GET /api/recon/wmn`
Runs WhatsMyName profile enumeration across 700+ websites.
- **Parameters**:
  - `handle` (string, required): Username to query.
  - `max_sites` (integer, optional, default: `50`): Maximum sites to probe.

#### `GET /api/recon/infrastructure`
Queries DNS-over-HTTPS and Certificate Transparency logs for domain infrastructure.
- **Parameters**:
  - `domain` (string, required): Domain name to evaluate (e.g., `company.com`).

#### `GET /api/recon/pastes`
Searches public paste repositories for leaked data.
- **Parameters**:
  - `target` (string, required): Identifier or email to search.
  - `max_results` (integer, optional, default: `10`): Maximum results to return.

#### `GET /api/recon/telecom`
Normalizes and validates phone numbers.
- **Parameters**:
  - `query` (string, required): Raw phone number (e.g., `+31621165021`).

#### `GET /api/hash/resolve`
Queries public rainbow tables to crack or identify password hashes.
- **Parameters**:
  - `hash` (string, required): Hexadecimal or formatted hash string.

#### `POST /api/ai/dossier`
Generates a structured narrative threat brief using Groq or Gemini.
- **Request Body**: Current investigation JSON payload.

#### `POST /api/ai/copilot`
Interactive chat endpoint for investigative Q&A against the active target dossier.

#### `GET /api/sessions/status`
Returns status of stored browser sessions and active scraping credentials.

#### `GET /api/unblocker/status`
Returns configuration and connectivity status of the proxy unblocker gateway.

#### `GET /api/stats`
Returns system inventory metrics, indexed breach counts, credential volumes, and pivot statistics.

---

## Running Automated Tests

Run the test suite using `unittest` or `pytest`:
```bash
# Run core test suites
python -m unittest discover tests/

# Run specific integration tests
python -m unittest tests/test_linkedin_safety.py tests/test_telecom_recon.py
```

### Test Coverage Areas
- PII and credential masking engine validation.
- SQLite schema integrity and spillover risk calculations.
- FastAPI endpoint contracts and error responses.
- Multi-source OSINT correlation and candidate quarantine logic.
- LinkedIn vanity slug derivation and identity corroboration gates.
- E.164 telecom normalization and documentation dummy number filtering.
- Unblocker gateway routing and headless browser fallback.

---

## License and Ethical Use Notice

BreachSpillover is developed strictly for authorized security research, defensive posture assessments, and forensic investigations. Users are responsible for ensuring that all reconnaissance and analysis activities comply with relevant local and international computer crime legislation.

Distributed under the MIT License.