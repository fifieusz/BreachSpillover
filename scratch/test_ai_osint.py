import os
import sys
sys.path.insert(0, '.')
import json

from backend.ai_engine import call_groq_api, resolve_api_key, load_dotenv

load_dotenv()

snippets = [
    {"title": "Jordin Zwaan - Merlon Security | LinkedIn", "url": "https://nl.linkedin.com/in/jordin-zwaan-716485261", "snippet": "CyberOps Associate at Merlon Security. Based in Nederland."},
    {"title": "HOME | My Site 1", "url": "https://jordinzwaan2016.wixsite.com/portfolio", "snippet": "Personal portfolio of Jordin Zwaan. Timezone Europe/Amsterdam."},
    {"title": "Jordan van der Zwaan Profiles - Facebook", "url": "https://www.facebook.com/public/Jordan-van-der-Zwaan/", "snippet": "People named Jordan van der Zwaan. Find your friends on Facebook."}
]

prompt = f"""You are an elite OSINT Intelligence Disambiguation Engine.
Target to investigate: Jordin Zwaan (email: jordinzwaan2016@gmail.com)

Analyze the following search engine dork snippets:
{json.dumps(snippets, indent=2)}

Task:
Filter out false positives (e.g. people with different names like Jordan van der Zwaan if they do not match).
Extract verified location, workplace, and social profiles for the exact target.

Respond ONLY with valid JSON in this exact structure:
{{
  "is_corroborated": true,
  "confidence_score": 0.90,
  "location": {{
    "city": "Amsterdam",
    "country": "Netherlands",
    "context": "Identified from LinkedIn and personal portfolio"
  }},
  "workplace": {{
    "company": "Merlon Security",
    "job_title": "CyberOps Associate",
    "context": "Verified LinkedIn profile"
  }},
  "profiles": [
    {{"platform": "LinkedIn", "url": "https://nl.linkedin.com/in/jordin-zwaan-716485261", "handle": "jordin-zwaan-716485261"}}
  ]
}}"""

print("Querying Groq Llama 3.3...")
key = resolve_api_key()
res = call_groq_api(prompt, "You are a senior OSINT disambiguation engine.", key)
print("AI Response:\n", json.dumps(res, indent=2))
