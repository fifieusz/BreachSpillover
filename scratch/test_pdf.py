import urllib.request
import re

url = "https://b60c98dd-0946-4d54-b101-79ba39a893ab.filesusr.com/ugd/d1fa24_7caeae29702b4c93a3e34fd3bebb9051.pdf"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as res:
        data = res.read()
        print("PDF downloaded, len:", len(data))
        # look for plaintext strings in pdf
        text = data.decode('latin-1', errors='ignore')
        matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        print("Emails in PDF:", set(matches))
        phones = re.findall(r'(?:\+31|06)[0-9\s-]{8,12}', text)
        print("Phones in PDF:", set(phones))
        for word in ["Wolvega", "Facebook", "facebook", "Instagram", "Zwolle", "Linde", "Amsterdam"]:
            if word.lower() in text.lower():
                print(f"'{word}' found in PDF!")
except Exception as e:
    print("PDF error:", e)
