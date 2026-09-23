import sqlite3
from pathlib import Path
import sys

# Ensure backend package can be imported
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_connection, init_db

def seed_database():
    print("[*] Initializing database schema...")
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data to ensure idempotent seeding
    cursor.executescript("""
        DELETE FROM relatives;
        DELETE FROM physical_footprints;
        DELETE FROM pivots;
        DELETE FROM credentials;
        DELETE FROM leaks;
        DELETE FROM employees;
    """)

    print("[*] Seeding sample target identities...")
    employees_data = [
        ("Alex Morgan", "alex.morgan@cybercorp.io", "Chief Technology Officer", "Executive / Engineering", "C-Level", "alex_morgan"),
        ("Elena Rostova", "elena.rostova@cybercorp.io", "VP of Global Finance", "Executive / Finance", "VP", "elena_rostova"),
        ("Marcus Vance", "marcus.vance@cybercorp.io", "Principal Cloud & DevOps Architect", "Infrastructure & SecOps", "Senior Staff", "marcus_vance"),
        ("Sarah Jenkins", "sarah.jenkins@gmail.com", "Private Individual", "Personal Identity", "Individual", "sarah_jenkins"),
        ("David Miller", "david.miller@proton.me", "Senior Software Engineer", "Core Platform", "Senior Engineer", "david_miller"),
        ("Emily Watson", "emily.watson@cybercorp.io", "Enterprise Account Director", "Sales & Partnerships", "Director", "emily_watson"),
        ("James Cooper", "james.cooper@cybercorp.io", "Junior QA Automation Engineer", "Quality Assurance", "Junior", "james_cooper"),
        ("Olivia Chen", "olivia.chen@cybercorp.io", "Security Analyst (Clean Identity)", "Cyber Defense & Blue Team", "Analyst", "olivia_chen"),
    ]

    cursor.executemany("""
        INSERT INTO employees (full_name, corporate_email, job_title, department, vip_level, avatar_seed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, employees_data)

    emp_ids = {}
    for row in cursor.execute("SELECT corporate_email, id FROM employees"):
        emp_ids[row[0]] = row[1]

    print("[*] Seeding threat intelligence leaks and infostealer malware dumps...")
    leaks_data = [
        # id=1
        ("LummaC2 Infostealer Campaign #2024-B", "INFOSTEALER", "2024-04-12", 
         "Infostealer malware drop containing full browser vaults, session cookies, autofill and network profiles.", 
         "Telegram Underground / Darknet Market", "CRITICAL"),
        # id=2
        ("ShopSphere E-Commerce Customer Database", "ECOMMERCE", "2023-08-19",
         "SQL injection breach on major consumer retailer leaking hashed passwords, phone numbers and customer emails.",
         "BreachForums Dump", "HIGH"),
        # id=3
        ("QuickBite Delivery Logistics Dump", "DELIVERY", "2022-11-04",
         "Exposed Elasticsearch cluster containing courier delivery drop addresses, order notes and recipient phone numbers.",
         "Darknet Data Broker", "MEDIUM"),
        # id=4
        ("RedLine Stealer Enterprise Botnet #7819", "INFOSTEALER", "2024-02-18",
         "Stealer-infected endpoint exfiltrating VPN credentials, browser sessions and internal corporate URLs.",
         "RedLine C2 Panel Exfiltration", "CRITICAL"),
        # id=5
        ("PetCare Online Superstore Leak", "ECOMMERCE", "2023-05-10",
         "API misconfiguration exposing customer profiles, order delivery details and contact numbers.",
         "Public Breach Archive", "MEDIUM"),
        # id=6
        ("GlobalTelecom Subscriber Directory", "ECOMMERCE", "2022-09-15",
         "Telecom provider credential and subscriber directory dump with phone numbers and billing addresses.",
         "Underground Telegram Channel", "HIGH"),
        # id=7
        ("Vidar Stealer Malware Drop #91", "INFOSTEALER", "2024-01-20",
         "Vidar stealer malware logs targeting developers, browser passwords, Discord tokens and AWS config files.",
         "Vidar Operator Channel", "CRITICAL"),
        # id=8
        ("UltraHardware Tech Store 2023", "ECOMMERCE", "2023-03-14",
         "E-commerce database breach with shipping addresses and contact details of hardware enthusiasts.",
         "Hacker Forum Dump", "HIGH"),
    ]

    cursor.executemany("""
        INSERT INTO leaks (leak_name, leak_type, breach_date, description, threat_actor_source, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, leaks_data)

    leak_ids = {}
    for row in cursor.execute("SELECT leak_name, id FROM leaks"):
        leak_ids[row[0]] = row[1]

    print("[*] Seeding Credentials, Pivots, Physical Footprints and Relatives...")

    # =========================================================================
    # 1. ALEX MORGAN (CTO) - CRITICAL SPILLOVER SCORE (95/100)
    # Infostealer -> Cleartext Password -> Private Email/Phone -> Home Address -> Family
    # =========================================================================
    am_id = emp_ids["alex.morgan@cybercorp.io"]
    l_lumma = leak_ids["LummaC2 Infostealer Campaign #2024-B"]
    l_shop = leak_ids["ShopSphere E-Commerce Customer Database"]
    l_food = leak_ids["QuickBite Delivery Logistics Dump"]

    cursor.execute("""
        INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (l_lumma, am_id, "alex.morgan@cybercorp.io", "Morgan2024!", None, "TitleCase[6] + Year[4] + Special", 1, "vpn.cybercorp.io"))

    cursor.execute("""
        INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (l_shop, am_id, "alex.morgan.priv@gmail.com", "AlexM!2023", None, "TitleCase[5] + Special + Year[4]", 1, "shopsphere.com"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (am_id, l_lumma, "PERSONAL_EMAIL", "alex.morgan.priv@gmail.com", 0.98, "Logged-in Google Chrome browser session profile extracted from LummaC2 vault"))
    p_am_email = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (am_id, l_lumma, "PHONE_NUMBER", "+1 (415) 892-4190", 0.95, "Personal mobile number recovered from browser checkout autofill store"))
    p_am_phone = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (am_id, l_lumma, "MACHINE_HWID", "DESKTOP-AM-WIN11-9A82F", 1.0, "Motherboard UUID and hostname of victim executive work-from-home rig"))

    cursor.execute("""
        INSERT INTO physical_footprints (employee_id, source_leak_id, pivot_id, address_line, city, postal_code, country, latitude, longitude, exposure_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (am_id, l_food, p_am_email, "742 Evergreen Terrace, Apt 4B", "San Francisco", "94107", "United States", 37.7749, -122.4194, "RESIDENTIAL_HOME"))
    am_addr_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO relatives (employee_id, source_leak_id, shared_address_id, full_name, relationship, contact_email, contact_phone, social_engineering_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (am_id, l_food, am_addr_id, "Sarah Morgan", "Spouse", "sarah.morgan.design@gmail.com", "+1 (415) 892-4195", 
          "High vishing risk: impersonation of spouse calling Corporate IT Helpdesk to request MFA token resets"))

    cursor.execute("""
        INSERT INTO relatives (employee_id, source_leak_id, shared_address_id, full_name, relationship, contact_email, contact_phone, social_engineering_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (am_id, l_food, am_addr_id, "Lucas Morgan", "Child", "lucas.m@sfusd.edu", "+1 (415) 892-4199",
          "Family emergency extortion / urgent SMS scam vector exploiting parental concern"))

    # =========================================================================
    # 2. ELENA ROSTOVA (VP Finance) - CRITICAL SPILLOVER SCORE (90/100)
    # =========================================================================
    er_id = emp_ids["elena.rostova@cybercorp.io"]
    l_redline = leak_ids["RedLine Stealer Enterprise Botnet #7819"]
    l_pet = leak_ids["PetCare Online Superstore Leak"]
    l_tel = leak_ids["GlobalTelecom Subscriber Directory"]

    cursor.execute("""
        INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (l_redline, er_id, "elena.rostova@cybercorp.io", "ElenaFin#2024", None, "TitleCase[5] + Alpha[3] + Special + Year[4]", 1, "finance-portal.cybercorp.io"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (er_id, l_redline, "PERSONAL_EMAIL", "elena.rostova.sec@proton.me", 0.99, "Secure ProtonMail address extracted from saved sessions in RedLine drop"))
    p_er_email = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (er_id, l_tel, "PHONE_NUMBER", "+1 (312) 555-0144", 0.96, "Subscriber MSISDN and mobile billing record"))

    cursor.execute("""
        INSERT INTO physical_footprints (employee_id, source_leak_id, pivot_id, address_line, city, postal_code, country, latitude, longitude, exposure_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (er_id, l_pet, p_er_email, "1200 N Lake Shore Dr, Unit 18A", "Chicago", "60610", "United States", 41.9056, -87.6253, "RESIDENTIAL_HOME"))
    er_addr_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO relatives (employee_id, source_leak_id, shared_address_id, full_name, relationship, contact_email, contact_phone, social_engineering_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (er_id, l_pet, er_addr_id, "Michael Rostov", "Sibling", "m.rostov@outlook.com", "+1 (312) 555-0145",
          "Business Email Compromise (BEC) vector: leveraged to manufacture urgent family wire-transfer requests"))

    # =========================================================================
    # 3. MARCUS VANCE (Principal DevOps) - HIGH EXPOSURE (75/100)
    # =========================================================================
    mv_id = emp_ids["marcus.vance@cybercorp.io"]
    l_vidar = leak_ids["Vidar Stealer Malware Drop #91"]
    l_ultra = leak_ids["UltraHardware Tech Store 2023"]

    cursor.execute("""
        INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (l_vidar, mv_id, "marcus.vance@cybercorp.io", "VanceCloud!2023", None, "TitleCase[5] + Cloud + Special + Year[4]", 1, "aws-console.cybercorp.io"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mv_id, l_vidar, "PERSONAL_EMAIL", "marcus.dev@fastmail.com", 0.95, "Personal commit email extracted from global .gitconfig on compromised workstation"))
    p_mv_email = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mv_id, l_vidar, "PHONE_NUMBER", "+1 (512) 402-9912", 0.92, "Two-factor recovery telephone line in browser session"))

    cursor.execute("""
        INSERT INTO physical_footprints (employee_id, source_leak_id, pivot_id, address_line, city, postal_code, country, latitude, longitude, exposure_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (mv_id, l_ultra, p_mv_email, "450 Barton Springs Rd", "Austin", "78704", "United States", 30.2612, -97.7511, "RESIDENTIAL_HOME"))

    # =========================================================================
    # 4. SARAH JENKINS (Private Gmail Account) - MEDIUM EXPOSURE (35/100)
    # Shopping leak only, legacy hash, phone number, NO physical address
    # =========================================================================
    sj_id = emp_ids["sarah.jenkins@gmail.com"]
    cursor.execute("""
        INSERT INTO credentials (leak_id, employee_id, username_or_email, plaintext_password, password_hash, password_pattern, is_corporate_password_match, domain_compromised)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (l_shop, sj_id, "sarah.jenkins@gmail.com", None, "5d41402abc4b2a76b9719d911017c592", "MD5 Legacy Hash (hello)", 0, "shopsphere.com"))

    cursor.execute("""
        INSERT INTO pivots (employee_id, source_leak_id, pivot_type, pivot_value, confidence_score, context_note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sj_id, l_shop, "PHONE_NUMBER", "+1 (206) 555-8821", 0.88, "Customer contact phone from online shopping order profile"))

    # =========================================================================
    # 5. DAVID MILLER (Software Engineer) - CLEAN / SAFE (0/100)
    # Zero leaks, zero credentials, zero pivots
    # =========================================================================

    # =========================================================================
    # 6. OLIVIA CHEN (Security Analyst) - CLEAN / SAFE (0/100)
    # Zero leaks, zero credentials, zero pivots
    # =========================================================================

    conn.commit()
    conn.close()
    print("[+] Database seeding completed successfully with 100% English threat intelligence data!")

if __name__ == "__main__":
    seed_database()
