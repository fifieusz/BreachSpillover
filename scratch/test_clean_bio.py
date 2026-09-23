import urllib.request
import re

html = urllib.request.urlopen('https://jordinzwaan2016.wixsite.com/portfolio').read().decode('utf-8', errors='ignore')
clean = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.IGNORECASE)
clean = re.sub(r'<style[\s\S]*?</style>', ' ', clean, flags=re.IGNORECASE)
clean = re.sub(r'<[^>]+>', ' ', clean)
clean = re.sub(r'\s+', ' ', clean).strip()
clean = clean.replace('\u200b', '').replace('&nbsp;', ' ')

bio_m = re.search(r'(?:Hoi,\s*ik\s*ben|Hi,\s*I\s*am|Hello,\s*I\s*am|Hallo,\s*ich\s*bin)\s+([^<>\n]{20,500})', clean, re.IGNORECASE)
if bio_m:
    print("MATCHED BIO:")
    print(bio_m.group(0))

edu_m = re.search(r'(?:opleiding\s+aan\s+het|studie\s+aan\s+het|studies\s+at|studied\s+at|aan\s+het)\s+([A-Z][A-Za-z0-9\s-]+?(?:College|University|Universiteit|School|Academy|Hogeschool))', clean, re.IGNORECASE)
if edu_m:
    print("MATCHED EDU:", edu_m.group(1))
