# BreachSpillover — Architecture Notes

Durable project memory for future sessions (MemoryGraph is not active in this
environment; keep this file concise and current instead).

## Purpose
Defensive breach-exposure + OSINT investigation tool. An authorized user enters
an email / username / domain / phone / hash and the app reports known breach
exposure and public online footprint. Data is largely seeded/deterministic
(`data_generator/seed_data.py`, `backend/seeder.py`); several OSINT enrichers
make live network calls (blocked by the egress proxy in this environment).

## Stack & entry points
- Backend: FastAPI (`backend/main.py`), SQLite WAL (`backend/database.py`).
  Launch: `python run.py` (seeds DB if empty, serves on 127.0.0.1:8000).
- Frontend: single-page app. `frontend/index.html` + one controller
  `frontend/static/js/app.v17.js` (~5.9k lines, browser globals, no build step).
  Served via `app.mount("/static", StaticFiles(directory=frontend/static))`.
- Dependencies: `requirements.txt`. NOTE: `phonenumbers` is required by
  `backend/live_osint.py` and was missing — added to requirements.

## Search flow
`/api/search` (alias `/api/scan`) in `main.py:139` →
`get_or_create_identity_profile` → gathers leaks, credentials, pivots,
physical_footprints, relatives → scoring + graph → returns one JSON object.
Frontend `executeInvestigation(email)` (app.v17.js) fetches it, stores it in the
module-level `let currentInvestigationData`, and renders. Secondary recon:
`/api/recon/wmn` (WhatsMyName public accounts) stored in `currentWMNResults`.

## `currentInvestigationData` shape (frontend state)
Keys: `employee`, `spillover_score`, `leaks[]`, `credentials[]`, `pivots[]`,
`physical_footprints[]`, `relatives[]`, `graph`, `timeline`, `email_verification`,
`osint_dorks`, `threat_provenance_matrix`, `cross_target_correlations`, ...

### SENSITIVE fields (never export / never put in defensive reports)
- `credentials[].plaintext_password`, `.password_hash`
- `physical_footprints[]` (`address_line`, `latitude`, `longitude`, `city`)
- `relatives[]` (names, `contact_email`, `contact_phone`, `social_engineering_risk`)
- `pivots[]` — mixed; includes `PHONE_NUMBER`, `PERSONAL_EMAIL`, `FULL_NAME`,
  `LOCATION`, `IP_ADDRESS`, PGP keys. Treat as sensitive; do NOT source exports from it.

### Non-sensitive / exposure-level fields (safe to surface)
- `leaks[]`: `leak_name`, `breach_date`, `leak_type`, `severity`,
  `exposed_data` (category labels, not values), `threat_actor_source`, `description`.
- WhatsMyName matches: `platform`, `category`, `url`, `confidence_score`.

## Sound system  (app.v17.js)
- `SoundManager` object + `playSound(key)` global. Cues → files under
  `frontend/static/sounds/` served at `/static/sounds/`:
  `click`→Clickingsound.mp3, `search`→Searchingsound.mp3,
  `error`→Errorsound.mp3, `export`→Exportbuttonsound.mp3.
- Shares the existing SFX mute flag (`localStorage "breachspillover_sfx"`), so the
  header SFX toggle controls it. Lazy `Audio`, 150ms per-cue throttle, all playback
  wrapped in try/catch + promise `.catch` — missing files 404 silently, never crash.
- Wiring: `search` in `executeInvestigation`; `click` in `triggerSearch` (after
  non-empty check) and at the start of `exportExposureReport`; `error` centralized
  in `showToast(type==="error")`; `export` only after a successful export download.
- MP3s are NOT in the repo — user must add the four files to
  `frontend/static/sounds/`. Coexists with the older synthesized `RetroSoundEngine`.

## Defensive exposure report / export  (app.v17.js)
- `buildExposureReport(data, wmnResults)` builds a NEW object by ALLOWLISTING only
  non-sensitive fields (it never copies `currentInvestigationData`), so sensitive
  data added upstream later cannot leak into exports. Shape:
  `{ subject{email,handle?}, breachExposure[], publicAccounts[], sources[], metadata }`.
  - breachExposure ← `leaks[]` (name/date/type/severity/exposedDataTypes/source/description)
  - publicAccounts ← `currentWMNResults.matches[]` (platform/category/profileUrl/confidence)
- `exposureReportToMarkdown(report)` renders the human-readable form.
- `exportExposureReport(format)` ('json'|'md'): guards empty findings, sanitizes
  filename (`sanitizeFilenamePart`), downloads via `downloadBlob`, plays export cue,
  toasts. Filenames: `exposure_report_<slug>_<YYYY-MM-DD>.{json,md}`.
- UI: "Defensive Exposure Report" buttons in `#target-exposure-card` header
  (`#btn-exposure-json`, `#btn-exposure-md`), visible only when results render.
- This is deliberately NOT the older full-dossier exports
  (`exportInvestigationJSON/CSV/DOC/PDF`) which DO include passwords/addresses and
  live in the hidden `#summary-metrics-banner`.

## Testing notes / gotchas
- Top-level `let currentInvestigationData` is a lexical binding, NOT
  `window.currentInvestigationData`. To drive/inspect from Playwright, use the bare
  name in `page.evaluate`, not `window.`.
- pytest: several tests need live DNS/AI network (egress-blocked here) and fail
  independent of app code.
- Headless: use `/opt/pw-browsers/chromium_headless_shell-1194/.../headless_shell`
  (old `--headless` was removed from the full chrome binary).

## Known limitations / extension points
- `exposed_data` is often empty for seeded infostealer/ecommerce leaks (only
  backfilled for names matching `KNOWN_REAL_BREACHES`); real HIBP-style breaches populate it.
- publicAccounts only populates after a WhatsMyName scan has run.
- Future: PDF export, saved investigations/case files, provenance-per-field — the
  normalized `buildExposureReport` model is the seam to build these on.
