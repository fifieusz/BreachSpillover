import urllib.request
import json
import urllib.parse

def test_author_email(email):
    url = f"https://api.github.com/search/commits?q=author-email:{urllib.parse.quote(email)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "BreachSpillover-OSINT/1.0",
        "Accept": "application/vnd.github.cloak-preview"
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as res:
            data = json.loads(res.read().decode())
            print(f"Total commits for {email}: {data.get('total_count', 0)}")
            discovered_authors = set()
            discovered_repos = set()
            for item in data.get('items', [])[:10]:
                author = item.get('commit', {}).get('author', {})
                repo = item.get('repository', {}).get('full_name')
                author_name = author.get('name')
                committer = item.get('author') or {}
                login = committer.get('login')
                if login:
                    discovered_authors.add(login)
                if author_name:
                    discovered_authors.add(author_name)
                if repo:
                    discovered_repos.add(repo)
            print("Discovered handles/authors:", discovered_authors)
            print("Discovered repos:", discovered_repos)
            return discovered_authors, discovered_repos
    except Exception as e:
        print("GitHub error:", e)
        return set(), set()

if __name__ == '__main__':
    test_author_email('filipos123.91@gmail.com')
