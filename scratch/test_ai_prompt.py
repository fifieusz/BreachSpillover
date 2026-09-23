import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ai_engine import call_groq_api, resolve_api_key, load_dotenv
import json

load_dotenv()
api_key = resolve_api_key("groq")

# Test snippets including DDG Lite, portfolio, and the snippets containing false positives (like @jjjordin, @jordinlaine)
test_snippets = [
    {
        "title": "HOME | My Site 1",
        "url": "https://jordinzwaan2016.wixsite.com/portfolio",
        "snippet": "Hoi, ik ben Jordin Zwaan, 20jaar oud, en ik woon in Wolvega, een dorpje in Friesland. Momenteel zit ik in het vierde leerjaar van de opleiding Media Vormgever aan het Deltion College. In mijn vrije tijd houd ik me graag bezig met gamen, fitnessen, werken en quality time doorbrengen met mijn vriendin."
    },
    {
        "title": "Jordin Zwaan - Merlon Security | LinkedIn",
        "url": "https://nl.linkedin.com/in/jordin-zwaan-716485261",
        "snippet": "Cyber security enthusiast | Cisco NetAcad CyberOps Associate | Student at AUAS (Amsterdam University of Applied Sciences) - Amsterdam, North Holland, Netherlands."
    },
    {
        "title": "jordin (@jjjordin) • Instagram photos and videos",
        "url": "https://www.instagram.com/jjjordin/",
        "snippet": "3,200 Followers, 850 Following, 140 Posts - See Instagram photos and videos from jordin (@jjjordin). Fashion, lifestyle, travel blogger."
    },
    {
        "title": "JordinLaine (@jordinlaine) • Instagram photos and videos",
        "url": "https://www.instagram.com/jordinlaine/",
        "snippet": "Jordin Laine singer songwriter and actress based in Nashville, TN."
    },
    {
        "title": "Jordan van der Zwaan Profiles - Facebook",
        "url": "https://www.facebook.com/public/Jordan-van-der-Zwaan/",
        "snippet": "View the profiles of people named Jordan van der Zwaan. Join Facebook to connect with Jordan van der Zwaan."
    },
    {
        "title": "Jordin Zwaan - Facebook",
        "url": "https://www.facebook.com/Jordin-Zwaan-100009907727146",
        "snippet": "Jordin Zwaan ; Lives in Wolvega ; Studies at Amsterdam University of Applied Sciences - AUAS ; Studied at MBO Deltion College Zwolle."
    }
]

system_instruction = (
    "You are an elite OSINT Intelligence Disambiguation Engine. "
    "Your duty is to strictly filter out false positives and extract verified "
    "person attributes from search engine snippets. Output strictly valid JSON."
)

prompt = f"""Target Entity Under Investigation:
- Target Full Name: Jordin Zwaan
- Target Email Address: jordinzwaan2016@gmail.com
- Target Known Handles / Nicknames: jordinzwaan, sazeku

Raw Live Search Snippets Retrieved for Target:
{json.dumps(test_snippets, indent=2)}

Verification Guidelines:
1. Strict Entity Disambiguation (Prune False Positives):
   - Only corroborate snippets that genuinely belong to the target entity.
   - REJECT stranger profiles: for instance, if the target is a male Dutch individual named Jordin Zwaan, REJECT female lifestyle / model accounts (e.g. @jjjordin, @jordinlaine) or unrelated users who happen to share a common first name.
   - REJECT individuals with different surnames or distinct personas (e.g. Jordan van der Zwaan, Joris Zwaan).
   - Only accept social accounts (Instagram, Facebook, LinkedIn, GitHub, Portfolio) where the handle, full name, or biography clearly corroborates the target's identity.
2. Verified Attributes Extraction:
   - Physical Location: Extract confirmed city, province/state, and country (e.g. Dutch 'ik woon in <City>', English 'Lives in <City>').
   - Workplace / Education: Extract confirmed educational institutions (e.g. Deltion College, AUAS) and companies/roles.
   - Social Presence: Return strictly verified profile URLs.

Respond ONLY with valid JSON in this exact structure:
{{
  "is_corroborated": true,
  "confidence_score": 0.95,
  "location": {{
    "city": "Exact city name",
    "country": "Country name",
    "context": "Evidence citation"
  }},
  "workplace": {{
    "company": "Company or Educational Institution name",
    "job_title": "Role title or student",
    "context": "Evidence citation"
  }},
  "profiles": [
    {{
      "platform": "LinkedIn / Facebook / Portfolio / Instagram / GitHub",
      "url": "https://...",
      "handle": "username or profile ID",
      "context": "Context note"
    }}
  ]
}}"""

res = call_groq_api(prompt, system_instruction, api_key, temperature=0.1, response_json=True)
print("Groq response success:", res.get("success"))
print(res.get("text"))
