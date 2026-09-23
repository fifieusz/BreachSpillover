#!/usr/bin/env python3
"""
BreachSpillover - High-Throughput Local Breach Combolist & Leak Importer
Ingests raw leak dumps, combolists, and CSV breach exports directly into BreachSpillover's local SQLite store.
Automatically maps fields, classifies hash types (MD5, SHA-1, SHA-256, bcrypt), enriches with HIBP catalog metadata,
and indexes credentials for instant sub-millisecond search.
"""

import sys
import os
import re
import csv
import time
import argparse
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Generator

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_path, get_connection
from backend.hibp_catalog import lookup_breach_metadata

# Regex patterns for hash classification
HASH_PATTERNS = [
    (re.compile(r'^\$2[aby]\$[0-9]{2}\$[A-Za-z0-9\./]{53}$'), "bcrypt"),
    (re.compile(r'^\$argon2[id]?\$'), "argon2"),
    (re.compile(r'^\$6\$[A-Za-z0-9\./]{1,16}\$[A-Za-z0-9\./]{86}$'), "sha512crypt"),
    (re.compile(r'^[a-fA-F0-9]{64}$'), "sha256"),
    (re.compile(r'^[a-fA-F0-9]{40}$'), "sha1"),
    (re.compile(r'^[a-fA-F0-9]{32}$'), "md5"),
    (re.compile(r'^[a-fA-F0-9]{16}$'), "half-md5/mysql"),
]

def classify_credential(token: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Classifies whether a token is a plaintext password or a hash.
    Returns: (plaintext_password, password_hash)
    """
    if not token:
        return None, None
    clean = token.strip()
    for pattern, htype in HASH_PATTERNS:
        if pattern.match(clean):
            return None, clean
    return clean, None

def parse_line_delimiter(line: str) -> Optional[Dict[str, str]]:
    """
    Auto-detects colon, semicolon, pipe, or tab delimited formats.
    Supported patterns:
      1. email:password
      2. email:hash
      3. user:email:password
      4. email:password:hash
      5. email:password:hash:salt
    """
    clean_line = line.strip()
    if not clean_line or clean_line.startswith("#"):
        return None

    # Detect delimiter
    delim = None
    for d in [":", ";", "|", "\t"]:
        if d in clean_line:
            delim = d
            break
    if not delim:
        return None

    parts = [p.strip() for p in clean_line.split(delim)]
    if len(parts) < 2:
        return None

    email_idx = -1
    for i, p in enumerate(parts):
        if "@" in p and "." in p and not re.search(r'\s', p):
            email_idx = i
            break

    if email_idx == -1:
        return None

    email = parts[email_idx].lower()
    
    plain, chash = None, None
    username = None

    if email_idx > 0:
        # Format: user:email:credential or user:email:pass:hash
        username = parts[0]
        post_tokens = parts[email_idx + 1:]
        if len(post_tokens) == 1:
            plain, chash = classify_credential(post_tokens[0])
        elif len(post_tokens) >= 2:
            p0, h0 = classify_credential(post_tokens[0])
            p1, h1 = classify_credential(post_tokens[1])
            plain = p0 if not h0 else (p1 if not h1 else None)
            chash = h1 if h1 else h0
    else:
        # Format: email:credential or email:pass:hash
        username = email.split("@")[0]
        post_tokens = parts[1:]
        if len(post_tokens) == 1:
            plain, chash = classify_credential(post_tokens[0])
        elif len(post_tokens) >= 2:
            p0, h0 = classify_credential(post_tokens[0])
            p1, h1 = classify_credential(post_tokens[1])
            plain = p0 if not h0 else None
            chash = h1 if h1 else (h0 if h0 else None)

    return {
        "email": email,
        "username": username or email.split("@")[0],
        "plaintext": plain,
        "hash": chash
    }

def stream_file_records(file_path: str) -> Generator[Dict[str, str], None, None]:
    """Streams records line-by-line supporting delimiter files and standard CSVs."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        # Check first line for CSV header
        first_pos = f.tell()
        sample = f.readline()
        f.seek(first_pos)

        # Check if standard CSV with header
        if "," in sample and any(h in sample.lower() for h in ["email", "e-mail", "mail"]):
            reader = csv.DictReader(f)
            for row in reader:
                # Find email column
                em = None
                for k, v in row.items():
                    if k and ("email" in k.lower() or "mail" in k.lower()):
                        em = v.strip().lower() if v else None
                        break
                if not em or "@" not in em:
                    continue

                pw = row.get("password") or row.get("pass") or row.get("plaintext") or ""
                phash = row.get("hash") or row.get("password_hash") or ""
                p_out, h_out = classify_credential(pw)
                if phash and not h_out:
                    h_out = phash.strip()

                yield {
                    "email": em,
                    "username": row.get("username") or em.split("@")[0],
                    "plaintext": p_out,
                    "hash": h_out
                }
            return

        # Otherwise parse line-by-line
        for line in f:
            rec = parse_line_delimiter(line)
            if rec:
                yield rec

def import_combolist(
    file_path: str,
    leak_name: str,
    leak_type: str = "DATABASE_LEAK",
    breach_date: Optional[str] = None,
    source: str = "Local Combolist Ingestion",
    batch_size: int = 5000
) -> Dict[str, Any]:
    """
    High-speed batch ingestion of combolists into BreachSpillover SQLite store.
    Uses SQLite WAL transactions for maximum write throughput (>50k rows/sec).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1. Enrich breach metadata via HIBP master catalog
    hibp_meta = lookup_breach_metadata(leak_name)
    final_name = leak_name
    final_date = breach_date or "2024-01-01"
    final_desc = f"Imported breach database from {os.path.basename(file_path)}."
    final_sev = "HIGH"

    if hibp_meta:
        final_name = hibp_meta["title"]
        final_date = breach_date or hibp_meta["breach_date"]
        final_desc = hibp_meta["description"]
        final_sev = hibp_meta["severity"]
        print(f"[+] HIBP Encyclopedia Match: {final_name} ({final_date}) [Severity: {final_sev}]")

    conn = get_connection()
    cursor = conn.cursor()

    # Create or get leak_id
    cursor.execute("""
        INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (final_name, leak_type, final_date, final_desc, source, final_sev))
    leak_id = cursor.lastrowid

    total_records = 0
    total_hashes = 0
    total_plains = 0
    unique_emails = set()

    cred_batch = []
    emp_cache = {} # email -> emp_id

    # Pre-cache existing employees
    cursor.execute("SELECT corporate_email, id FROM employees")
    for r in cursor.fetchall():
        emp_cache[r[0].lower()] = r[1]

    t0 = time.time()
    print(f"[*] Beginning streaming ingestion of '{file_path}' into Leak ID #{leak_id}...")

    def flush_batch():
        nonlocal cred_batch
        if not cred_batch:
            return
        cursor.executemany("""
            INSERT INTO credentials (
                leak_id, employee_id, username_or_email,
                plaintext_password, password_hash, password_pattern,
                is_corporate_password_match, domain_compromised
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, cred_batch)
        conn.commit()
        cred_batch = []

    for rec in stream_file_records(file_path):
        em = rec["email"]
        plain = rec["plaintext"]
        chash = rec["hash"]

        # Ensure employee row exists
        if em not in emp_cache:
            uname = rec.get("username") or em.split("@")[0]
            # Format clean full name
            full_name = " ".join([w.capitalize() for w in re.split(r'[\._\-+]', uname) if w]) or uname
            cursor.execute("""
                INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, em, "Indexed Target", "External Service", "Individual", uname))
            emp_id = cursor.lastrowid
            emp_cache[em] = emp_id
        else:
            emp_id = emp_cache[em]

        pattern_desc = None
        if plain:
            total_plains += 1
            if len(plain) >= 8 and any(c.isupper() for c in plain) and any(c.isdigit() for c in plain):
                pattern_desc = "Complex AlphaNumeric"
            elif plain.isdigit():
                pattern_desc = "Numeric PIN"
            else:
                pattern_desc = "Standard Passphrase"
        if chash:
            total_hashes += 1

        domain_comp = em.split("@")[-1] if "@" in em else "unknown.com"

        cred_batch.append((
            leak_id, emp_id, em,
            plain, chash, pattern_desc,
            0, domain_comp
        ))

        unique_emails.add(em)
        total_records += 1

        if len(cred_batch) >= batch_size:
            flush_batch()
            sys.stdout.write(f"\r -> Ingested {total_records:,} records ({len(unique_emails):,} unique targets)...")
            sys.stdout.flush()

    flush_batch()
    elapsed = max(time.time() - t0, 0.001)
    rate = total_records / elapsed

    print(f"\n[+] Ingestion Complete in {elapsed:.2f}s ({rate:,.0f} records/sec)")
    print(f"    * Total Credentials: {total_records:,}")
    print(f"    * Unique Identities: {len(unique_emails):,}")
    print(f"    * Plaintext Passwords: {total_plains:,}")
    print(f"    * Cryptographic Hashes: {total_hashes:,}")

    return {
        "leak_id": leak_id,
        "leak_name": final_name,
        "total_records": total_records,
        "unique_emails": len(unique_emails),
        "total_plains": total_plains,
        "total_hashes": total_hashes,
        "elapsed_sec": round(elapsed, 2)
    }

def import_combolist_text(
    raw_text: str,
    leak_name: str,
    leak_type: str = "DATABASE_LEAK",
    breach_date: Optional[str] = None,
    source: str = "Web UI Ingestion",
    batch_size: int = 2000
) -> Dict[str, Any]:
    """
    Direct in-memory / paste ingestion of combolist lines (email:pass, user:email:pass, etc.)
    for dashboard drag-and-drop and manual paste imports.
    """
    hibp_meta = lookup_breach_metadata(leak_name)
    final_name = leak_name
    final_date = breach_date or "2024-01-01"
    final_desc = f"Imported breach database via Web UI Combolist Ingestion."
    final_sev = "HIGH"

    if hibp_meta:
        final_name = hibp_meta["title"]
        final_date = breach_date or hibp_meta["breach_date"]
        final_desc = hibp_meta["description"]
        final_sev = hibp_meta["severity"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (final_name, leak_type, final_date, final_desc, source, final_sev))
    leak_id = cursor.lastrowid

    total_records = 0
    total_hashes = 0
    total_plains = 0
    unique_emails = set()

    cred_batch = []
    emp_cache = {}

    cursor.execute("SELECT corporate_email, id FROM employees")
    for r in cursor.fetchall():
        emp_cache[r[0].lower()] = r[1]

    t0 = time.time()

    def flush_batch():
        nonlocal cred_batch
        if not cred_batch:
            return
        cursor.executemany("""
            INSERT INTO credentials (
                leak_id, employee_id, username_or_email,
                plaintext_password, password_hash, password_pattern,
                is_corporate_password_match, domain_compromised
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, cred_batch)
        conn.commit()
        cred_batch = []

    for line in raw_text.splitlines():
        rec = parse_line_delimiter(line)
        if not rec:
            continue
        em = rec["email"]
        plain = rec["plaintext"]
        chash = rec["hash"]

        if em not in emp_cache:
            uname = rec.get("username") or em.split("@")[0]
            full_name = " ".join([w.capitalize() for w in re.split(r'[\._\-+]', uname) if w]) or uname
            cursor.execute("""
                INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, em, "Indexed Target", "External Service", "Individual", uname))
            emp_id = cursor.lastrowid
            emp_cache[em] = emp_id
        else:
            emp_id = emp_cache[em]

        pattern_desc = None
        if plain:
            total_plains += 1
            if len(plain) >= 8 and any(c.isupper() for c in plain) and any(c.isdigit() for c in plain):
                pattern_desc = "Complex AlphaNumeric"
            elif plain.isdigit():
                pattern_desc = "Numeric PIN"
            else:
                pattern_desc = "Standard Passphrase"
        if chash:
            total_hashes += 1

        domain_comp = em.split("@")[-1] if "@" in em else "unknown.com"

        cred_batch.append((
            leak_id, emp_id, em,
            plain, chash, pattern_desc,
            0, domain_comp
        ))
        unique_emails.add(em)
        total_records += 1

        if len(cred_batch) >= batch_size:
            flush_batch()

    flush_batch()
    elapsed = max(time.time() - t0, 0.001)
    rate = total_records / elapsed
    conn.close()

    return {
        "success": True,
        "leak_id": leak_id,
        "leak_name": final_name,
        "total_records": total_records,
        "unique_emails": len(unique_emails),
        "total_plains": total_plains,
        "total_hashes": total_hashes,
        "elapsed_sec": round(elapsed, 2),
        "records_per_sec": round(rate, 1)
    }

def main():
    parser = argparse.ArgumentParser(description="BreachSpillover High-Speed Combolist & Breach Importer")
    parser.add_argument("file", help="Path to raw leak file (.txt, .csv, .tsv)")
    parser.add_argument("--name", default=None, help="Name of data breach (matches against HIBP 1,000-breach catalog)")
    parser.add_argument("--type", default="DATABASE_LEAK", help="Leak category (DATABASE_LEAK, INFOSTEALER, COMBO_LIST, VPN)")
    parser.add_argument("--date", default=None, help="Breach date (YYYY-MM-DD)")
    parser.add_argument("--source", default="Local Ingestion", help="Threat actor or intelligence origin")
    args = parser.parse_args()

    default_name = args.name or Path(args.file).stem.replace("_", " ").title()
    import_combolist(
        file_path=args.file,
        leak_name=default_name,
        leak_type=args.type,
        breach_date=args.date,
        source=args.source
    )

if __name__ == "__main__":
    main()
