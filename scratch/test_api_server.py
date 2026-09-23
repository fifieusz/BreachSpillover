import urllib.request
import json

url = "http://127.0.0.1:8000/api/search?email=jordinzwaan2016@gmail.com"
print(f"Requesting {url}...")
try:
    with urllib.request.urlopen(url, timeout=60) as resp:
        print("Status code:", resp.status)
        data = json.loads(resp.read().decode('utf-8'))
        print("\n=== RESPONSE PAYLOAD CHECK ===")
        print("Employee ID:", data.get("employee", {}).get("id"))
        print("Name:", data.get("employee", {}).get("full_name"))
        print("Job Title:", data.get("employee", {}).get("job_title"))
        print("Department:", data.get("employee", {}).get("department"))
        
        print("\nPhysical Footprints count:", len(data.get("physical_footprints", [])))
        for foot in data.get("physical_footprints", []):
            print(f"  [Footprint] City: {foot.get('city')} | Country: {foot.get('country')} | Addr: {foot.get('address_line')}")
        
        print("\nPivots count:", len(data.get("pivots", [])))
        for piv in data.get("pivots", []):
            print(f"  [{piv.get('pivot_type')}] {piv.get('pivot_value')} | Context: {piv.get('context_note')[:100]}")
except Exception as e:
    print("Error:", e)
