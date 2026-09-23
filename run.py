#!/usr/bin/env python3
"""
BreachSpillover - One-Step Launch Script
Author: Senior Security Software Engineer & System Architect
"""

import os
import sys
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_path
from data_generator.seed_data import seed_database

def banner():
    print(r"""
======================================================================
  ____                      _     ____        _ _ _                     
 | __ ) _ __ ___  __ _  ___| |__ / ___| _ __ (_) | | _____   _____ _ __ 
 |  _ \| '__/ _ \/ _` |/ __| '_ \\___ \| '_ \| | | |/ _ \ \ / / _ \ '__|
 | |_) | | |  __/ (_| | (__| | | |___) | |_) | | | | (_) \ V /  __/ |   
 |____/|_|  \___|\__,_|\___|_| |_|____/| .__/|_|_|_|\___/ \_/ \___|_|   
                                       |_|                              
  Universal Digital Risk Protection & Identity Exposure Intelligence
======================================================================
    """)

def main():
    banner()
    db_file = get_db_path()
    if not db_file.exists() or db_file.stat().st_size == 0:
        print("[*] Local database not found or empty. Running initial deterministic seed...")
        seed_database()
        print("[+] Seed completed successfully.\n")
    else:
        print(f"[+] Using existing local database: {db_file}")

    from backend.ai_engine import load_dotenv
    load_dotenv()
    if os.getenv("GROQ_API_KEY"):
        print("[+] AI Threat Engine: ONLINE (Groq Llama 3.3 key detected)")
    elif os.getenv("GEMINI_API_KEY"):
        print("[+] AI Threat Engine: ONLINE (Gemini Flash key detected)")
    else:
        print("[i] AI Threat Engine: Ready (Configure GROQ_API_KEY in .env or via Web UI [AI ENGINE])")

    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    print(f"[*] Starting BreachSpillover Server at: {url}")
    print("[*] Press Ctrl+C to terminate.")
    print("----------------------------------------------------------------------\n")

    uvicorn.run("backend.main:app", host=host, port=port, log_level="info", reload=False)

if __name__ == "__main__":
    main()
