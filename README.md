# BreachSpillover

Identity Threat Exposure, Credential Spillover Analysis and Attack Surface Correlation Platform.

BreachSpillover is an open-source, local-first intelligence platform built for security analysts, threat hunters, and red/blue teams. It aggregates dark web database dumps, infostealer malware logs, public account registrations, passive infrastructure records, and open-source intelligence (OSINT) to map out an identity's digital exposure and quantify lateral credential spillover risk.

---

## Key Capabilities

### 1. Breach and Infostealer Intelligence
- Indexed local SQLite database running in WAL (Write-Ahead Logging) mode for sub-millisecond querying over large breach corpora.
- Ingestion and tracking of major darknet dumps (Collection #1, AntiPublic, Exploit.in, Adobe, LinkedIn, etc.) alongside active infostealer C2 exfiltrations (RedLine, Vidar, Lumma).
- Automatic credential classification separating plaintext passwords from hash algorithms (bcrypt, Argon2, SHA-512 crypt, SHA-256, SHA-1, MD5, and MySQL hashes).
- Hash resolution via public rainbow tables and reverse hash lookup endpoints.
- Cross-identity credential matching to detect corporate password reuse across external consumer services.

### 2. Multi-Source OSINT and Account Enumeration
- **Holehe Engine**: Probes 120+ web and cloud service endpoints (Microsoft 365, Spotify, Snapchat, LastPass, Duolingo, etc.) using password-reset and registration APIs without alerting target accounts.
- **WhatsMyName (WMN) Integration**: Dispatches concurrent multi-threaded probes across 700+ platform signatures to discover public profiles by handle.
- **Git Archaeology**: Scrapes GitHub commit history, author metadata, and repository pages to uncover real names, personal email addresses, and portfolio links.
- **OpenPGP Keyserver Indexing**: Queries Ubuntu HKP (`keyserver.ubuntu.com`), `keys.openpgp.org`, and MIT keyservers to extract verified PGP keys, key IDs, and secondary identities.
- **Gravatar Profile v2**: Parses Gravatar profile data, avatars, bios, and connected social media profiles.

### 3. Passive Infrastructure and DNS Reconnaissance
- **DNS-over-HTTPS (DoH)**: Non-intrusive DNS queries through Cloudflare and Google DoH for A, AAAA, MX, TXT, NS, SOA, and CAA records.
- **Certificate Transparency (CT) Logs**: Subdomain discovery via `crt.sh` to map organizational infrastructure and exposed endpoints (VPNs, SSO, mail gateways, developer panels).
- **Mail Exchanger (MX) & Email Security Posture**: Identifies corporate email providers (Google Workspace, Microsoft 365, Proofpoint, Mimecast) and evaluates SPF/DMARC policies (`p=reject`, `p=quarantine`, `p=none`).

### 4. Threat Dump and Paste Scraping
- Searches active paste services and dump sites (Pastebin, JustPaste.it, Rentry, Ghostbin, ControlC) for target email mentions and leaked credentials.
- Heuristic regex analysis detecting exposed API keys, bearer tokens, private keys, and credential patterns.
- Calculates situational severity ratings (Critical, High, Medium, Low) based on content analysis.

### 5. Interactive Attack Surface Graph
- Interactive visualization powered by Vis.js with real-time physics simulation.
- Categorized Provenance Hubs: Breaches, Git Repositories, Public Accounts, Telecom, and Geospatial records.
- **Concentric Orbit Mode (`[TIDY ORBITS]`)**: Organizes the graph into concentric geometric rings centered around the target identity to declutter complex graphs.
- **In-Place Multi-Hop Pivot Expansion**: Click any node (breach, credential, domain, handle, or identity) to dynamically traverse connected entities and query lateral records without reloading the canvas.
- Slide-in telemetry inspector drawer detailing metadata, raw hashes, and pivot triggers.

### 6. Telecom Intelligence
- International phone number normalization and formatting (E.164 standard) via `libphonenumber`.
- Carrier identification, line type validation (mobile, fixed-line, VOIP), and country-level routing telemetry.

### 7. Pluggable AI Narrative Engine
- Supports automated synthesis of executive threat intelligence briefings using external LLM providers.
- Direct integration with Groq Cloud (Meta Llama 3.3 70B, ~300 tokens/sec) and Google Gemini (Gemini 1.5 Flash).
- Generates threat actor playbooks, attack chain narratives, and structured defensive remediations.

### 8. Forensic Reporting and Exports
- **CSV Export**: Comprehensive flat spreadsheet ledger of all breaches, stolen credentials, verified handles, and geospatial footprints with UTF-8 BOM encoding for Excel compatibility.
- **Microsoft Word (.doc) Export**: Executive incident report with summary tables, risk classifications, and confidentiality disclaimers.
- **JSON Export**: Raw machine-readable forensic payload for SIEM and SOAR pipelines.
- **PDF Export**: Single-click executive brief generation via HTML5 canvas renderer.

### 9. Interface and System Controls
- Dual-theme engine supporting full Dark and Light modes, with synchronized Leaflet tile layers (CartoDB DarkMatter and Positron) and graph color palettes.
- Web Audio API 8-bit retro chiptune sound synthesis with header mute toggle.

---

## Architecture Overview

```
BreachSpillover/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & API routers
│   ├── database.py              # SQLite schema, WAL configuration & connection pool
│   ├── osint_scanner.py         # Multi-source intelligence orchestrator
│   ├── live_osint.py            # Holehe, Gravatar, PGP, and Git scraping modules
│   ├── wmn_engine.py            # WhatsMyName 700+ signature probe engine
│   ├── dns_recon.py             # DoH DNS lookups, CT log parser, and mail posture
│   ├── paste_recon.py           # Paste site search and heuristic regex secret detector
│   ├── telecom_recon.py         # E.164 phone normalization and carrier lookup
│   ├── web_dork_recon.py        # Web scraping, portfolio analysis & content validation
│   ├── graph_builder.py         # Vis.js graph transformer and multi-hop pivot logic
│   ├── scoring.py               # Spillover risk calculation and severity engine
│   ├── hash_resolver.py         # Rainbow table lookup and hash algorithm detector
│   ├── ai_engine.py             # Groq and Gemini AI dossier generation
│   ├── masking.py               # PII masking utilities for audit mode
│   ├── models.py                # Pydantic data schemas
│   └── data/
│       ├── wmn-data.json        # WhatsMyName signature definitions
│       └── hibp_breaches_catalog.json # Metadata catalog of verified breaches
├── frontend/
│   ├── index.html               # Single-page dashboard interface
│   └── static/
│       ├── css/style.css        # Responsive styling and dual-theme variables
│       └── js/app.v17.js        # UI controller, Vis.js graph, audio engine, exports
├── data/
│   └── breach_spillover.db      # Local SQLite breach and intelligence store
├── data_generator/
│   └── seed_data.py             # Deterministic seed data generator for testing
├── tests/
│   ├── test_spillover.py        # Core integration and regression test suites
│   ├── test_ai_engine.py        # AI engine unit tests
│   ├── test_telecom_recon.py    # Telecom parser tests
│   └── test_friend_archaeology.py # OSINT archaeology tests
├── import_breach.py             # High-throughput CLI leak dump and combolist importer
├── run.py                       # One-step startup and server launcher
└── requirements.txt             # Python package dependencies
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

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
```

### 4. Configure Environment Variables (Optional)
Copy the template configuration file:
```bash
cp .env.example .env
```

Edit `.env` to supply API keys if you wish to use external AI or paid HIBP endpoints:
```ini
# Free instant key from https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Free instant key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Paid HIBP key (if omitted, free public indices are used automatically)
HIBP_API_KEY=
```

---

## Running the Application

Start the local server using the launch script:
```bash
python run.py
```

The script initializes the local SQLite database if it does not already exist, seeds baseline test profiles, and starts the FastAPI server at:
```
http://127.0.0.1:8000
```

Open `http://127.0.0.1:8000` in any modern web browser to access the interface.

---

## Ingesting Custom Breaches and Combolists

BreachSpillover includes a high-throughput CLI tool (`import_breach.py`) for importing custom leak dumps, combolists, and CSV breach data directly into the local database.

### Features:
- Auto-detects delimiters (colon, semicolon, comma, pipe, tab).
- Detects format variations (`email:pass`, `user:email:pass`, `email:hash:salt`, etc.).
- Automatically classifies password hashes (bcrypt, Argon2, SHA-512, SHA-256, SHA-1, MD5).
- Performs batch inserts in transactions of 5,000 to 20,000 records for high throughput.

### Usage:
```bash
# Basic combolist import (colon-delimited)
python import_breach.py path/to/combo.txt --name "Exploit_Dump_2024"

# Custom delimiter and breach metadata
python import_breach.py leaks.csv --delimiter "," --name "Internal_Corporate_Leak" --date "2024-06-15" --severity CRITICAL

# Dry-run mode to validate parsing without writing to the database
python import_breach.py dump.txt --name "Test_Dump" --dry-run
```

You can also import combolists directly from the web interface using the **`[INGEST COMBOLIST]`** button in the top navigation bar.

---

## API Reference

The backend exposes a REST API running on port 8000. Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Core Endpoints

#### `GET /api/search`
Runs a full identity investigation across local breaches and live OSINT sources.
- **Parameters**:
  - `email` (string, required): Target email address or identifier.
  - `audit_mode` (boolean, optional, default: `true`): Returns unmasked forensic data.
  - `known_name` (string, optional): Known target full name to anchor OSINT correlation.
  - `known_username` (string, optional): Known target username.
  - `known_phone` (string, optional): Known phone number.
  - `known_city` (string, optional): Known residential or operating city.
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
  - `query` (string, required): Raw phone number (e.g., `+14155552671`).

#### `GET /api/hash/resolve`
Queries public rainbow tables to crack or identify password hashes.
- **Parameters**:
  - `hash` (string, required): Hexadecimal or formatted hash string.

#### `POST /api/ai/dossier`
Generates a structured narrative threat brief using Groq or Gemini.
- **Request Body**: Current investigation JSON payload.

#### `GET /api/stats`
Returns system inventory metrics, indexed breach counts, credential volumes, and pivot statistics.

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
# Run all tests
pytest tests/ -v

# Run core spillover and OSINT integration tests
pytest tests/test_spillover.py -v
```

### Test Suites Included:
- **Suite 1**: PII and credential masking engine verification.
- **Suite 2**: SQLite relational schema integrity and risk scoring calculations.
- **Suite 3**: FastAPI REST endpoint validation and error handling.
- **Suite 4**: Multi-source OSINT correlation and attack playbook generation.
- **Suite 5**: EmploLeaks subdomains and handle permutations.
- **Suite 6**: Disposable email detection and rainbow table hash resolution.
- **Suite 7**: Universal multi-modal search and combolist importer validation.
- **Suite 8**: WhatsMyName engine, passive DNS DoH lookups, and paste scrapers.

---

## License and Ethical Use Notice

BreachSpillover is developed strictly for authorized security research, defensive posture assessments, and forensic investigations. Users are responsible for ensuring that all reconnaissance and analysis activities comply with relevant local and international computer crime legislation.

Distributed under the MIT License.