import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import re


BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "breach_spillover.db"

def get_db_path() -> Path:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH

def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the SQLite schema with foreign keys and performance indexes."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        corporate_email TEXT UNIQUE NOT NULL,
        job_title TEXT NOT NULL,
        department TEXT NOT NULL,
        vip_level TEXT NOT NULL, -- C-Level, VP, Senior Staff, Developer, Individual
        avatar_seed TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS leaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leak_name TEXT NOT NULL,
        leak_type TEXT NOT NULL, -- INFOSTEALER, ECOMMERCE, DELIVERY, FITNESS_APP, VPN, FORUM
        breach_date TEXT NOT NULL,
        description TEXT,
        threat_actor_source TEXT,
        severity TEXT NOT NULL -- CRITICAL, HIGH, MEDIUM, LOW
    );

    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leak_id INTEGER NOT NULL,
        employee_id INTEGER,
        username_or_email TEXT NOT NULL,
        plaintext_password TEXT,
        password_hash TEXT,
        password_pattern TEXT, -- e.g. "TitleCase + Year + SpecialChar (P*****2024!)"
        is_corporate_password_match BOOLEAN DEFAULT 0,
        domain_compromised TEXT, -- e.g. vpn.cybercorp.io, mail.cybercorp.io, google.com
        FOREIGN KEY (leak_id) REFERENCES leaks(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS pivots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        source_leak_id INTEGER,
        pivot_type TEXT NOT NULL, -- PERSONAL_EMAIL, PHONE_NUMBER, MACHINE_HWID, IP_ADDRESS
        pivot_value TEXT NOT NULL,
        confidence_score REAL DEFAULT 1.0,
        context_note TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (source_leak_id) REFERENCES leaks(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS physical_footprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        source_leak_id INTEGER,
        pivot_id INTEGER,
        address_line TEXT NOT NULL,
        city TEXT NOT NULL,
        postal_code TEXT NOT NULL,
        country TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        exposure_type TEXT DEFAULT 'RESIDENTIAL_HOME', -- RESIDENTIAL_HOME, SECONDARY_RESIDENCE
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (source_leak_id) REFERENCES leaks(id) ON DELETE SET NULL,
        FOREIGN KEY (pivot_id) REFERENCES pivots(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS relatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        source_leak_id INTEGER,
        shared_address_id INTEGER,
        full_name TEXT NOT NULL,
        relationship TEXT NOT NULL, -- Spouse, Partner, Child, Parent, Sibling
        contact_email TEXT,
        contact_phone TEXT,
        social_engineering_risk TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (source_leak_id) REFERENCES leaks(id) ON DELETE SET NULL,
        FOREIGN KEY (shared_address_id) REFERENCES physical_footprints(id) ON DELETE SET NULL
    );

    -- Optimized Indexes for Fast Relational Lookups
    CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(corporate_email);
    CREATE INDEX IF NOT EXISTS idx_credentials_emp ON credentials(employee_id);
    CREATE INDEX IF NOT EXISTS idx_credentials_leak ON credentials(leak_id);
    CREATE INDEX IF NOT EXISTS idx_credentials_user ON credentials(username_or_email);
    CREATE INDEX IF NOT EXISTS idx_pivots_emp ON pivots(employee_id);
    CREATE INDEX IF NOT EXISTS idx_pivots_val ON pivots(pivot_value);
    CREATE INDEX IF NOT EXISTS idx_physical_emp ON physical_footprints(employee_id);
    CREATE INDEX IF NOT EXISTS idx_relatives_emp ON relatives(employee_id);
    CREATE INDEX IF NOT EXISTS idx_credentials_hash ON credentials(password_hash);
    CREATE INDEX IF NOT EXISTS idx_credentials_plain ON credentials(plaintext_password);
    """)

    # Schema enhancements for multi-source OSINT & infostealer provenance
    for col_table, col_name, col_type in [
        ("leaks", "malware_family", "TEXT"),
        ("leaks", "antivirus_bypassed", "TEXT"),
        ("leaks", "compromised_date", "TEXT"),
        ("leaks", "exposed_data", "TEXT"),
        ("credentials", "global_frequency", "INTEGER DEFAULT 0")
    ]:
        try:
            cursor.execute(f"ALTER TABLE {col_table} ADD COLUMN {col_name} {col_type};")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

COMMON_FIRST_NAMES = {
    # Western & Anglo-American
    "jordin", "jordan", "filip", "phillip", "philip", "alex", "alexander", "david",
    "john", "michael", "mike", "lucas", "luka", "thomas", "daniel", "dan", "robert",
    "peter", "mark", "kevin", "brian", "jason", "eric", "erik", "lisa", "anna",
    "maria", "emma", "sophia", "olivia", "james", "william", "benjamin", "samuel",
    "nathan", "niels", "lars", "sander", "stefan", "bram", "thijs", "daan", "tim",
    "tom", "max", "ruben", "julian", "milan", "luuk", "mees", "gijs", "teun",
    "adam", "oliver", "henry", "george", "charles", "richard", "joseph", "sam",
    "paul", "steven", "anthony", "andrew", "edward", "harry", "jack", "noah",
    # Middle Eastern & Arabic & Islamic
    "yasir", "yasser", "ashraf", "kadim", "kadhim", "ali", "omar", "mohammed", "mohamed",
    "muhammad", "ahmed", "ahmad", "hassan", "hussein", "tariq", "tarik", "kareem",
    "karim", "mustafa", "mahmoud", "ibrahim", "youssef", "yousef", "bilal", "hamza",
    "khalid", "walid", "ziad", "zaid", "samir", "rami", "nabil", "fadi", "amr",
    # Slavic & Eastern European
    "mateusz", "piotr", "krzysztof", "pawel", "michal", "jan", "jakub", "marcin",
    "tomasz", "andrzej", "stanislaw", "wojciech", "lukasz", "grzegorz", "dmitry",
    "alexei", "sergey", "ivan", "vladimir", "igor", "mikhail", "nikolay", "artem",
    # Nordic & Scandinavian
    "ole", "per", "knut", "sven", "magnus", "henrik", "jonas", "espen", "morten",
    "bjorn", "tor", "geir", "rune", "arild", "frode", "oyvind", "einar",
    # Southern European & Latin
    "carlos", "luis", "juan", "miguel", "antonio", "pedro", "manuel", "jose",
    "marco", "matteo", "luca", "francesco", "alessandro", "giovanni", "andrea"
}

def parse_name_from_email(email: str) -> str:
    cleaned = email.strip().lower()
    local = cleaned.split("@")[0]
    parts = re.split(r'[._\-\+\d]+', local)
    parts = [p.capitalize() for p in parts if len(p) >= 2]
    if len(parts) >= 2:
        return " ".join(parts)
    elif len(parts) == 1:
        single = parts[0].lower()
        # Test if single word starts with a known first name (e.g. jordinzwaan -> Jordin Zwaan, yasirkadhim -> Yasir Kadhim)
        for fn in sorted(COMMON_FIRST_NAMES, key=lambda x: -len(x)):
            if single.startswith(fn) and len(single) > len(fn) + 1:
                sur = single[len(fn):]
                if not sur.isdigit() and len(sur) >= 2:
                    # Ignore short diminutive endings like 'os' in 'filipos'
                    if sur in ["os", "ek", "ik", "ka", "io", "ie", "y"]:
                        return fn.capitalize()
                    return f"{fn.capitalize()} {sur.capitalize()}"
        return parts[0]
    return local.capitalize() or "Target User"



DEMO_EMAILS = {
    "alex.morgan@cybercorp.io",
    "elena.rostova@cybercorp.io",
    "marcus.vance@cybercorp.io",
    "sarah.jenkins@gmail.com",
    "david.miller@proton.me",
    "emily.watson@cybercorp.io",
    "james.cooper@cybercorp.io",
    "olivia.chen@cybercorp.io"
}

def get_or_create_identity_profile(
    email: str,
    scenario: Optional[str] = None,
    custom_password: Optional[str] = None,
    custom_city: Optional[str] = None,
    custom_street: Optional[str] = None,
    custom_relative: Optional[str] = None,
    anchors: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Retrieves an existing identity profile or creates a new one.
    For standard user searches (non-demo emails):
    - Automatically executes live OSINT and verified threat disclosures.
    - Strictly factual: never invents fake addresses, phone numbers, or spouses.
    - If unbreached, returns 100% clean profile (0/100 score).
    """
    cleaned_email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE LOWER(corporate_email) = LOWER(?)", (cleaned_email,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("SELECT employee_id FROM pivots WHERE LOWER(pivot_value) = LOWER(?)", (cleaned_email,))
        p_row = cursor.fetchone()
        if p_row:
            cursor.execute("SELECT * FROM employees WHERE id = ?", (p_row["employee_id"],))
            row = cursor.fetchone()

    if not row:
        name = parse_name_from_email(cleaned_email)
        domain = cleaned_email.split("@")[1] if "@" in cleaned_email else "local"
        profile_type = "Personal Account" if any(d in domain for d in ["gmail", "yahoo", "outlook", "hotmail", "proton", "icloud", "zoho", "mail"]) else "Corporate Identity"
        
        cursor.execute("""
            INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, cleaned_email, profile_type, f"Domain @{domain}", "Standard / Individual", name.lower().replace(" ", "_")))
        emp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        has_custom = any([custom_password, custom_city, custom_street, custom_relative])
        if scenario in ["clean", "partial", "full"] or has_custom:
            from backend.seeder import seed_identity_scenario
            seed_identity_scenario(
                emp_id, cleaned_email, name, scenario or "full",
                custom_password=custom_password,
                custom_city=custom_city,
                custom_street=custom_street,
                custom_relative=custom_relative
            )
            return get_employee_by_id(emp_id)

        # Automatic live OSINT & verified breach detection (e.g. Suno, Canva, XposedOrNot)
        if scenario != "clean":
            from backend.osint_scanner import scan_email_breaches, ingest_breaches_to_profile
            breaches = scan_email_breaches(cleaned_email)
            conn_b = get_connection()
            cur_b = conn_b.cursor()
            ingest_breaches_to_profile(cur_b, emp_id, cleaned_email, name, breaches, anchors=anchors)
            conn_b.commit()
            conn_b.close()

        return get_employee_by_id(emp_id)
    else:
        emp_id = row["id"]
        current_name = row["full_name"] or ""
        parsed_better = parse_name_from_email(cleaned_email)
        name_to_use = current_name
        should_update_name = False

        anchor_name = (anchors.get("known_name") or "") if anchors else ""
        if anchor_name and anchor_name.strip() and anchor_name.strip() not in ["Target User", "Webmail Target"] and anchor_name.strip() != current_name:
            name_to_use = anchor_name.strip()
            should_update_name = True
        elif any(char.isdigit() for char in current_name) and not any(char.isdigit() for char in parsed_better):
            name_to_use = parsed_better
            should_update_name = True
        elif (" " not in current_name or current_name.lower().startswith("webmail") or current_name == "Target User") and (" " in parsed_better):
            name_to_use = parsed_better
            should_update_name = True

        if should_update_name:
            cursor.execute("UPDATE employees SET full_name = ? WHERE id = ?", (name_to_use, emp_id))
            conn.commit()
        conn.close()
        
        has_custom = any([custom_password, custom_city, custom_street, custom_relative])
        if scenario in ["clean", "partial", "full"] or has_custom:
            from backend.seeder import seed_identity_scenario
            actual_scenario = scenario or "full"
            seed_identity_scenario(
                emp_id, cleaned_email, name_to_use, actual_scenario,
                custom_password=custom_password,
                custom_city=custom_city,
                custom_street=custom_street,
                custom_relative=custom_relative
            )
            return get_employee_by_id(emp_id)

        # For any non-demo email, refresh live OSINT intelligence on search
        if cleaned_email not in DEMO_EMAILS and scenario != "clean":
            from backend.osint_scanner import scan_email_breaches, ingest_breaches_to_profile
            breaches = scan_email_breaches(cleaned_email)
            conn_b = get_connection()
            cur_b = conn_b.cursor()
            ingest_breaches_to_profile(cur_b, emp_id, cleaned_email, name_to_use, breaches, anchors=anchors)
            conn_b.commit()
            conn_b.close()
            return get_employee_by_id(emp_id)

        return dict(row)

def reset_identity_profile(email: str) -> Dict[str, Any]:
    """Clears all breach records for an identity and restores clean status (0 score)."""
    from backend.seeder import seed_identity_scenario
    cleaned_email = email.strip().lower()
    profile = get_or_create_identity_profile(cleaned_email, scenario="clean")
    seed_identity_scenario(profile["id"], cleaned_email, profile["full_name"], scenario="clean")
    return get_employee_by_id(profile["id"])

def get_all_employees() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, 
            (SELECT COUNT(*) FROM credentials c WHERE c.employee_id = e.id) as creds_count,
            (SELECT COUNT(DISTINCT l.id) FROM leaks l 
             JOIN credentials c ON c.leak_id = l.id 
             WHERE c.employee_id = e.id) as direct_leaks_count,
            (SELECT COUNT(*) FROM physical_footprints pf WHERE pf.employee_id = e.id) as address_count,
            (SELECT COUNT(*) FROM relatives r WHERE r.employee_id = e.id) as relatives_count
        FROM employees e
        ORDER BY e.id ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_employee_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE LOWER(corporate_email) = LOWER(?)", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_employee_by_id(emp_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_employee_credentials(emp_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, l.leak_name, l.breach_date, l.leak_type, l.severity 
        FROM credentials c
        JOIN leaks l ON c.leak_id = l.id
        WHERE c.employee_id = ?
        ORDER BY l.breach_date DESC
    """, (emp_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_employee_leaks(emp_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT l.* FROM leaks l
        LEFT JOIN credentials c ON c.leak_id = l.id AND c.employee_id = ?
        LEFT JOIN pivots p ON p.source_leak_id = l.id AND p.employee_id = ?
        LEFT JOIN physical_footprints pf ON pf.source_leak_id = l.id AND pf.employee_id = ?
        LEFT JOIN relatives r ON r.source_leak_id = l.id AND r.employee_id = ?
        WHERE c.id IS NOT NULL OR p.id IS NOT NULL OR pf.id IS NOT NULL OR r.id IS NOT NULL
        ORDER BY l.breach_date DESC
    """, (emp_id, emp_id, emp_id, emp_id))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_employee_pivots(emp_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, l.leak_name, l.leak_type 
        FROM pivots p
        LEFT JOIN leaks l ON p.source_leak_id = l.id
        WHERE p.employee_id = ?
    """, (emp_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_employee_footprints(emp_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pf.*, l.leak_name 
        FROM physical_footprints pf
        LEFT JOIN leaks l ON pf.source_leak_id = l.id
        WHERE pf.employee_id = ?
    """, (emp_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_employee_relatives(emp_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, pf.city, pf.address_line, l.leak_name 
        FROM relatives r
        LEFT JOIN physical_footprints pf ON r.shared_address_id = pf.id
        LEFT JOIN leaks l ON r.source_leak_id = l.id
        WHERE r.employee_id = ?
    """, (emp_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_global_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leaks")
    total_leaks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leaks WHERE leak_type = 'INFOSTEALER'")
    stealer_leaks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM physical_footprints")
    exposed_addresses = cursor.fetchone()[0]
    conn.close()
    return {
        "total_employees": total_employees,
        "total_leaks": total_leaks,
        "stealer_leaks": stealer_leaks,
        "exposed_physical_addresses": exposed_addresses
    }

def get_employees_by_domain(domain: str) -> List[Dict[str, Any]]:
    """
    EmploLeaks Corporate Directory Module:
    Retrieves all indexed company employees associated with a corporate domain.
    """
    conn = get_connection()
    cursor = conn.cursor()
    clean_dom = domain.strip().lower().lstrip("@")
    cursor.execute("""
        SELECT e.*, 
            (SELECT COUNT(*) FROM credentials c WHERE c.employee_id = e.id) as creds_count,
            (SELECT COUNT(DISTINCT l.id) FROM leaks l 
             JOIN credentials c ON c.leak_id = l.id 
             WHERE c.employee_id = e.id) as direct_leaks_count
        FROM employees e
        WHERE LOWER(e.corporate_email) LIKE ?
        ORDER BY e.vip_level DESC, e.id ASC
    """, (f"%@{clean_dom}",))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_cross_target_correlations(employee_id: int) -> Dict[str, Any]:
    """
    Identifies cross-target identity correlations across the database:
    1. Shared Passwords / Hashes (lateral movement rings)
    2. Shared Residential Addresses (household / physical proximity)
    3. Shared Pivot Points (phone lines or secondary emails)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Shared Credentials
    cursor.execute("""
        SELECT DISTINCT 
            c2.employee_id as target_id,
            e.full_name,
            e.corporate_email,
            c1.password_hash,
            c1.plaintext_password,
            l.leak_name
        FROM credentials c1
        JOIN credentials c2 ON (
            (c1.password_hash IS NOT NULL AND c1.password_hash != '' AND c1.password_hash = c2.password_hash)
            OR
            (c1.plaintext_password IS NOT NULL AND c1.plaintext_password != '' AND LOWER(c1.plaintext_password) = LOWER(c2.plaintext_password))
        ) AND c1.employee_id != c2.employee_id
        JOIN employees e ON e.id = c2.employee_id
        LEFT JOIN leaks l ON c2.leak_id = l.id
        WHERE c1.employee_id = ?
    """, (employee_id,))
    shared_creds = [dict(r) for r in cursor.fetchall()]

    # 2. Shared Physical Addresses
    cursor.execute("""
        SELECT DISTINCT 
            pf2.employee_id as target_id,
            e.full_name,
            e.corporate_email,
            pf1.address_line,
            pf1.city
        FROM physical_footprints pf1
        JOIN physical_footprints pf2 ON LOWER(pf1.address_line) = LOWER(pf2.address_line) AND pf1.employee_id != pf2.employee_id
        JOIN employees e ON e.id = pf2.employee_id
        WHERE pf1.employee_id = ?
    """, (employee_id,))
    shared_addresses = [dict(r) for r in cursor.fetchall()]

    # 3. Shared Identity Pivots (e.g. Phone, Secondary Inboxes)
    cursor.execute("""
        SELECT DISTINCT 
            p2.employee_id as target_id,
            e.full_name,
            e.corporate_email,
            p1.pivot_type,
            p1.pivot_value
        FROM pivots p1
        JOIN pivots p2 ON LOWER(p1.pivot_value) = LOWER(p2.pivot_value) AND p1.employee_id != p2.employee_id
        JOIN employees e ON e.id = p2.employee_id
        WHERE p1.employee_id = ? AND p1.pivot_type IN ('PHONE_NUMBER', 'PERSONAL_EMAIL', 'ALTERNATIVE_EMAIL', 'DISCOVERED_PHONE')
    """, (employee_id,))
    shared_pivots = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "shared_credentials": shared_creds,
        "shared_addresses": shared_addresses,
        "shared_pivots": shared_pivots,
        "total_correlations": len(shared_creds) + len(shared_addresses) + len(shared_pivots)
    }

