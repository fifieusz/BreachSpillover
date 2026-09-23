import hashlib
from typing import Optional
from backend.database import get_connection

def seed_identity_scenario(
    emp_id: int,
    email: str,
    name: str,
    scenario: str = "full",
    custom_password: Optional[str] = None,
    custom_city: Optional[str] = None,
    custom_street: Optional[str] = None,
    custom_relative: Optional[str] = None
):
    """
    Seeds a deterministic or custom simulation scenario for any identity profile.
    Supports clean (0 leaks), partial (e-commerce breach with password only),
    or full (infostealer malware with exfiltrated credentials, pivots, home address, and household contacts).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Clear previous associated records for this identity
    cursor.execute("DELETE FROM relatives WHERE employee_id = ?", (emp_id,))
    cursor.execute("DELETE FROM physical_footprints WHERE employee_id = ?", (emp_id,))
    cursor.execute("DELETE FROM pivots WHERE employee_id = ?", (emp_id,))
    cursor.execute("DELETE FROM credentials WHERE employee_id = ?", (emp_id,))

    if scenario == "clean":
        conn.commit()
        conn.close()
        return

    h = int(hashlib.md5(email.encode("utf-8")).hexdigest(), 16)
    
    # 1. Stealer leak template
    cursor.execute("SELECT id FROM leaks WHERE leak_type = 'INFOSTEALER' LIMIT 1")
    stealer_row = cursor.fetchone()
    if not stealer_row:
        cursor.execute("""
            INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("LummaC2 Infostealer Campaign #2024-B", "INFOSTEALER", "2024-04-12",
              "Infostealer malware drop containing full browser vaults, session cookies, autofill and network profiles.",
              "Underground Telegram Channel", "CRITICAL"))
        stealer_leak_id = cursor.lastrowid
    else:
        stealer_leak_id = stealer_row[0]

    # 2. E-commerce leak template
    cursor.execute("SELECT id FROM leaks WHERE leak_type = 'ECOMMERCE' LIMIT 1")
    ecom_row = cursor.fetchone()
    if not ecom_row:
        cursor.execute("""
            INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("ShopSphere E-Commerce Customer Database", "ECOMMERCE", "2023-08-19",
              "SQL injection breach on consumer retail store leaking hashed passwords and emails.",
              "BreachForums Dump", "HIGH"))
        ecom_leak_id = cursor.lastrowid
    else:
        ecom_leak_id = ecom_row[0]

    # 3. Delivery leak template
    cursor.execute("SELECT id FROM leaks WHERE leak_type = 'DELIVERY' LIMIT 1")
    deliv_row = cursor.fetchone()
    if not deliv_row:
        cursor.execute("""
            INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("QuickBite Delivery Logistics Dump", "DELIVERY", "2022-11-04",
              "Courier delivery database containing recipient names and home addresses.",
              "Darknet Data Broker", "MEDIUM"))
        deliv_leak_id = cursor.lastrowid
    else:
        deliv_leak_id = deliv_row[0]

    first_name = name.split()[0] if name else "User"
    last_name = name.split()[-1] if len(name.split()) > 1 else ""
    phone_middle = f"{100 + (h % 899)}"
    phone_end = f"{10 + ((h >> 4) % 89)}"
    simulated_phone = f"+1 (415) {phone_middle}-{phone_end}1"

    if scenario == "partial":
        pwd_hash = hashlib.md5(f"{email}:pass".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ecom_leak_id, emp_id, email, None, pwd_hash, "MD5 Legacy Hash (unsalted)", 0, "shopsphere.com"))
        
        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (emp_id, ecom_leak_id, "PHONE_NUMBER", simulated_phone, 0.88, "Customer contact phone from online store order profile"))
    
    else:  # "full" scenario
        simulated_pwd = custom_password if custom_password else f"{first_name}2024!"
        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (stealer_leak_id, emp_id, email, simulated_pwd, None, f"Exfiltrated Password: {simulated_pwd}", 1, "mail.corporate-portal.io"))

        cursor.execute("""
            INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ecom_leak_id, emp_id, email, f"{first_name.lower()}99!", None, "Small[4+] + Digits + Special", 0, "shopsphere.com"))

        clean_user = email.split("@")[0]
        sec_email = f"{clean_user}.priv@gmail.com" if not email.endswith("gmail.com") else f"{clean_user}.sec@proton.me"
        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (emp_id, stealer_leak_id, "PERSONAL_EMAIL", sec_email, 0.98, "Secondary Google account logged into Chrome browser vault"))
        pivot_email_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (emp_id, stealer_leak_id, "PHONE_NUMBER", simulated_phone, 0.95, "Mobile phone line recovered from browser autofill cache"))

        cities = ["San Francisco", "New York", "Chicago", "Austin", "London", "Seattle", "Boston"]
        streets = ["Evergreen Terrace", "Market St", "Michigan Ave", "Broadway", "Barton Springs Rd", "Oxford St"]
        city = custom_city if custom_city else cities[h % len(cities)]
        street = custom_street if custom_street else streets[(h >> 2) % len(streets)]
        addr_line = f"{((h % 80) + 1) * 10} {street}, Apt {(h % 20) + 1}"
        post_code = f"94{100 + (h % 800)}"

        cursor.execute("""
            INSERT INTO physical_footprints (employee_id, source_leak_id, pivot_id, address_line, city, postal_code, country, latitude, longitude, exposure_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, deliv_leak_id, pivot_email_id, addr_line, city, post_code, "United States", 37.7749, -122.4194, "RESIDENTIAL_HOME"))
        addr_id = cursor.lastrowid

        rel_first_names = ["Sarah", "Emily", "Michael", "Lucas", "Olivia", "James", "Sophia"]
        rel_name = custom_relative if custom_relative else f"{rel_first_names[(h >> 3) % len(rel_first_names)]} {last_name or 'Morgan'}"
        rel_phone = f"+1 (415) {phone_middle}-{phone_end}5"
        cursor.execute("""
            INSERT INTO relatives (employee_id, source_leak_id, shared_address_id, full_name, relationship, contact_email, contact_phone, social_engineering_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, deliv_leak_id, addr_id, rel_name, "Spouse", f"{rel_first_names[0].lower()}@fastmail.com", rel_phone,
              "Social engineering vector: impersonation of cohabitant to initiate vishing or bypass security verification"))

    conn.commit()
    conn.close()
