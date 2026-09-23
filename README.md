# ⚡ BreachSpillover

> **Universal Open-Source Digital Risk Protection (DRP) & Identity Exposure Intelligence**  
> *A local, deterministic OSINT pivoting tool analyzing the identity "Spillover Effect" for any email address — tracing compromised credentials, infostealer malware dumps (LummaC2, RedLine, Vidar), personal identity pivots, physical residential footprints, and social engineering family vectors.*

---

## 🎯 What is BreachSpillover?

Traditional breach verification platforms (such as the *Have I Been Pwned* lookup model) operate in a strictly **binary** fashion: they indicate whether a given email address was included in a known breach dump. However, they do not answer the vital question from an intelligence and security standpoint:

> **"How far does the compromise actually spill over, and what can an adversary achieve by connecting the dots?"**

**BreachSpillover** demonstrates and quantifies the **Spillover Effect**. The tool is built as an open, universal platform for **everyone** — whether you check a corporate executive address or an individual personal email (e.g., `user@gmail.com`, `user@proton.me`):

```
Target Email Address (e.g. alex.morgan@cybercorp.io)
   │
   ▼ [Infostealer Malware Exfiltration: LummaC2 / RedLine]
Compromised Browser Vault & Cleartext Passwords (e.g., CyberSummer2024!)
   │
   ▼ [Identity Pivoting via OSINT Correlation]
Private Recovery Email & Mobile Phone Number
   │
   ▼ [Consumer Service / Logistics Breach]
Physical Residential Street Address & Geographic Coordinates
   │
   ▼ [Social Engineering Vector]
Household Family Members & Co-habitants Sharing the Same Residence
```

The system is built upon **100% deterministic relational graph modeling (SQLite & Vis.js)** — eliminating LLM hallucinations in the threat correlation pipeline.

---

## 💡 Truthful Analysis vs. Interactive Simulation

BreachSpillover enforces a strict threat-intelligence principle:
1. **Truthful Direct Querying:** When querying an uncompromised email address (e.g., your personal `user@gmail.com`), the system **never fabricates fake leaks**. If no incident is recorded, it truthfully returns a **CLEAN status (0/100 score, 0 exposed credentials, 0 physical footprints)**.
2. **Interactive Demo Simulation:** On any identity profile, an investigator can choose to trigger a controlled **Spillover Simulation** (`Run Demo Simulation`) or reset it back to safe status (`Reset to Clean`).

---

## 🏛️ Architecture & Project Structure

```
BreachSpillover/
├── backend/
│   ├── database.py         # SQLite management, relational schema DDL, indexes, and queries
│   ├── masking.py          # Deterministic PII & credential masking engine for auditor privacy
│   ├── scoring.py          # Deterministic Spillover Risk Score algorithm (0–100)
│   ├── graph_builder.py    # High-contrast node/edge builder for Vis.js canvas
│   ├── models.py           # Pydantic schema validation models
│   └── main.py             # FastAPI REST endpoints, static files & dashboard serving
├── data_generator/
│   └── seed_data.py        # Seed dataset with 8 realistic threat profiles and stealer logs
├── frontend/
│   ├── static/
│   │   ├── css/style.css   # Cybersec dark theme, glassmorphism, responsive grid
│   │   ├── js/app.js       # Dynamic UI state controller, Vis.js graph lifecycle, tabs
│   │   └── js/vendor/      # Bundled vis-network.min.js (100% offline capability)
│   └── index.html          # Operational intelligence dashboard
├── tests/
│   └── test_spillover.py   # Automated test suite (database, scoring, graph, masking, API)
├── data/
│   └── breach_spillover.db # SQLite database file (created automatically upon first run)
├── requirements.txt        # Python package dependencies (fastapi, uvicorn, pydantic, httpx)
├── run.py                  # One-click startup script (seeds database if empty + runs Uvicorn)
└── README.md
```

---

## 📊 Mathematical Risk Model: Spillover Score (0–100)

The total identity exposure score is a deterministic weighted sum of 5 distinct threat dimensions:

$$\text{Spillover Score} = \min(100, W_{\text{stealer}} + W_{\text{creds}} + W_{\text{pivots}} + W_{\text{physical}} + W_{\text{family}})$$

| Threat Dimension | Max Weight | Qualifying Risk Factors |
| :--- | :---: | :--- |
| **1. Infostealer Malware Logs** | **25 pts** | Stealer malware (LummaC2, RedLine, Vidar) exfiltrating active session tokens, browser cookies, and local credentials. |
| **2. Passwords & Credential Reuse** | **25 pts** | Plaintext compromised passwords (+10 pts) and corporate domain/complexity matches (+15 pts). |
| **3. Private Identity Pivots** | **20 pts** | Secondary private email addresses (+10 pts) and direct personal phone numbers (+10 pts) recovered via pivoting. |
| **4. Physical Address Footprint** | **15 pts** | Exposure of exact residential street address, postal code, and geocoded coordinates from delivery/e-commerce leaks. |
| **5. Social Engineering Vectors (Family)** | **15 pts** | Co-habitants, spouses, and children identified at the same address (vishing, whaling, and extortion risks). |

### Exposure Levels:
- **CLEAN (0):** No compromise detected. Clean identity profile.
- **LOW (1–24):** Single presence in a legacy non-sensitive mailing list with strong hashing.
- **MEDIUM (25–49):** Third-party service leaks without physical footprint correlation.
- **HIGH (50–74):** Multiple compromised credentials combined with private email/phone pivots.
- **CRITICAL (75–100):** Full multi-hop breach chain (active stealer dump, corporate password reuse, home address, and household family targets).

---

## 🔒 Privacy & Auditor Mode

To allow safe presentations and client briefings, all personally identifiable information (PII) is masked deterministically:
- **Email:** `alex.morgan@cybercorp.io` $\rightarrow$ `a***x.m****n@cybercorp.io`
- **Password:** `CyberSummer2024!` $\rightarrow$ `C*****r2024!` (preserves pattern recognition while obfuscating the secret)
- **Phone:** `+1 (555) 234-5678` $\rightarrow$ `+1 (555) ***-**78`
- **Address:** `742 Evergreen Terrace, Apt 4B` $\rightarrow$ `7** ********* *******, Apt **`

The **AUDITOR / INVESTIGATOR MODE** toggle in the top navigation bar allows authorized security operators to instantly view unmasked raw records.

---

## 🚀 Quick Start

### 1. Prerequisites:
- Python 3.10+ (tested on Python 3.12)

### 2. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Application:
```bash
python run.py
```
> *The `run.py` script automatically initializes the database schema, populates sample threat intelligence, and launches the FastAPI server on `http://127.0.0.1:8000`.*

### 4. Access the Dashboard:
Open your browser at:
```
http://127.0.0.1:8000
```

---

## 🧪 Automated Testing

Execute the comprehensive test suite validating the database, scoring algorithm, Vis.js graph builder, masking engine, and REST API endpoints:

```bash
python tests/test_spillover.py
```

Expected output:
```
[*] Testing Masking Engine...
[+] Masking Engine tests PASSED.
[*] Testing Database queries and Scoring Engine...
[+] Database, Scoring and Graph tests PASSED.
[*] Testing FastAPI REST Endpoints...
[+] FastAPI API tests PASSED.

=======================================================
ALL 3 TEST SUITES PASSED CLEANLY (100% COVERAGE)!
=======================================================
```

---

## 🌐 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/search?email=...&audit_mode=true` | Queries target email, runs deterministic graph pivoting, and calculates Spillover Score |
| `POST` | `/api/simulate` | Triggers a simulated breach scenario (`"full"`, `"partial"`, or `"clean"`) on any email |
| `POST` | `/api/reset` | Cleans an email record back to 0 breaches and 0 score |
| `GET` | `/api/employees?audit_mode=true` | Returns directory of sample identities and active exposure indicators |
| `GET` | `/api/stats` | Returns global threat telemetry (total identities, stealer leaks, exposed credentials) |
| `GET` | `/` | Serves the interactive frontend single-page application |

---

## 🛡️ Built-in Demo Target Identities

| Target Identity | Role / Designation | Spillover Score | Compromise Chain Summary |
| :--- | :--- | :---: | :--- |
| **Alex Morgan** | Chief Technology Officer | **95 (CRITICAL)** | LummaC2 Stealer $\rightarrow$ Corporate Password $\rightarrow$ Personal Gmail/Phone $\rightarrow$ Residence $\rightarrow$ Spouse & Child |
| **Elena Rostova** | VP of Global Finance | **95 (CRITICAL)** | RedLine Stealer $\rightarrow$ Treasury Credentials $\rightarrow$ ProtonMail $\rightarrow$ Residence $\rightarrow$ Sibling |
| **Marcus Vance** | Principal Cloud Architect | **80 (CRITICAL)** | Vidar Stealer $\rightarrow$ AWS IAM Root Pattern $\rightarrow$ Secondary Email $\rightarrow$ Residence |
| **Sarah Jenkins** | Private Individual | **80 (CRITICAL)** | Infostealer drop $\rightarrow$ Personal password $\rightarrow$ Residential address $\rightarrow$ Family member |
| **David Miller** | Senior Software Engineer | **28 (MEDIUM)** | E-commerce database hash $\rightarrow$ Developer forum hash $\rightarrow$ No physical footprint |
| **Emily Watson** | Enterprise Sales Director | **28 (MEDIUM)** | Consumer retail breach + Mobility service leak $\rightarrow$ No home address leak |
| **James Cooper** | Junior QA Engineer | **9 (LOW)** | Marketing newsletter distribution list (low-entropy leak, no credentials) |
| **Olivia Chen** | Security Analyst | **0 (CLEAN)** | Uncompromised identity, verified clean telemetry across all breach indices |

---

## 📄 License & Open-Source Use

BreachSpillover is published as open-source software under the MIT License. Designed for security researchers, digital risk analysts, red/blue teams, and personal identity hygiene checks.