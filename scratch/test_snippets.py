import sys
sys.path.insert(0, '.')
from backend.web_dork_recon import query_search_snippets

print("Snippets for email:")
s1 = query_search_snippets('"3gbxdd@gmail.com"')
print("Count s1:", len(s1))
for s in s1:
    print(" ", s)

print("\nSnippets for handle:")
s2 = query_search_snippets('"3gbxdd"')
print("Count s2:", len(s2))
for s in s2:
    print(" ", s)
