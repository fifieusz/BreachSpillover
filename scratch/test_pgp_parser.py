import urllib.request, urllib.parse, re, datetime

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

PGP_ALGOS = {
    "1": "RSA", "2": "RSA-E", "3": "RSA-S",
    "16": "Elgamal", "17": "DSA", "18": "ECDH",
    "19": "ECDSA", "22": "Ed25519", "23": "X25519"
}

def parse_rfc2822_uid(raw_uid: str):
    cleaned = raw_uid.strip()
    match = re.match(r'^(?:(?P<name>[^<(]+?)\s*)?(?:\((?P<comment>[^)]+?)\)\s*)?(?:<(?P<email>[^>]+?)>)?$', cleaned)
    name, comment, email = None, None, None
    if match:
        name = (match.group("name") or "").strip() or None
        comment = (match.group("comment") or "").strip() or None
        email = (match.group("email") or "").strip().lower() or None
    
    # Handle reversed "email <Name>"
    if name and "@" in name and email and "@" not in email:
        name, email = email, name
        
    return name, comment, email

# Test parsing on Ubuntu HKP
email = "torvalds@kernel.org"
url = f"https://keyserver.ubuntu.com/pks/lookup?search={urllib.parse.quote(email)}&op=index&options=mr"
req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
with urllib.request.urlopen(req, timeout=5) as r:
    raw = r.read().decode("utf-8", errors="ignore")

keys = []
curr_key = None
for line in raw.splitlines():
    parts = line.split(":")
    if parts[0] == "pub" and len(parts) > 1:
        fp = parts[1]
        algo_code = parts[2] if len(parts) > 2 else "1"
        key_len = parts[3] if len(parts) > 3 else "2048"
        ts_str = parts[4] if len(parts) > 4 else None
        date_str = None
        if ts_str and ts_str.isdigit():
            date_str = datetime.datetime.fromtimestamp(int(ts_str), tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        
        curr_key = {
            "fingerprint": fp,
            "key_id": fp[-16:] if len(fp) >= 16 else fp,
            "algo": PGP_ALGOS.get(algo_code, f"Algo-{algo_code}"),
            "key_len": key_len,
            "created": date_str,
            "uids": [],
            "names": set(),
            "alternate_emails": set()
        }
        keys.append(curr_key)
    elif parts[0] == "uid" and curr_key and len(parts) > 1:
        raw_uid = urllib.parse.unquote(parts[1])
        n, c, e = parse_rfc2822_uid(raw_uid)
        curr_key["uids"].append({"raw": raw_uid, "name": n, "comment": c, "email": e})
        if n and len(n) > 2:
            curr_key["names"].add(n)
        if e and e != email.lower():
            curr_key["alternate_emails"].add(e)

print(f"Discovered {len(keys)} PGP keys:")
for k in keys:
    print(f"Key ID: 0x{k['key_id']} | {k['algo']}-{k['key_len']} | Created: {k['created']}")
    print(f" Names: {list(k['names'])}")
    print(f" Alternate emails: {list(k['alternate_emails'])}")
    for u in k["uids"]:
        print(f"   UID: {u['raw']}")
