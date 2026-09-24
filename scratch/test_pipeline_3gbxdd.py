import sys
sys.path.insert(0, ".")
from backend.live_osint import execute_deep_live_osint

def run_test():
    print("=" * 65)
    print("RUNNING LIVE OSINT SCAN ON: 3gbxdd@gmail.com")
    print("=" * 65)

    res = execute_deep_live_osint("3gbxdd@gmail.com")
    profiles = res.get("discovered_profiles", [])
    names = res.get("discovered_names", [])
    handles = res.get("discovered_handles", [])
    
    print(f"\nDiscovered Names ({len(names)}): {names}")
    print(f"Discovered Handles ({len(handles)}): {handles}")
    print(f"\nDiscovered Profiles ({len(profiles)}):")
    for p in profiles:
        plat = p.get("platform")
        url = p.get("url")
        src = p.get("source")
        badge = p.get("tie_badge") or p.get("tie_type")
        ctx = (p.get("context") or "")[:85]
        print(f"  [{plat}] {url}")
        print(f"      Source: {src} | Badge: {badge}")
        print(f"      Context: {ctx}")

if __name__ == "__main__":
    run_test()
